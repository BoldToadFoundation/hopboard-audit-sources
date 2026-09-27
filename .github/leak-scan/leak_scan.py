#!/usr/bin/env python3
"""leak_scan.py — this repository's CI leak check (hopboard D-056). Stdlib and gitleaks only.

WHAT IT SCANS. Project-written content only: the manifests (their provenance text and URLs),
the top-level files, anything outside a capture pin, commit objects (message, author,
committer), and, for a pushed range, the lines each commit adds. CAPTURED BYTES ARE NEVER
SCANNED: a file whose sha256 is pinned by a manifest's `content_sha256`, or listed in
`unmanifested_captures.sha256` (the older captures no manifest holds), is third-party content,
and the IPs, `/home/...` URLs, timestamps and tokens third-party pages carry would fire every
run. A capture edited after pinning stops matching its hash and is scanned like anything else.

TWO CHECKS.
  * credentials: gitleaks' default rules, on that project-written material.
  * LEAK_PATTERN: an extended regex from the repository secret of that name. It holds
    infrastructure markers only. IDENTITY TERMS NEVER REACH GITHUB, SECRETS INCLUDED (Tony's
    floor, hopboard D-055 amendment 1): identity is the local pre-push gate's job
    (hopboard D-055), which decodes captures too.

THE LOG IS PUBLIC. It prints counts, rule names and commit ids. Never matched text, and never a
path; `--details` prints paths and line numbers, still no text, and refuses to run in Actions.

EXIT: 0 clean · 1 findings · 2 cannot run, or the LEAK_PATTERN half did not run (fail closed).
A fork pull request gets no secrets, so there it says THIS CHECK DID NOT RUN and exits on
gitleaks alone.

WHAT ITS SELF-TEST WOULD STILL PASS IF THE SCAN WERE BROKEN: the tests plant synthetic values;
they prove the plumbing, not that the real LEAK_PATTERN is complete. A leak in a form the pattern
does not hold passes, and so does a leak inside a pinned capture, by design.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

INDEX = ".github/leak-scan/unmanifested_captures.sha256"
ZERO = "0" * 40
TAG = "leak-scan:"
GREP_ENV = {**os.environ, "LC_ALL": "C"}


class CannotRun(Exception):
    pass


def git(repo, *args, text=True):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, stdin=subprocess.DEVNULL)
    if r.returncode:
        raise CannotRun(f"git {args[0]} failed (exit {r.returncode})")
    return r.stdout.decode("utf-8", "surrogateescape") if text else r.stdout


def read_blobs(repo, shas):
    out, p = {}, subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for s in dict.fromkeys(shas):
        p.stdin.write(s.encode() + b"\n")
        p.stdin.flush()
        hdr = p.stdout.readline().split()
        if len(hdr) < 3 or hdr[1] != b"blob":
            raise CannotRun("git cat-file returned something other than a blob")
        out[s] = p.stdout.read(int(hdr[2]))
        p.stdout.read(1)
    p.stdin.close()
    p.wait()
    return out


def tree(repo, rev):
    """[(path, blob)] for every file at rev; gitlinks skipped."""
    items = []
    for ent in git(repo, "ls-tree", "-r", "-z", rev).split("\0"):
        if ent:
            meta, path = ent.split("\t", 1)
            mode, typ, sha = meta.split()
            if typ == "blob":
                items.append((path, sha))
    return items


def pins(repo, rev):
    """(manifest-pinned sha256s, indexed sha256s) at rev. Anything unreadable refuses."""
    files = tree(repo, rev)
    manifests = [(p, s) for p, s in files if p == "manifest.json" or p.endswith("/manifest.json")]
    data = read_blobs(repo, [s for _p, s in manifests])
    pinned = set()
    for n, (_p, s) in enumerate(manifests, 1):
        try:
            entries = json.loads(data[s])
            for e in entries:
                h = e["content_sha256"]
                if not re.fullmatch(r"[0-9a-f]{64}", h):
                    raise ValueError
                pinned.add(h)
        except (ValueError, KeyError, TypeError):
            raise CannotRun(f"a manifest does not parse, or an entry lacks a sha256 "
                            f"(manifest {n} of {len(manifests)}); run --details locally")
    indexed = set()
    idx = [s for p, s in files if p == INDEX]
    if idx:
        for n, line in enumerate(read_blobs(repo, idx)[idx[0]].decode("utf-8", "replace").splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            m = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            if not m:
                raise CannotRun(f"the capture index {INDEX} has a malformed line ({n})")
            indexed.add(m.group(1))
    return pinned, indexed


def added_lines(new: bytes, old: bytes) -> bytes:
    """Lines of `new` beyond their count in `old`. A binary file is taken whole."""
    if b"\0" in new[:8192] or old is None:
        return new
    seen = Counter(old.splitlines())
    out = []
    for line in new.splitlines():
        if seen[line] > 0:
            seen[line] -= 1
        else:
            out.append(line)
    return b"\n".join(out)


def range_units(repo, commits, pinned_all):
    """Commit objects plus each commit's added lines in files outside the pins."""
    units = []
    for c in commits:
        short = c[:9]
        units.append((f"commit object {short}", f"commit {c}", git(repo, "cat-file", "commit", c, text=False)))
        parents = git(repo, "rev-list", "--parents", "-n1", c).split()[1:]
        toks = git(repo, "diff-tree", "-r", "-z", "-M", "--root", "--no-commit-id",
                   *(parents[:1] or []), c).split("\0")
        i, changes = 0, []
        while i < len(toks) - 1:
            meta = toks[i].split()
            if len(meta) < 5:
                i += 1
                continue
            step = 3 if meta[4][:1] in ("R", "C") else 2
            path = toks[i + step - 1]
            if meta[3] != ZERO and meta[1] != "160000":
                changes.append((path, meta[2], meta[3]))
            i += step
        blobs = read_blobs(repo, [b for _p, o, n in changes for b in (o, n) if b != ZERO])
        for path, old, new in changes:
            data = blobs[new]
            if hashlib.sha256(data).hexdigest() in pinned_all:
                continue
            units.append((f"added lines, commit {short}", f"{path} (added in {short})",
                          added_lines(data, blobs.get(old) if old != ZERO else None)))
    return units


