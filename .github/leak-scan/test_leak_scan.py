"""Tests for leak_scan.py, the CI leak check (hopboard D-056). Stdlib only: CI runs them with
`python3 -m unittest` before every scan, so the scan proves it still catches planted values
before its own verdict is trusted.

Everything planted here is synthetic, and the one credential shape is assembled at run time,
so this file itself scans clean. No identity term appears anywhere in CI (D-055 amendment 1):
identity is the local pre-push gate's job.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("leak_scan.py")
WORKFLOW = Path(__file__).resolve().parents[1] / "workflows" / "leak-scan.yml"
MARK = "zqmarker-7"                      # what the synthetic LEAK_PATTERN finds
PATTERN = "zqmarker-[0-9]"
CRED = "AKIA" + "Z7QXKW3M4N5P6R2T"      # an AWS-key shape, assembled so this file holds none
PLANTS = (MARK, CRED)
ZERO = "0" * 40


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Repo:
    """A throwaway repo shaped like hopboard-audit-sources: a manifest-pinned capture, an
    indexed capture outside any manifest, and project-written files. Both captures carry
    the marker and a credential, as third-party pages do."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="leakscan-test-"))
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        for k in ("GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "LEAK_PATTERN", "LEAK_SCAN_BEFORE",
                  "LEAK_SCAN_BASE", "LEAK_SCAN_HEAD", "LEAK_SCAN_FORK"):
            self.env.pop(k, None)
        self.git("init", "-q", "-b", "main")
        cap = f"<p>third party {MARK} {CRED}</p>\n".encode()
        legacy = f"<p>older capture {MARK}</p>\n".encode()
        self.write("AA/cap.html", cap)
        self.write("AA/manifest.json", json.dumps([{"local_path": "AA/cap.html",
                                                   "content_sha256": sha(cap)}]))
        self.write("BB/legacy.html", legacy)
        self.write(".github/leak-scan/unmanifested_captures.sha256", f"{sha(legacy)}  BB/legacy.html\n")
        self.write("README.md", "project notes\n")
        self.commit("baseline")
        self.base = self.head()

    def git(self, *a, check=True):
        r = subprocess.run(["git", *a], cwd=self.dir, env=self.env, capture_output=True, text=True)
        if check and r.returncode:
            raise AssertionError(r.stderr)
        return r.stdout.strip()

    def write(self, name, data):
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())

    def commit(self, msg="change"):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", msg)

    def head(self):
        return self.git("rev-parse", "HEAD")

    def scan(self, *args, pattern=PATTERN, **env):
        e = {**self.env, **{k: v for k, v in env.items() if v is not None}}
        if pattern is not None:
            e["LEAK_PATTERN"] = pattern
        r = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.dir), *args],
                           env=e, capture_output=True, text=True)
        out = r.stdout + r.stderr
        for v in PLANTS:
            assert v not in out, f"the scan printed a planted value: {v}"
        return r.returncode, out

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class LeakScanTests(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.close()

    # ── what is skipped and what is scanned ─────────────────────────────────
    def test_pinned_and_indexed_captures_are_skipped(self):
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 0, out)
        self.assertIn("2 captured file(s) skipped (1 manifest-pinned, 1 indexed)", out)
        self.assertIn("LEAK_PATTERN: 0 match(es)", out)
        self.assertIn("credentials", out)

    def test_a_marker_in_a_project_written_file_fails_and_is_not_printed(self):
        self.r.write("README.md", f"notes {MARK}\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 1, out)
        self.assertIn("LEAK_PATTERN: 1 match(es)", out)

    def test_a_capture_changed_after_pinning_is_scanned(self):
        self.r.write("AA/cap.html", f"<p>edited {MARK}</p>\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 1, out)

    def test_an_indexed_capture_changed_after_indexing_is_scanned(self):
        self.r.write("BB/legacy.html", f"<p>edited {MARK}</p>\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 1, out)

    def test_a_new_file_outside_any_pin_is_scanned(self):
        self.r.write("CC/new.html", f"<p>{MARK}</p>\n")
        self.r.commit()
        rc, _ = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 1)

    # ── the pushed range ────────────────────────────────────────────────────
    def test_a_marker_only_in_a_commit_message_fails(self):
        self.r.commit(msg=f"note {MARK}")
        rc, out = self.r.scan("--mode", "range", "--range", f"{self.r.base}..{self.r.head()}")
        self.assertEqual(rc, 1, out)
        self.assertIn("commit object", out)

    def test_a_marker_in_an_author_field_fails(self):
        self.r.env["GIT_AUTHOR_NAME"] = f"someone {MARK}"
        self.r.commit()
        rc, _ = self.r.scan("--mode", "range", "--range", f"{self.r.base}..{self.r.head()}")
        self.assertEqual(rc, 1)

    def test_range_mode_reads_added_lines_only(self):
        self.r.write("README.md", f"old {MARK}\n")
        self.r.commit()
        mid = self.r.head()
        self.r.write("README.md", f"old {MARK}\nnew clean line\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "range", "--range", f"{mid}..{self.r.head()}")
        self.assertEqual(rc, 0, out)
        rc, _ = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 1)

    def test_a_capture_replaced_inside_the_range_is_skipped_in_both_versions(self):
        """Each version was pinned by its own commit's manifest. Pins read only at the tip
        would scan the first version as project-written (found in admission, 2026-09-27:
        an older CA capture set off a gitleaks rule)."""
        v1 = f"<p>first capture {MARK} {CRED}</p>\n".encode()
        self.r.write("DD/page.html", v1)
        self.r.write("DD/manifest.json", json.dumps([{"local_path": "DD/page.html", "content_sha256": sha(v1)}]))
        self.r.commit()
        v2 = f"<p>recaptured {MARK}</p>\n".encode()
        self.r.write("DD/page.html", v2)
        self.r.write("DD/manifest.json", json.dumps([{"local_path": "DD/page.html", "content_sha256": sha(v2)}]))
        self.r.commit()
        rc, out = self.r.scan("--mode", "range", "--range", f"{self.r.base}..{self.r.head()}")
        self.assertEqual(rc, 0, out)

    def test_a_marker_added_then_removed_inside_the_range_fails(self):
        self.r.write("README.md", f"{MARK}\n")
        self.r.commit()
        self.r.write("README.md", "clean\n")
        self.r.commit()
        rc, _ = self.r.scan("--mode", "range", "--range", f"{self.r.base}..{self.r.head()}")
        self.assertEqual(rc, 1)

    def test_a_push_event_scans_the_range_and_the_tree(self):
        self.r.commit(msg=f"m {MARK}")
        rc, out = self.r.scan(GITHUB_EVENT_NAME="push", LEAK_SCAN_BEFORE=self.r.base,
                              LEAK_SCAN_HEAD=self.r.head())
        self.assertEqual(rc, 1, out)
        self.assertIn("1 commit(s) in range", out)

    def test_a_new_branch_push_scans_what_the_default_branch_lacks(self):
        self.r.git("update-ref", "refs/remotes/origin/main", self.r.base)
        self.r.git("checkout", "-q", "-b", "topic")
        self.r.commit(msg=f"m {MARK}")
        rc, out = self.r.scan(GITHUB_EVENT_NAME="push", LEAK_SCAN_BEFORE=ZERO, LEAK_SCAN_HEAD=self.r.head())
        self.assertEqual(rc, 1, out)
        self.assertIn("1 commit(s) in range", out)

    def test_a_schedule_run_reads_the_tree_and_every_commit_object(self):
        self.r.commit(msg=f"m {MARK}")
        self.r.commit(msg="later, clean")
        rc, out = self.r.scan(GITHUB_EVENT_NAME="schedule", LEAK_SCAN_HEAD=self.r.head())
        self.assertEqual(rc, 1, out)
        self.assertIn("commit object", out)

    def test_an_empty_range_finishes_even_with_stdin_held_open(self):
        """Found by a mutant, 2026-09-27: with nothing to scan, grep got no file arguments and
        read stdin instead, which hangs wherever stdin never closes. An empty push range
        (a push that adds no commits) reaches exactly that state."""
        e = {**self.r.env, "LEAK_PATTERN": PATTERN}
        p = subprocess.Popen([sys.executable, str(SCRIPT), "--repo", str(self.r.dir), "--mode", "range",
                              "--range", f"{self.r.base}..{self.r.base}"],
                             env=e, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            rc = p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            self.fail("the scan hung reading stdin")
        finally:
            p.stdin.close()
        self.assertEqual(rc, 0)

    # ── credentials (gitleaks) ──────────────────────────────────────────────
    def test_a_credential_in_a_project_written_file_fails_by_rule_name(self):
        self.r.write("notes.md", f"key {CRED}\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 1, out)
        self.assertIn("aws-access-token", out)

    def test_a_credential_inside_a_capture_is_not_scanned(self):
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 0, out)
        self.assertIn("credentials (gitleaks", out)
        self.assertIn("0 finding(s)", out)

    # ── fail closed ─────────────────────────────────────────────────────────
    def test_a_missing_pattern_fails_and_says_the_check_did_not_run(self):
        rc, out = self.r.scan(pattern="", GITHUB_EVENT_NAME="push", LEAK_SCAN_BEFORE=self.r.base,
                              LEAK_SCAN_HEAD=self.r.head())
        self.assertEqual(rc, 2, out)
        self.assertIn("THIS CHECK DID NOT RUN", out)
        self.assertIn("credentials (gitleaks", out)

    def test_a_fork_pull_request_without_the_secret_says_so_and_still_runs_gitleaks(self):
        rc, out = self.r.scan(pattern="", GITHUB_EVENT_NAME="pull_request", LEAK_SCAN_BASE=self.r.base,
                              LEAK_SCAN_HEAD=self.r.head(), LEAK_SCAN_FORK="true")
        self.assertEqual(rc, 0, out)
        self.assertIn("THIS CHECK DID NOT RUN", out)
        self.assertIn("credentials (gitleaks", out)

    def test_a_secret_pasted_with_a_trailing_newline_still_works(self):
        """Pasting into GitHub's secret box can keep a trailing newline; grep -e would read the
        text after it as a second, EMPTY pattern that matches everything."""
        self.r.write("README.md", f"notes {MARK}\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree", pattern=PATTERN + "\r\n")
        self.assertEqual(rc, 1, out)
        self.assertIn("LEAK_PATTERN: 1 match(es)", out)

    def test_an_invalid_pattern_fails(self):
        rc, out = self.r.scan("--mode", "tree", pattern="zq(")
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: LEAK_PATTERN is not a valid", out)

    def test_a_pattern_that_matches_everything_fails(self):
        rc, out = self.r.scan("--mode", "tree", pattern="q*")
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: LEAK_PATTERN matches the empty string", out)

    def test_a_broken_manifest_fails(self):
        self.r.write("AA/manifest.json", "{not json")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: a manifest", out)

    def test_a_broken_index_line_fails(self):
        self.r.write(".github/leak-scan/unmanifested_captures.sha256", "not-a-hash  BB/legacy.html\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree")
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: the capture index", out)

    def test_missing_gitleaks_fails(self):
        path = ":".join(p for p in os.environ["PATH"].split(":")
                        if not (Path(p) / "gitleaks").exists())
        rc, out = self.r.scan("--mode", "tree", PATH=path)
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: gitleaks", out)

    # ── output discipline (the Actions log is public) ───────────────────────
    def test_details_are_refused_inside_actions(self):
        rc, out = self.r.scan("--mode", "tree", "--details", GITHUB_ACTIONS="true")
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: --details", out)

    def test_details_locally_give_path_and_line_but_never_text(self):
        self.r.write("README.md", f"a\nb {MARK}\n")
        self.r.commit()
        rc, out = self.r.scan("--mode", "tree", "--details")
        self.assertEqual(rc, 1)
        self.assertIn("README.md:2", out)


class WorkflowTests(unittest.TestCase):
    """The workflow text, checked without a YAML library (stdlib only in CI)."""

    def setUp(self):
        self.text = WORKFLOW.read_text()
        self.code = "\n".join(l for l in self.text.splitlines() if not l.lstrip().startswith("#"))

    def test_triggers_and_permissions(self):
        for t in ("push:", "pull_request:", "schedule:", "workflow_dispatch:"):
            self.assertIn(t, self.code)
        self.assertRegex(self.code, r"permissions:\s*\n\s+contents: read")
        self.assertNotIn("pull_request_target", self.code)

    def test_actions_are_pinned_by_commit_and_credentials_not_persisted(self):
        uses = re.findall(r"uses:\s*(\S+)", self.code)
        self.assertTrue(uses)
        for u in uses:
            self.assertRegex(u, r"@[0-9a-f]{40}$")
        self.assertIn("persist-credentials: false", self.code)

    def test_gitleaks_comes_from_a_pinned_checksummed_release(self):
        self.assertRegex(self.code, r"GITLEAKS_VERSION:\s*\S+")
        self.assertRegex(self.code, r"GITLEAKS_SHA256:\s*[0-9a-f]{64}")
        self.assertIn("sha256sum -c", self.code)

    def test_the_self_test_runs_before_the_scan(self):
        self.assertLess(self.code.index("unittest"), self.code.index("leak_scan.py"))

    def test_expressions_reach_scripts_only_through_env(self):
        for block in re.findall(r"run: \|\n((?:\s{10,}.*\n)+)", self.code):
            self.assertNotIn("${{", block)
        self.assertIn("LEAK_PATTERN: ${{ secrets.LEAK_PATTERN }}", self.code)


if __name__ == "__main__":
    unittest.main()


class PrePushRepo(Repo):
    """Repo plus a local bare remote holding the baseline, and a stand-in for hopboard's
    identity gate that records the stdin and arguments it was given and exits as told."""

    def __init__(self):
        super().__init__()
        self.remote = Path(str(self.dir) + "-remote.git")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], env=self.env,
                       check=True, capture_output=True)
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "origin", "main")
        self.gate = Path(str(self.dir) + "-gate.sh")
        self.set_gate(0)

    def set_gate(self, rc):
        self.gate.write_text(f'#!/usr/bin/env bash\ncat > "{self.gate}.stdin"\necho "$@" > "{self.gate}.args"\n'
                             f'echo "[stand-in identity gate] exit {rc}" >&2\nexit {rc}\n')
        self.gate.chmod(0o755)

    def lines(self):
        return [f"refs/heads/main {self.head()} refs/heads/main {self.git('rev-parse', 'refs/remotes/origin/main')}"]

    def pre_push(self, lines=None, gate=True, **env):
        args = [sys.executable, str(SCRIPT), "--repo", str(self.dir), "--pre-push"]
        if gate:
            args += ["--identity-gate", str(self.gate)]
        e = {**self.env, **env}
        r = subprocess.run(args + ["origin", str(self.remote)], input="\n".join(lines or self.lines()) + "\n",
                           env=e, capture_output=True, text=True)
        out = r.stdout + r.stderr
        for v in PLANTS:
            assert v not in out, f"the scan printed a planted value: {v}"
        return r.returncode, out

    def install_hook(self):
        """The same shape as the clone's real wrapper: exec the shared script with the gate."""
        h = self.dir / ".git" / "hooks" / "pre-push"
        h.write_text(f'#!/usr/bin/env bash\nexec "{sys.executable}" "{SCRIPT}" --pre-push '
                     f'--identity-gate "{self.gate}" "$@"\n')
        h.chmod(0o755)

    def close(self):
        super().close()
        shutil.rmtree(self.remote, ignore_errors=True)
        for p in (self.gate, Path(f"{self.gate}.stdin"), Path(f"{self.gate}.args")):
            p.unlink(missing_ok=True)


