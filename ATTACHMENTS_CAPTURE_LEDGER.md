# Renewal-attachments capture ledger — Layer-B option (c)

Ruling (Tony, 2026-06-10): capture-now/verify-later — the renewal form/checklist page is
captured at crank time; the extraction/verification pass over these frozen artifacts runs
later and is **gated pre-C3-reseed** (LAUNCH_GATES G1 RIDE-ALONGS: the reseed step must
check extraction-pass-complete and refuse/warn). Rider 1: every capture records the
~30-second completeness check — "page visibly lists attachment/enclosure requirements
y/n" — keyed on what the artifact CONTAINS, never on whether a fetch succeeded.

This ledger is that record. The capture manifests (per-state manifest.json) have no
annotation field by design; this file is the annotation layer. Completeness basis codes:
GREP = pdftotext/grep verified by Crabdaddy on the local artifact; AGENT = research-agent
fetch-verified; LOCAL = verified in the pre-existing local capture.

## 9-state catch-up — 2026-06-10 (Crabdaddy, standing capture authority)

| State | Artifact (local path) | Captured | Lists attachments? | Basis | Corpus claim shape |
|---|---|---|---|---|---|
| CA | `CA/oag.ca.gov-system-files-media-rrf1_form.pdf.pdf` (RRF-1 + embedded instructions; upgrade over the already-captured renewals page) | 2026-06-10 `921dda0` | **YES** ("together with all attachments and schedules") | GREP | NO `_annual` key — claims live in `required_attachments` booleans + `renewal.notes` (~3 items) — diff pass needs key-shape awareness |
| NY | `NY/ag.ny.gov-...char500-user-guide.pdf.pdf` (CHAR500 Online User Guide §2.10 Document Upload) | 2026-06-10 `07eff9b` | **PARTIAL** — portal-driven; authoritative list is conditional on form answers; this is the most complete official static artifact | GREP | `required_attachments_annual`: 6 items |
| OH | `OH/charitable.ohioago.gov-...List-of-Annual-Report-Q.pdf` + AG info-sheet | 2026-06-10 `c19b763` | **PARTIAL** — data-entry portal (990 figures keyed in, NOT uploaded; conditional bylaws upload only) | GREP | `required_attachments_annual`: 6 items — **pre-flag: corpus lists a 990 attachment; portal doesn't take one** |
| GA | — **BLOCKED** — sos.ga.gov 403s ALL UAs from this machine (the GA seven-source wall). Target: How-To Guide Charities page / renewal-notice PDF | — | YES per search snippets — **NOT fetch-confirmed** | — | `required_attachments_renewal`: 6 items. **Needs Tony's-browser path or alternate egress; the ONE open catch-up item** |
| MA | `MA/www.mass.gov-doc-form-pc-2023-update-download.pdf` (Form PC page-1 "Check all items attached" checklist) — pre-existing 2026-05-31 capture; mass.gov now 403s this machine (WAF regression, IP/policy-level — §3.42's UA fix insufficient) | 2026-05-31 | **YES** (form-embedded checklist) | LOCAL/AGENT | `required_attachments_annual`: 7 items |
| WA | `WA/www.sos.wa.gov-_assets-charities-charitable-organization-renewal.pdf.pdf` | pre-existing | **YES** ("IRS determination letter MUST be attached"; explicitly do-NOT-enclose-990) | AGENT | `required_attachments_annual`: 4 items — **pre-flag: corpus lists "annual financial report" attachment; form says figures are keyed in + 990 not enclosed** |
| OR | `OR/www.doj.state.or.us-...2025_web_ct-12.pdf.pdf` (domestic CT-12) **+ `OR/...2025_web_ct-12f.pdf.pdf` (CT-12F, foreign — the form Bold Toad files)** | pre-existing + 2026-06-10 `ace6a5d` | **YES** (CT-12F verified directly: 33 attachment-language hits incl. auditor-report attach directive) | GREP | `required_attachments_annual`: 5 items. **Rider-1 disposition (2026-06-10 review): the domestic-only capture was a FAILED completeness check for the applicable entity class, not a mere pre-flag — cured by capturing the CT-12F rather than reasoning around it. Extraction for OR must diff against the CT-12F.** |
| NH | `NH/mm.nh.gov-...nhct12-instructions.pdf.pdf` (explicit "Enclosures or Attachments:" section) — mm.nh.gov now 403s this machine (WAF regression since the 2026-05-29 bare-UA fix; recapture blocked, existing capture unaffected) | 2026-05-29 | **YES** | LOCAL | `required_attachments_annual`: 5 items |
| FL | `FL/forms.fdacs.gov-10100.pdf.pdf` (FDACS-10100, embedded financial-statement options + "return it with all attachments") — Perma/Wayback queued-retry, local capture signed + hashed | 2026-06-10 `d8d0580` | **YES** | GREP | NO `_renewal` key — claims in `required_attachments.other` (8 items) + notes — key-shape awareness needed |

## Extraction-pass pre-flags (carry into the diff)

**STATUS DISCIPLINE: every pre-flag below is a SINGLE-ARTIFACT OBSERVATION awaiting the
extraction pass + review gate — NOT a settled fact, NOT a license to edit the corpus now.
Acting on these outside the verified-write gate would be exactly the unverified-write the
regime prohibits, however plausible the artifact makes them look (review ruling 2026-06-10).**

1. WA + OH: corpus claims a 990/financial-report *attachment*; one official artifact each
   says figures are keyed in / explicitly not enclosed — **observation, awaits diff pass;
   do not read "portal doesn't take a 990" as established.**
2. ~~OR: capture CT-12F~~ — RESOLVED 2026-06-10 (`ace6a5d`); see the OR row's rider-1
   disposition. Extraction diffs against the CT-12F.
3. CA + FL: renewal-attachment claims live outside the `_annual`/`_renewal` keys — the diff
   must be key-shape-aware or it will false-clear both states.
4. NY + OH PARTIAL is by state design (portal-conditional) — extraction for these two yields
   "static-artifact floor + portal-conditional remainder", not a complete list.

## 403 wall — protocol risk, not per-state inconvenience (2026-06-10)

Three states' official hosts now block this machine: sos.ga.gov (all UAs, long-standing),
mm.nh.gov + mass.gov (NEW regressions since their 05-29/05-31 captures — IP/policy-level;
the §3.42 UA fix no longer suffices). The trendline is one-way (state portals hardening
against datacenter egress) and erodes the capture protocol's substrate. **Standing rule:
hitting a wall during a crank block is NOT solved ad hoc in-block — flag the state here,
continue the crank, route to the batch session.** Egress options priced for the batch
session live in the week-one close-out thread; GA routes to the Tony-browser path
(`BROWSER_CAPTURE_RUNBOOK.md`).

## Going forward (protocol)

Every new state cranked under the pipeline captures its renewal form/instructions page in the
same audit session (~3–5 min) and appends a row here. GA joins the table when an egress path
exists. Capture-tool annotation limitation (no manifest note field) is WHY this file exists.
