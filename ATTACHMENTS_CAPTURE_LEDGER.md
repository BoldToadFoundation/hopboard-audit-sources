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
| MA | `MA/www.mass.gov-doc-form-pc-2023-update-download.pdf` (Form PC page-1 "Check all items attached" checklist) — pre-existing 2026-05-31 capture; mass.gov now 403s this machine (WAF regression, IP/policy-level — §3.42's UA fix insufficient). **BYTE-CONFIRMED 2026-06-12, independent channel:** Tony's browser-downloaded full Form PC (fillable, rev 01/2023, 15pp) is sha-IDENTICAL to this artifact (`c7513ebf…`) — two capture paths, different clients/days, same bytes; no duplicate ingest (staging copy retired after verification). Perma `5Y6J-ARR7` = **capture-incomplete** (JS-triggered download glitches Perma's capture entirely — see §Perma-incompatible content classes); annotated known-incomplete, NOT deleted. This artifact = MA's local re-homing substrate (the verification row stays Wayback-only until the sweep converts it). | 2026-05-31 | **YES** (form-embedded checklist) | LOCAL/AGENT | `required_attachments_annual`: 7 items |
| WA | `WA/www.sos.wa.gov-_assets-charities-charitable-organization-renewal.pdf.pdf` | pre-existing | **YES** ("IRS determination letter MUST be attached"; explicitly do-NOT-enclose-990) | AGENT | `required_attachments_annual`: 4 items — **pre-flag: corpus lists "annual financial report" attachment; form says figures are keyed in + 990 not enclosed** |
| OR | `OR/www.doj.state.or.us-...2025_web_ct-12.pdf.pdf` (domestic CT-12) **+ `OR/...2025_web_ct-12f.pdf.pdf` (CT-12F, foreign — the form Bold Toad files)** | pre-existing + 2026-06-10 `ace6a5d` | **YES** (CT-12F verified directly: 33 attachment-language hits incl. auditor-report attach directive) | GREP | `required_attachments_annual`: 5 items. **Rider-1 disposition (2026-06-10 review): the domestic-only capture was a FAILED completeness check for the applicable entity class, not a mere pre-flag — cured by capturing the CT-12F rather than reasoning around it. Extraction for OR must diff against the CT-12F.** |
| NH | `NH/mm.nh.gov-...nhct12-instructions.pdf.pdf` (explicit "Enclosures or Attachments:" section) — mm.nh.gov now 403s this machine (WAF regression since the 2026-05-29 bare-UA fix; recapture blocked, existing capture unaffected) | 2026-05-29 | **YES** | LOCAL | `required_attachments_annual`: 5 items |
| FL | `FL/forms.fdacs.gov-10100.pdf.pdf` (FDACS-10100, embedded financial-statement options + "return it with all attachments") — Perma/Wayback queued-retry, local capture signed + hashed | 2026-06-10 `d8d0580` | **YES** | GREP | NO `_renewal` key — claims in `required_attachments.other` (8 items) + notes — key-shape awareness needed |

## Crank-block captures (states #17+, per-state at crank time)

| State | Artifact (local path) | Captured | Lists attachments? | Basis | Corpus claim shape |
|---|---|---|---|---|---|
| ME | `ME/www.mainelegislature.org-legis-statutes-9-title9sec5004.html.html` (§5004(5) = the STATUTORY renewal-content list: AFAR + disciplinary/court disclosures w/ disposition documents + change-updates + director's-discretion item) + OPOR licensing page ("Completed Application and supporting documents; Annual Fundraising Activity Report") + AFAR PDF | 2026-06-11 `0936ef4` | **YES** (statutory enumeration captured; AFAR itself = on-form figures, NO enclosure language — WA-style keyed-in) | GREP | Seed claims live in `required_attachments` dict but are **initial-application-phrased** (form_990 TRUE note says "with initial application"); renewal-side claims are in `notes` prose — extraction diff needs key-shape awareness (CA/FL-class). Renewal side per §5004(5): NO 990/budget attachment. |
| AK | `AK/www.law.alaska.gov-consumer-charityreg.html.html` (reg page aggregates the FAQ sections: "You will not need to attach any documents to your application"; 990/audited financials only on Department request) + RegInstructions-Online PDF. **STATUTE LOCALIZED 2026-06-11 PM `a6459c6`:** `AK/www.akleg.gov-basis-statutes.asp-45.68.warc.gz` — authenticated api.perma.cc WARC download of 4VWP-52Z5 (Perma headless render of the full ch. 68 text; Tony visual confirmation + byte-grep: 45.68.010(a)/(d), §45.68.120 verbatim, history tail SLA 2004/2006), ingested via the new `--from-file` flag (no hand-edited manifest), supersedes the JS-shell entry; provenance local-primary/Perma-secondary per the 2026-06-11 standard | 2026-06-11 `8a84206` | **YES — explicit NO-attachments regime** (verbatim on the captured reg page; AK explicitly does not take 990s — a documented ABSENCE) | GREP | Seed `required_attachments` claims should reflect none-required; extraction diff: AK is an absence row. ⚠ degraded-artifact history (disclosed, both RESOLVED): `charityFAQ.html` = 200-masked F5 WAF body (FAQ content verified inline on the primary's raw HTML; queued retry **DISCHARGED 2026-06-12** by the FAQ-expanded browser-print PDF below; Perma `D3XT-JZYV` still UNVERIFIED — completeness-grep candidate); akleg JS shell **SUPERSEDED** by the localized 4VWP-52Z5 WARC (Tony visual + byte-grep 2026-06-11 PM; the 06-09 apply precondition SATISFIED). **NEW 2026-06-12 `510246b`:** `AK/www.law.alaska.gov-department-civil-consumer-charityreg.html-FAQ.pdf` — capture-method **principal-browser-print 2026-06-12** (Tony print-to-PDF, ALL FAQ sections EXPANDED, 8pp, source URL in footer; `/department/civil/` path alias of the primary). Reason: Perma `49ZU-2X2A` renders the FAQ COLLAPSED (capture-incomplete — see §Perma-incompatible content classes); 49ZU-2X2A annotated known-incomplete, NOT deleted (honesty trail). |

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
continue the crank, route to the batch session.**

**Approved path (Tony, 2026-06-10): option (b)** — Tony-browser capture
(`BROWSER_CAPTURE_RUNBOOK.md`) + a `--from-file` ingest flag built at the next batch
session; browser artifacts WAIT in the drop dir until the flag exists (no informal archive
entries); `browser_captured: true` disclosed provenance.

**Option (a) — residential/alternate egress — activates on EITHER trigger (amended 2026-06-10):**
- **Count:** walled-host total reaches ~6 of 51; OR
- **Rate:** ≥2 NEW hosts wall in any 14-day window (slope is trend confirmation regardless
  of level); OR a wall blocks a deadline-verification source (not just attachments) mid-crank.

**STANDING PROCEDURE (Tony rulings 2026-06-11, egress riders a+b):**
- **Re-probe-before-count:** a host is NOT a durable wall until it fails a re-probe ≥48h
  after first block (this HEAVY existed partly because self-caused transient blocks were
  logged as walls). Log the first block as PROVISIONAL with its date; promote to durable
  only on the failed re-probe.
- **Escalation trigger (measurement window through ~2026-06-25):** escalate to the (a1)
  residential-egress review if ≥2 NEW durable walls appear under the 4s politeness cap,
  OR any durable wall blocks an active-crank-path state with no archive alternative
  (Wayback snapshot or Perma headless render both count as alternatives — the AK statute
  proved the Perma-render channel). **CONTENT-CLASS QUALIFIER (Tony ruling 2026-06-12):
  Perma counts as an alternative ONLY for content it demonstrably captures completely —
  static scrolling text, the AK-statute case that earned the clause. Interaction-gated
  content (click-to-expand) and JS-triggered downloads are documented Perma-INCOMPATIBLE
  (see §Perma-incompatible content classes below) and do NOT satisfy the
  archive-alternative condition.**
- **Politeness:** 4s floor between fetches + published robots.txt Crawl-delay honored
  where larger (survey 2026-06-11: oag.ca.gov publishes 10s — honored; no other captured
  host publishes above the floor).

**Walled-hosts log** (the wall-rate data — batch sessions read THIS table, not logs; append a
row the moment any capture 403s; note when Perma's independent crawler succeeds where we
403 — that's the free measurement on whether (a) is even needed):

| Host | Walled (observed) | Window evidence | Perma succeeds? |
|---|---|---|---|
| sos.ga.gov | long-standing (≤2026-05-25, GA audit "seven-source wall") | all UAs, pre-dates this ledger | untested |
| mm.nh.gov | between 2026-05-29 (successful bare-UA capture) and 2026-06-10 | both UAs, IP/policy-level | untested |
| mass.gov | between 2026-05-31 (successful capture) and 2026-06-10 | both UAs, incl. previously-served URLs | untested |
| law.alaska.gov (PARTIAL — URL-selective) | 2026-06-11 (AK crank) | `charityFAQ.html` returns a **200-masked F5 "Request Rejected" body** to the capture client while `charityreg.html` + a PDF on the same host serve clean — URL-pattern WAF rule, not IP-level. NEW failure mode for the log: a 200 rejection page archives SILENTLY (no fetch_failed); rider-1 byte-grep is what caught it | likely (D3XT-JZYV, different egress) — UNVERIFIED. ⚠ 2026-06-12: same host's `49ZU-2X2A` "succeeded" but renders the FAQ COLLAPSED — Perma-success ≠ complete (see §Perma-incompatible content classes) |
| (not walls, recorded for completeness) akleg.gov = JS-only publisher (httpx 200 shell, no statute text server-side); law.justia.com + touchngo.com mirrors block this machine | 2026-06-11 | — | akleg Perma 4VWP-52Z5 render UNVERIFIED |

**⚠ RATE-TRIGGER QUESTION — WITHDRAWN 2026-06-11 PM (live re-probe re-sorted the
evidence; Tony's behavior-vs-IP challenge was right):** mm.nh.gov and mass.gov **both
served 200-clean to this machine with the capture UA on 2026-06-11 re-probe** (NHCT-12 PDF
389KB; mass.gov FAQ 202KB; previously-"walled" URLs included). They were TRANSIENT
rate/behavior-triggered blocks — very plausibly SELF-INFLICTED by the 2026-06-10
nine-state catch-up burst (the capture pipeline had **zero inter-request delay** until
today). Corrected wall census: **sos.ga.gov = the only durable wall** (403 re-confirmed
2026-06-11); law.alaska.gov = URL-selective behavioral rule (not IP-class); mm.nh.gov +
mass.gov = transient, rows retained for history with this correction. The ≥2-new-hosts
slope condition is NOT met on corrected data. **Mitigation shipped 2026-06-11:** the
capture script now enforces a 4s politeness gap between fetches AND refuses to archive
200-masked WAF bodies (raises → fetch_failed queue) — both the rate-trip cause and the
silent-archive symptom are closed. Egress ruling input: see hopboard
docs/EGRESS_DECISION_PACKAGE_20260611.md (revised: politeness-cap-first, measure ~2 weeks,
(a) shelved unless durable walls accumulate).

Rate-trigger watch: mm.nh.gov + mass.gov both walled within ≤12 days of each other's last
success — IF their actual wall dates land in the same 14-day window, the slope condition is
already arguably met; we can't resolve the true dates from here (observed only at next
attempt). The NEXT new wall settles it: one more host in 14 days from its observation date
fires the trigger unambiguously.

## Perma-incompatible content classes (capture-incomplete — the success-shaped-failure family)

Found 2026-06-12 (Tony dashboard pass): a NEW corruption class — captures that are **bad
without being broken**. Both resolve, both render, both look green; the load-bearing content
is missing. This is the 200-masked WAF body's cousin one layer up: HTTP succeeded, archive
"succeeded", content didn't. Resolution-checking catches rot but would have PASSED both.

**Documented Perma-incompatible classes** (Perma captures initial page state only):

1. **JS-only publishers** (the established akleg class) — server serves a shell; content is
   client-rendered. Perma's *headless render* CAN work here (4VWP-52Z5 carried the full
   ch. 68 text) — this class is case-by-case, verify-before-trust.
2. **Interaction-gated content** (NEW 2026-06-12) — click-to-expand sections captured in
   initial (collapsed) state. Instance: Perma `49ZU-2X2A` (law.alaska.gov charityreg) —
   FAQ sections collapsed in the Perma render; the FAQ holds load-bearing facts (Sep-1
   expiry regardless of filing date, Jul-1 window open, one-time Notice of Exemption).
   NB the *local raw-HTML* capture carries the text byte-present-but-collapsed (expand
   toggles are client-side over present-in-DOM content) — so a byte-grep can PASS while
   the visual render is incomplete; the two layers are distinct claims.
3. **JS-triggered downloads** (NEW 2026-06-12) — the link fires a scripted download Perma
   can't follow; the capture glitches entirely. Instance: Perma `5Y6J-ARR7` (mass.gov
   Form PC `/doc/form-pc-2023-update/download`).

**Known-incomplete Perma annotations (do NOT delete — the honesty trail is the point):**

| Perma | Source | Failure mode | Remediation |
|---|---|---|---|
| `49ZU-2X2A` | law.alaska.gov charityreg (AK primary) | interaction-gated: FAQ collapsed in render; byte-layer unverified | principal-browser-print PDF (FAQ expanded) ingested 2026-06-12 `510246b`; local raw HTML carries FAQ inline (byte-verified) |
| `5Y6J-ARR7` | mass.gov Form PC download (MA) | JS-triggered download: Perma capture glitched entirely | local 05-31 capture-script artifact intact + byte-confirmed 2026-06-12 via Tony's independent browser download (sha-identical) |

**Standing consequences:** (a) fresh captures of interaction-gated / JS-download content
route to the browser-capture path (like GA), not Perma; (b) the Perma-verify rider carries
a per-artifact completeness assertion (load-bearing-string grep against the WARC via
api.perma.cc), not just link-resolution — byte-layer; render-layer incompleteness (class 2
with content in DOM) is only caught by eyeball/dashboard passes, disclosed honestly here.

## Going forward (protocol)

Every new state cranked under the pipeline captures its renewal form/instructions page in the
same audit session (~3–5 min) and appends a row here. GA joins the table when an egress path
exists. Capture-tool annotation limitation (no manifest note field) is WHY this file exists.
