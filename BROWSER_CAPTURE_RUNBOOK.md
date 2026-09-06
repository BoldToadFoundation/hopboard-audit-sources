# Browser-capture runbook — for hosts that 403 the capture machine

When a state's official host blocks datacenter egress (GA today; the 403-wall list lives in
`ATTACHMENTS_CAPTURE_LEDGER.md`), the capture routes through Tony's browser (residential IP).
Design goal: **Tony's part takes five minutes; everything else stays script-enforced.**

## Tony's part (~5 minutes)

1. Open the target URL in your normal browser (Crabdaddy supplies the exact URL and what the
   page should contain — e.g. "GA How-To Guide: Charities; should list renewal attachments").
2. Save the artifact AS-IS:
   - PDF → just download it (don't print-to-PDF a PDF — keep original bytes).
   - Web page → "Save Page As… → Webpage, HTML Only" (not "Complete" — single file).
3. Drop the file in **`hopboard-audit-sources/.capture-drop/<STATE>/`**
   (full path: `/mnt/data/ngo-go/hopboard-audit-sources/.capture-drop/<STATE>/`).
   Create the state dir if needed.

   > **MOVED 2026-08-08 (Tony).** This was `~/capture-drop/<STATE>/`. The home-dir
   > path was namespaced by STATE, not by project — a shared catch-all, which the
   > standing "keep each project's data under its own dir" rule exists to prevent
   > (an `AZ/` drop for a second project would have collided). The staging dir now
   > sits one directory from the archive it feeds. Contents are gitignored, which
   > buys back the only thing the home-dir location provided: a raw, half-saved or
   > WAF-challenge page can never reach a commit just by sitting in staging.
   > Nothing in code ever read the old path — `--from-file` takes an explicit path
   > argument — so this is convention only.
4. Tell Crabdaddy (or note in the session): the URL you actually ended on (post-redirects),
   and roughly when. Done.

## Crabdaddy's part (script-enforced — DO NOT hand-edit manifests)

Ingest goes through the canonical capture tool, NOT a hand-assembled manifest entry
([[feedback_canonical_path_for_prod_writes]] — the script-enforced discipline IS the gate):

- **✅ BUILT — this said "pending tool support" until 2026-09-06 and was stale by ~3 months.**
  The ingest mode is `--from-file PATH --from-file-url URL --from-file-provenance TEXT`
  (all three required together), built 2026-06-11 for the AK Perma-WARC localization. Same
  SHA-256 / manifest / signed-commit flow, no hand-edited manifests. Provenance is free text;
  the runbook's convention is `browser_captured per BROWSER_CAPTURE_RUNBOOK` (the flag's own
  `--help` gives that as the example). `--from-file-primary` marks the artifact load-bearing.
- **It has been used.** 54 manifest entries already carry a browser-capture provenance:
  11 `browser_capture_2026-08-08` and **43 `browser_captured (automated variant): playwright
  chromium-1223 headless, raw HTTP response.body() bytes`** (HI, 2026-08-18).
- **⚠ TWO DIFFERENT WALLS, and only one needs Tony.** The distinction was not written down and
  it is the whole cost question:
  - **JS-render walls** (the host returns 200 with an empty SPA shell). **Automatable** — this
    is what the HI 43 did. Measured 2026-09-06: `sdlegislature.gov/Statutes/37-30` returns
    HTTP 200 / 5,982 bytes / zero "37-30" hits to curl, and **28,015 chars with 73 "37-30" hits
    under headless Playwright**. No residential IP needed.
  - **IP / datacenter blocks** (403 to every UA from this machine — GA's `sos.ga.gov` is the
    live one). **These need Tony's browser**, and only these.
  Classify the wall BEFORE routing to a human; the default assumption that a wall means Tony
  is what made SD's F7 residual look like it was queued behind a person.

## Chain-of-custody note

A browser capture is weaker provenance than a machine capture (no controlled UA, human in
the loop, save-dialog variability). The `browser_captured: true` flag exists so the
extraction pass and any future audit can weight it accordingly. It is disclosed degradation,
not silent substitution.

## ⛔ SIDECAR ENTRY IS PART OF THE CAPTURE, NOT A FOLLOW-UP (2026-08-21, Tony)

**A capture without a sidecar entry silently blocks that state's next apply —
during whatever unrelated write happens to come first.** Measured: DC §44-1701
was captured here on 2026-08-19 with no sidecar entry and blocked every DC apply
for two days, surfacing only when an unrelated carry-forward tried to land. Five
other captures were in the same state (CA, IL, OR, UT ×2).

**This runbook is why they exist.** It described how to get bytes past a wall and
into a manifest, and never mentioned `PERMA_VERIFY_STRINGS.json` — so the
walled-site path produced uncovered captures *by construction*, while the
canonical `capture_audit_sources.py` path did not.

**So: a capture is not finished until its sidecar entry exists.** Two forms, and
the choice is a judgment about what the capture BACKS:

- **strings** — one or more verbatim substrings that are PRESENT IN THE LOCAL
  BYTES (grep the artifact before writing them; do not transcribe from the
  rendered page — the SC "½" vs "4 1/2" transliteration proves a generated
  string can fail the very grep it powers), plus a `basis` sentence naming what
  the capture supports.
- **skip** — a documented reason the artifact cannot be string-verified (a PDF
  whose text is FlateDecoded, an image scan), still with a `basis`.

`scripts/check_perma_sidecar.py` is wired into hopboard's pre-commit as of
2026-08-21 and BLOCKS a new uncovered capture. The declared backlog lives in
`scripts/perma_sidecar_baseline.txt`; adding to it is not a substitute for a
disposition.