def grep_matches(pattern, files):
    """{file: [line numbers]}, one entry per match. Matched text is read and dropped.
    No files means no scan: grep with no file argument would read stdin, and where stdin
    never closes it hangs (found by a mutant, 2026-09-27)."""
    if not files:
        return {}
    r = subprocess.run(["grep", "-a", "-o", "-n", "-H", "-i", "-E", "-e", pattern, *files],
                       capture_output=True, stdin=subprocess.DEVNULL, env=GREP_ENV)
    if r.returncode == 2:
        raise CannotRun("grep failed on LEAK_PATTERN")
    hits = {}
    for line in r.stdout.splitlines():
        f, ln, _rest = line.split(b":", 2)
        hits.setdefault(f.decode(), []).append(int(ln))
    return hits


def check_pattern(pattern):
    r = subprocess.run(["grep", "-E", "-e", pattern], input=b"\n", capture_output=True, env=GREP_ENV)
    if r.returncode == 2:
        raise CannotRun("LEAK_PATTERN is not a valid extended regular expression")
    if r.returncode == 0:
        raise CannotRun("LEAK_PATTERN matches the empty string, so it would flag everything")


def plan(repo, args):
    """(event label, range commits, commit objects to read beyond the range, head)."""
    if args.mode == "tree":
        return "tree", [], [], args.head or "HEAD"
    if args.mode == "range":
        a, b = args.range.split("..", 1)
        return "range", git(repo, "rev-list", "--reverse", f"{a}..{b}").split(), [], b
    event = os.environ.get("GITHUB_EVENT_NAME", "manual")
    head = os.environ.get("LEAK_SCAN_HEAD") or "HEAD"
    if event == "push":
        before = os.environ.get("LEAK_SCAN_BEFORE", ZERO)
        ok = before != ZERO and subprocess.run(["git", "-C", repo, "cat-file", "-e", f"{before}^{{commit}}"],
                                                capture_output=True).returncode == 0
        if ok:
            revs = [f"{before}..{head}"]
        elif subprocess.run(["git", "-C", repo, "rev-parse", "-q", "--verify", "refs/remotes/origin/main"],
                            capture_output=True).returncode == 0:
            revs = [head, "--not", "refs/remotes/origin/main"]
        else:
            revs = [head]
        return "push", git(repo, "rev-list", "--reverse", *revs).split(), [], head
    if event == "pull_request":
        base = os.environ.get("LEAK_SCAN_BASE", "")
        return "pull_request", git(repo, "rev-list", "--reverse", f"{base}..{head}").split(), [], head
    # schedule, workflow_dispatch, anything else: the tree and every commit object
    return event, [], git(repo, "rev-list", head).split(), head


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--mode", choices=["auto", "tree", "range"], default="auto")
    ap.add_argument("--range")
    ap.add_argument("--head")
    ap.add_argument("--pattern-file")
    ap.add_argument("--details", action="store_true",
                    help="paths and line numbers of findings (never text); local runs only")
    args = ap.parse_args(argv)
    repo = args.repo
    try:
        if args.details and os.environ.get("GITHUB_ACTIONS") == "true":
            raise CannotRun("--details prints paths, and this log is public; run it locally")
        gitleaks = shutil.which("gitleaks")
        if not gitleaks:
            raise CannotRun("gitleaks is not installed")
        if args.pattern_file:
            with open(args.pattern_file, encoding="utf-8") as fh:
                pattern = fh.read()
        else:
            pattern = os.environ.get("LEAK_PATTERN", "")
        # A pasted secret can carry a trailing newline, and grep -e would read what follows it
        # as a second, empty pattern that matches everything.
        pattern = pattern.strip("\r\n")
        fork = (os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
                and os.environ.get("LEAK_SCAN_FORK") == "true")
        if pattern:
            check_pattern(pattern)

        event, rng, extra_msgs, head = plan(repo, args)
        head_sha = git(repo, "rev-parse", f"{head}^{{commit}}").strip()
        pinned, indexed = pins(repo, head_sha)
        files = tree(repo, head_sha)
        blobs = read_blobs(repo, [s for _p, s in files])
        n_pin = n_idx = 0
        units = []
        for path, s in files:
            if event == "range":
                break                     # an explicit --range reads the range only
            h = hashlib.sha256(blobs[s]).hexdigest()
            if h in pinned:
                n_pin += 1
            elif h in indexed:
                n_idx += 1
            else:
                units.append(("tree", path, blobs[s]))
        n_tree = len(units)
        # A capture's pin is read at every commit in the range as well as the tip: a capture
        # added and then replaced inside one push was pinned by its own commit's manifest.
        range_pins = set(pinned | indexed)
        for c in rng:
            p_c, i_c = pins(repo, c)
            range_pins |= p_c | i_c
        units += range_units(repo, rng, range_pins)
        units += [(f"commit object {c[:9]}", f"commit {c}", git(repo, "cat-file", "commit", c, text=False))
                  for c in extra_msgs if c not in rng]

        with tempfile.TemporaryDirectory(prefix="leakscan-") as tmp:
            names = {}
            for k, (scope, where, data) in enumerate(units):
                f = os.path.join(tmp, f"u{k:06d}.txt")
                with open(f, "wb") as fh:
                    fh.write(data)
                names[f] = (scope, where)
            report = os.path.join(tmp, "..", f"gitleaks-{os.getpid()}.json")
            ver = subprocess.run([gitleaks, "version"], capture_output=True, text=True,
                                 stdin=subprocess.DEVNULL).stdout.strip()
            r = subprocess.run([gitleaks, "dir", tmp, "--no-banner", "--log-level", "error", "--redact",
                                "-f", "json", "-r", report, "--exit-code", "0"], capture_output=True,
                               stdin=subprocess.DEVNULL)
            if r.returncode:
                raise CannotRun(f"gitleaks failed (exit {r.returncode})")
            with open(report) as fh:
                findings = json.load(fh) or []
            os.unlink(report)
            cred = Counter((f["RuleID"], names[f["File"]][0]) for f in findings)
            cred_where = [(names[f["File"]][1], f.get("StartLine")) for f in findings]
            pat, pat_where = Counter(), []
            if pattern:
                for f, lines in grep_matches(pattern, list(names)).items():
                    pat[names[f][0]] += len(lines)
                    pat_where += [(names[f][1], ln) for ln in lines]

        print(f"{TAG} event {event}: {len(rng)} commit(s) in range, {len(extra_msgs)} more commit object(s) "
              f"read; tree at {head_sha[:9]}: {n_tree} project-written file(s) scanned, {n_pin + n_idx} "
              f"captured file(s) skipped ({n_pin} manifest-pinned, {n_idx} indexed).")
        print(f"{TAG} credentials (gitleaks {ver or '?'}, default rules): {sum(cred.values())} finding(s)"
              + "".join(f"; {rule} x{n} in {scope}" for (rule, scope), n in sorted(cred.items())))
        if pattern:
            print(f"{TAG} LEAK_PATTERN: {sum(pat.values())} match(es)"
                  + "".join(f"; {scope} x{n}" for scope, n in sorted(pat.items())))
        elif fork:
            print(f"{TAG} LEAK_PATTERN: THIS CHECK DID NOT RUN (a fork pull request: GitHub withholds "
                  f"secrets). Merge locally, through the pre-push gate.")
        else:
            print(f"{TAG} LEAK_PATTERN: THIS CHECK DID NOT RUN: the LEAK_PATTERN secret is not set.")
        if args.details:
            for where, ln in sorted(set(cred_where) | set(pat_where), key=str):
                print(f"{TAG}   {where}:{ln}" if where and not where.startswith("commit ") else f"{TAG}   {where} line {ln}")
        found = bool(cred or pat)
        if found:
            print(f"{TAG} FINDINGS. This log names rules and places, never text. Locally: python3 "
                  f".github/leak-scan/leak_scan.py --mode tree --details --pattern-file <file>")
        if not pattern and not fork:
            return 2
        if not found:
            print(f"{TAG} CLEAN.")
        return 1 if found else 0
    except CannotRun as e:
        print(f"{TAG} CANNOT RUN: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
