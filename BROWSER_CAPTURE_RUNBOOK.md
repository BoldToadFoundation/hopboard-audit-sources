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
3. Drop the file in `~/capture-drop/<STATE>/` (create the dir if needed).
4. Tell Crabdaddy (or note in the session): the URL you actually ended on (post-redirects),
   and roughly when. Done.

## Crabdaddy's part (script-enforced — DO NOT hand-edit manifests)

Ingest goes through the canonical capture tool, NOT a hand-assembled manifest entry
([[feedback_canonical_path_for_prod_writes]] — the script-enforced discipline IS the gate):

- **Pending tool support:** a `--from-file PATH --source-url URL --browser-captured` ingest
  mode for `capture_audit_sources.py` (~30–60 min build, priced for the batch session): same
  SHA-256/manifest/signed-commit flow, plus `browser_captured: true` + who/when in the entry,
  Perma capture still attempted from the capture machine (Perma's own crawler has different
  egress and may succeed where we 403).
- **Until that flag exists, browser-captured artifacts WAIT in the drop dir** — they are not
  in the archive, and the ledger row stays BLOCKED. No manual manifest writes.

## Chain-of-custody note

A browser capture is weaker provenance than a machine capture (no controlled UA, human in
the loop, save-dialog variability). The `browser_captured: true` flag exists so the
extraction pass and any future audit can weight it accordingly. It is disclosed degradation,
not silent substitution.
