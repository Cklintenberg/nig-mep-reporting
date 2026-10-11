# MEP recording and technical-review guide

**Current version · 11 October 2026.** Follow the HTML presentation’s highlighted speaker paragraphs, not its longer reference notes. Planned run: **9 minutes 40 seconds including a 3-minute demo**, with 20 seconds for pauses/window switches. Appendix is optional Q&A outside the recording; do not tour it to fill time.

| Elapsed | Slides | Purpose |
| --- | --- | --- |
| 0:00–1:10 | 1–3 | Introduction, assignment, BD ownership and MEP |
| 1:10–1:35 | 4 | Tools used and the selected reporting workflow |
| 1:35–2:20 | 5 | Time released, software running costs and the partner-growth scenario |
| 2:20–3:55 | 6–9 | Existing BD work, ICE method, task inventory and workflow selection |
| 3:55–5:20 | 10–13 | Code versus AI, manual versus automated work, canvas |
| 5:20–8:20 | 14 | One reporting workflow end to end |
| 8:20–8:45 | 15 | Drafting model choice and observed weaknesses |
| 8:45–9:10 | 16 | Future connected sources, reviewed actions and staged access |
| 9:10–9:40 | 17 | Native alternatives, four-week pilot, stop criteria and close |

## Before recording

- Refresh the presentation, then click **Speaker notes window** or press **N**. Allow pop-ups if prompted. Keep the notes window on a second monitor or outside the shared area, and share **only the presentation window/tab**, not the entire desktop. Previous/next buttons in the notes window control the slides; workflow-step clicks still jump to the matching notes. Close with **Esc** or the window close button.
- Start the app and have PowerPoint/browser windows ready. Confirm the configured reporting model locally without displaying credentials. User-supplied keys may expire; check readiness before recording, not during the demo.
- Have the five files from `prototype/sample_data/Demo files/` ready: `platform-metrics.xlsx`, `engineering-notes.docx`, `partner-call.vtt`, `vendor-call.srt`, `bd-follow-up-notes.txt`. Do not upload the README.
- Select **Engineering** and week **28 September 2026**. Use this one pack, not all the alternate demo folders together.
- Inspect one generated output against the files yourself: the numerical change, unresolved cause/fix date, proposed vendor maintenance, pending onboarding and prior open action. Known model errors are not fixed by a valid quotation. If the output misstates an owner or commitment, identify the correction honestly.
- Keep a saved synthetic report/output available if generation or rendering fails. Say that it was generated earlier if you use it; do not present it as a successful current run.
- Keep `.env`, tokens, unrelated browser tabs and real business material out of the recording. No deployment or confidential-data approval is implied by the demo.

## Three-minute prototype walkthrough

| Demo time | Action | Explain |
| --- | --- | --- |
| 0:00–0:15 | Brief Overview, then Weekly report | Overview is demonstration data. Uploaded reports do not update it |
| 0:15–0:50 | Audience/week, five uploads, Create report draft | Local extraction/preflight runs on upload; click starts generation. BD does not choose AI mode/model |
| 0:50–1:15 | Let generation run | Code calculates figures; Haiku interprets notes; quotations are mechanically checked. No automatic sending |
| 1:15–2:20 | Show one KPI, download/open PPTX | 1,000 → 1,200 is +20%. Inspect an unresolved analytics finding: no confirmed root cause/fix date. A requested date must not become an engineering commitment. Identify any incorrect wording. Mention HTML option without opening both |
| 2:20–2:45 | Reopen from Report library | Same saved report; no new AI call. BD reviews/edits the downloaded artifact; no approval form |
| 2:45–3:00 | Return to slide 15 | Transition to the model decision |

This exposes an actual difficult case without spending the recording on a second full run. Invalid sheets, missing figures, duplicate notes and injected instructions are additional test/evaluation evidence for Q&A. If a critical error appears, explain why it matters rather than claiming the model got everything right.

## Required messages in the main recording