class PrePushTests(unittest.TestCase):
    """The clone's pre-push hook: hopboard's identity gate, then a credential scan of the outgoing
    commits' project-written content, sharing this script's capture-skip logic with CI (D-057)."""

    def setUp(self):
        self.r = PrePushRepo()

    def tearDown(self):
        self.r.close()

    def test_a_credential_in_a_project_written_file_is_refused(self):
        self.r.write("notes.md", f"key {CRED}\n")
        self.r.commit()
        rc, out = self.r.pre_push()
        self.assertEqual(rc, 1, out)
        self.assertIn("aws-access-token", out)
        self.assertIn("PUSH REFUSED", out)

    def test_a_credential_inside_a_capture_pinned_in_the_same_push_goes_through(self):
        page = f"<p>third party {CRED}</p>\n".encode()
        self.r.write("DD/page.html", page)
        self.r.write("DD/manifest.json", json.dumps([{"local_path": "DD/page.html", "content_sha256": sha(page)}]))
        self.r.commit()
        rc, out = self.r.pre_push()
        self.assertEqual(rc, 0, out)
        self.assertIn("credentials (gitleaks", out)
        self.assertIn("0 finding(s)", out)

    def test_a_credential_only_in_the_commit_message_is_refused(self):
        self.r.commit(msg=f"rotated {CRED}")
        rc, out = self.r.pre_push()
        self.assertEqual(rc, 1, out)
        self.assertIn("commit object", out)

    def test_only_outgoing_commits_are_read(self):
        self.r.write("README.md", f"already public {CRED}\n")
        self.r.commit()
        self.r.git("push", "-q", "origin", "main")          # on the remote before this push
        self.r.write("other.md", "clean\n")
        self.r.commit()
        rc, out = self.r.pre_push()
        self.assertEqual(rc, 0, out)
        self.assertIn("1 outgoing commit(s)", out)

    def test_the_identity_gate_runs_first_with_the_same_input(self):
        self.r.commit()
        lines = self.r.lines()
        rc, out = self.r.pre_push(lines)
        self.assertEqual(rc, 0, out)
        self.assertEqual(Path(f"{self.r.gate}.stdin").read_text().split("\n")[0], lines[0])
        self.assertEqual(Path(f"{self.r.gate}.args").read_text().split(), ["origin", str(self.r.remote)])

    def test_a_credential_in_an_annotated_tag_is_refused(self):
        self.r.git("tag", "-a", "v1", "-m", f"release {CRED}")
        tag = self.r.git("rev-parse", "v1")
        rc, out = self.r.pre_push([f"refs/tags/v1 {tag} refs/tags/v1 {ZERO}"])
        self.assertEqual(rc, 1, out)
        self.assertIn("tag object", out)

    def test_an_identity_refusal_refuses_the_push(self):
        self.r.set_gate(1)
        self.r.commit()
        rc, out = self.r.pre_push()
        self.assertEqual(rc, 1, out)
        self.assertIn("the identity gate refused", out)

    def test_a_missing_identity_gate_refuses(self):
        self.r.gate.unlink()
        self.r.commit()
        rc, out = self.r.pre_push()
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: the identity gate", out)

    def test_no_leak_pattern_is_needed_before_a_push(self):
        self.r.commit()
        rc, out = self.r.pre_push(LEAK_PATTERN="")
        self.assertEqual(rc, 0, out)
        self.assertIn("leak-scan: pre-push", out)

    def test_a_deletion_scans_nothing(self):
        rc, out = self.r.pre_push([f"(delete) {ZERO} refs/heads/old {self.r.head()}"])
        self.assertEqual(rc, 0, out)
        self.assertIn("0 outgoing commit(s)", out)

    def test_missing_gitleaks_refuses_before_a_push(self):
        path = ":".join(p for p in os.environ["PATH"].split(":") if not (Path(p) / "gitleaks").exists())
        self.r.commit()
        rc, out = self.r.pre_push(PATH=path)
        self.assertEqual(rc, 2, out)
        self.assertIn("CANNOT RUN: gitleaks", out)

    def test_findings_name_the_local_path_and_line_but_never_the_text(self):
        self.r.write("notes.md", f"a\nkey {CRED}\n")
        self.r.commit()
        rc, out = self.r.pre_push()
        self.assertEqual(rc, 1, out)
        self.assertIn("notes.md", out)

    def test_a_real_git_push_is_refused_on_a_credential_and_allowed_when_clean(self):
        self.r.install_hook()
        self.r.write("clean.md", "clean\n")
        self.r.commit()
        ok = subprocess.run(["git", "push", "origin", "main"], cwd=self.r.dir, env=self.r.env,
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.r.git("fetch", "-q", "origin")
        before = self.r.git("rev-parse", "refs/remotes/origin/main")
        self.r.write("notes.md", f"key {CRED}\n")
        self.r.commit()
        bad = subprocess.run(["git", "push", "origin", "main"], cwd=self.r.dir, env=self.r.env,
                             capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("aws-access-token", bad.stderr + bad.stdout)
        self.assertNotIn(CRED, bad.stderr + bad.stdout)
        self.assertEqual(self.r.git("ls-remote", "origin", "refs/heads/main").split()[0], before)