- **Three assumptions to reinforce in the business-case and pilot discussion, slides 5 and 17:** accessible/consistent/permitted evidence; net effort reduction including corrections; adoption and useful released capacity. The pilot validates them; detailed consequences are in the technical document.
- **Tools and workflow, slide 4:** VS Code + Codex for development; Streamlit + CSS for the frontend; Python/pandas/Pydantic for calculations and checks; Anthropic Haiku for note drafting; HTML and template-based PowerPoint output. The selected workflow is weekly engineering-report preparation.
- **Business value/cost, slide 5:** scenario 8h → 2h releases 60 team hours/week for partner development with the same ten-person BD team. Target: four to ten active partners in two years. Assume $2m annual revenue/partner: $8m → $20m. Assume 20% net profit before the $500k increase in full MEP operation: $1.6m → $3.5m. Whole MEP operation is an illustrative $3m → $3.5m/year: engineering $2m → $2.3m, infrastructure/hosting $500k → $650k, support/security/access $500k → $550k. The current $3m sits inside the margin assumption; deduct only the $500k increase once. This is annual business performance at the target, not accumulated two-year income or profit attributable entirely to automation. Local software example: under $1/month at 40 benchmark-sized reports on an existing laptop. Shared-service allowance: $50–250/month at 1,000 reports; untested, not a quote, excludes people/delivery and includes a model-usage reserve. Revenue, margins and support costs are fictional assumptions. The former salary-value/25%/payback example is removed. Notes give the arithmetic and attribution limits.
- **Access roadmap, slide 16:** BD is the intended user today, not an enforced role in the local prototype. Add authenticated BD access first, internal engineers next, then restricted vendor/partner accounts. Report audience selection does not grant app access. Each organisation must see only its permitted information; these controls are future work.
- **Engineering understanding, slides 10–15:** file parsing and arithmetic use code; the model receives notes, uses audience-specific instructions and may still omit/misinterpret evidence. Quote checks do not prove truth. PPTX uses a template and the same saved content, not another AI call.
- **Build versus buy, slides 5 and 17:** compare a native Microsoft workflow before expansion. Existing identity/storage/tasks should be adopted where suitable; MEP rules/evaluations are the custom part. This alternative comparison remains proposed.
- **Kill criteria, slide 17:** during four pilot weeks, pause for a critical unsupported claim surviving review; redesign below two hours median net weekly saving per manager or below 75% usable planned reports. All failures count. Privacy incidents stop processing immediately.

## For the engineer Q&A

Follow `app.py` → `ingestion.py` → `schemas.py` / `metrics.py` → `workflow.py` / `ai.py` → `exports.py` / `report_store.py` / `presentation_export.py`. The workflow slide’s detailed reference notes contain clickable code locations. Legacy approval functions remain but are not in the current BD download path.

Use `docs/technical-design.md` as the current source of truth. Recorded model evidence is in `evaluation/workflow-model-comparison.json` and the separate assisted-intake study. Historical evaluation logs describe earlier interfaces and are not current instructions. If asked about speed: approximately seven active hours was the candidate’s earlier estimate for the initial exercise, before subsequent presentation and packaging work. It is not a verified final time log; no task-level split exists. The future pilot allowance is a separate, unscoped estimate for real-user preparation and support; it is not the cost of the prototype.

## Before submission

Record and check the finished 5–10-minute video. Confirm personal review of the example output, assemble a clean source package, exclude credentials/private runs and test a fresh setup. The submission uses a pinned public PptxGenJS dependency installed separately with npm. Check the submission verification record and visually inspect the exported deck in your presentation software. Submit technical design and executive summary before the interview. The existing local tests and recorded model runs do not replace these remaining handover checks.

## Scope reflection for questions

Appendix 4 contains the full automation/manual-work table and input-volume limits. Do not add it to the timed main run. The scenario assumes 1h figures + 4h synthesis + 2h assembly + 1h checking before, and 0.25h operating the workflow + 1.75h review/correction after. These are fictional allocations. The five-file demo is technical evidence, not a time-and-motion study. More files can create more checking rather than more savings.
