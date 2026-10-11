# Reporting workflow validation

Both providers now generate live reports. The prototype also completes a live OpenAI run through the browser approval and download path, and removes approval after an edit. This validates the implemented workflow on the fictional examples; it does not establish production reliability or actual BD time savings.

## Measured comparison on 8 October 2026

One output per model per case, with identical input and prompt hashes. The normal week was the development case; four other cases were held out from prompt changes during this run. Both adapters used low reasoning effort and a 6,000-token output limit. Provider tokenization and SDK schema handling differ.

| Configuration | Completed | Reports passing quotation checks | Median generation time | Estimated cost for five reports |
| --- | --- | --- | --- | --- |
| Non-AI baseline | 5/5 | 5/5 | Under 0.01 seconds | $0 |
| OpenAI gpt-6-luna | 5/5 | 5/5 | 7.84 seconds | $0.0023552 |
| Anthropic claude-haiku-5-5 | 5/5 | 5/5 | 5.51 seconds | $0.0040549 |

All 28 OpenAI and 50 Anthropic quoted passages matched their cited source text. Cost estimates use actual token counts and the dated rate table, not billing records. The ten comparison reports total an estimated $0.0064101. A separate live UI verification request cost an estimated $0.0004871 and is excluded from the paired comparison. Costs of rejected requests are unknown and are not included.

## What worked

The Codex assistant reviewed each output against the criteria and original sources. Both models retained the key normal-week facts, distinguished the requested 9 October deadline from an agreed engineering commitment, grouped duplicate feedback and did not follow the injected instruction. Missing availability remained missing and no change was invented; that safeguard belongs to deterministic Python processing, not the model.

The saved evidence is `live-comparison.json`, available through Model comparison → Load recorded evaluation. Original provider run IDs, response IDs, token usage, input hashes and prompt hashes remain with each result. Assistant observations are separate from the still-uncompleted independent human review fields.

## Observed failures and limitations

| Observation | Why it matters | Handling |
| --- | --- | --- |
| Anthropic initially rejected two requests because the identity-linked key needed a workspace ID | A valid key does not guarantee that a provider adapter is configured correctly | Added the workspace header using the existing Default workspace; retained the setup failure outside the post-fix comparison and added a regression test |
| OpenAI marked an open action as not needing review in the normal and conflicting-date cases despite missing completion evidence | Review flags are not a reliable way to select which findings people should inspect | Every finding still requires review before approval; preserve the source uncertainty in the text |
| Anthropic often quoted only part of the evidence behind a finding | Exact matching quotations do not establish support for every claim in the summary | Check full source text, not just the displayed snippet |
| Anthropic's untrusted-note case said the action owner was not stated, although the source names BD | Lack of an individual assignee was overstated as lack of any owner | Correct to “No individual assignee or due date is specified” if needed; do not use that note unchanged |
| Anthropic asked when Tokyo would report findings even though the source says the next weekly meeting | Redundant questions create unnecessary meeting work | Remove the already-answered part of the question |
| Anthropic repeated a description of the malicious instruction as a risk finding | The attack did not succeed, but irrelevant source instructions still entered the business report | Omit the extra finding; preserve substantive platform risks |
| The baseline repeats duplicate feedback and copies the untrusted note | Verbatim assembly leaves grouping and interpretation to the reviewer | Keep it as a simple alternative, then measure whether AI reduces human review effort |

The provisional demo choice is OpenAI gpt-6-luna: concise findings, generally fuller evidence excerpts and lower estimated cost in this set. Anthropic was faster and remains a working alternative. Five synthetic examples and one output each are insufficient for a robust model ranking. The injected note is deliberately conspicuous and labels itself untrusted, so its handling is only a basic check, not a security claim.

## Workflow verification

Thirty-two automated tests pass, covering arithmetic, units, dates, cohorts, missing values, invalid citations, provider dispatch, the Anthropic workspace header, HTML escaping and approval state. Chrome verification covered real OpenAI generation → approval → JSON download → edit → approval removed, with no JavaScript errors. The test reviewer is explicitly labelled “Automated UI verification — not human sign-off.” This is a UI test, not a BD acceptance record.

## Remaining evidence before production

Have the candidate or BD owner independently review the saved reports, record corrections and time the review. Then compare real end-to-end preparation effort with the manual baseline. Add representative messy and multilingual sources, stronger injection attempts, larger packs and repeated trials. Once these examples influence prompt changes, they become development examples and a fresh holdout set is needed. API availability and these small-case results do not prove the assumed six-hour weekly saving.

## Additional office file check

After adding ordinary file intake, both providers generated reports from a fictional VTT transcript, DOCX engineering notes, SRT vendor call, pasted BD notes and XLSX workbook. All quoted text matched the extracted sources. The XLSX values, including percentage-formatted cells, produced the same metrics as the original CSV. Source names, hashes and excerpt offsets were retained. OpenAI took 9.93 seconds and Anthropic 17.99 seconds for these single requests; these timings are not combined with the earlier five-case benchmark.

The assistant checked the drafts against the new material: both retained the lack of a confirmed analytics cause/fix date, the open BD action, pending onboarding validation, absence of measured revenue loss, and the provisional nature of vendor maintenance. Review-flag and redundant-question limitations remain. Missing calendar dates are visibly flagged rather than invented. The output schema now also permits a neutral source-note category for non-AI excerpts; new report records include a schema hash.

A browser check also completed XLSX and meeting-file upload, pasted notes, non-AI draft generation, approval and JSON download. The downloaded record retained the worksheet, original spreadsheet row mapping and source-file provenance. Its reviewer is explicitly labelled as an automated UI test, not independent human sign-off.

## Local report history regression check

After a user reported a disappearing draft, the input-change deletion was replaced with a visible mismatch warning. New drafts and committed edits now persist locally, and Report library can reopen them and prior approved exports. The automated suite now passes 34 tests, including navigation/fresh-session restoration and approval invalidation after reopening and editing. This does not recover unapproved drafts lost before autosave was introduced.

A separate browser check passed generation, summary editing, navigation, reopening, page reload and reopening again without an AI call. Its synthetic test draft was moved out of the user-facing library after verification.

## Audience-specific briefs and visual updates

Engineering, Vendor and Partner now share the internal report workflow with audience-specific AI instructions, saved audience metadata and export titles. The audience is part of input identity and prompt hashing. Thirty-eight tests pass, including audience-specific hashes, unchanged arithmetic, export labels and rejection of unknown types. Calendar week/month navigation and selection, local logo rendering and audience restoration were also checked.

OpenAI generated one report per audience on the same office-file example. The initial prompts produced excessive overlap, so instructions were revised to order findings by audience and omit unrelated vendor material. Both sets are preserved in `audience-smoke-initial.json` and `audience-smoke.json`; these are development smoke checks, not a held-out benchmark. The revised Engineering draft leads with the investigation, Vendor with proposed maintenance, and Partner with partner feedback. All exact-quote checks pass, but human review remains necessary: the Vendor draft's statement that no reliability update was supplied requires reading the whole call, since its individual quote alone does not establish absence. Some unresolved topics still have needs_review=false despite uncertainty in the wording.

The older five-case OpenAI/Anthropic comparison remains unchanged and used the prior prompt. The new variants have only been smoke-tested live with OpenAI, not re-benchmarked across providers. These are internal BD preparation packs, not externally cleared partner/vendor reports.

## Upload-only UI check · 8 October 2026

Removed sample/scenario selection, in-app sample downloads, the input preview and the introduction banner from Weekly report. File validation and visible warnings remain. Existing tests now supply office-file bytes at the upload boundary; all 38 tests pass. A browser check uploaded the Excel workbook and TXT/VTT/SRT/DOCX files, generated a baseline draft, edited it, and reopened the saved draft from Report library. Three local Demo files sets passed CSV/XLSX parsing and baseline generation. New vendor and partner notes are fictional demo material, not additional live benchmark evidence. Workflow understanding remains unconfirmed.

## Unified upload check · 8 October 2026

One upload area accepts a mixed selection and classifies files by extension. Missing or multiple platform spreadsheets block generation with explicit guidance. Two additional UI checks cover these ambiguous/missing input cases; all 40 tests pass. Browser validation confirmed one uploader with coloured format icons, Excel/DOCX/TXT/VTT/SRT intake together, baseline generation and library reopening. No live model call was made for this UI change.

## Simplified controls and PDF intake · 8 October 2026

Reporting week copy and upload instructions simplified; mode uses a Non-AI / AI-assisted toggle, with a compact draft button. Repeated accepted-format text is hidden only in the upload dropzone. Both Streamlit and parser limits are now 10 MB per file. pypdf extracts text with page markers; PDFs are limited to 50 pages, 40,000 combined note characters and a 20 MB decoded content-stream check. Malformed/encrypted PDFs and pages with no readable text are rejected explicitly. No OCR or visual interpretation. Six new tests cover PDF provenance, unsupported inputs and the size boundary; all 46 tests pass. Browser checks exercised both toggle states, uploaded a 2.1 MB PDF alongside CSV metrics, generated a baseline draft and reopened it from the library. This is not a live AI evaluation or human sign-off.

## Automatic worksheet selection · 8 October 2026

Removed worksheet dropdown and upload introduction. Excel intake selects the unique sheet whose first row contains the required metric headings; absent or ambiguous matches fail explicitly. Detection is independent of sheet title and position. Three new tests cover renamed/reordered sheets, ambiguity and a misleading Metrics title without the required columns; all 49 tests pass. A browser check uploaded the five files from sample_data/Demo files and generated a baseline report, showing the workbook and sheet name below its figures. No live AI call or human sign-off. Demo guide now explains synthetic exports, column-based detection, deterministic numerical calculations and separation from the Overview fixture.

## Haiku / Gemini / Mistral comparison · 9 October 2026

Evidence: `workflow-model-comparison.html` and its companion JSON. Six frozen engineering-report cases (five existing regression cases plus the actual five files in `sample_data/Demo files`), two trials per model, with six non-AI baseline outputs. Same per-case input, prompt and schema hashes verified. This is familiar synthetic development evidence, not a held-out or production benchmark. Reasoning settings differ: Haiku low adaptive, Gemini low, Mistral instruct. Metrics are computed locally; missing-metric checks do not measure model skill.

Haiku 5.5 completed 12/12, with 12/12 exact-quote checks, median workflow time 5.32 seconds and estimated completed-call cost $0.010115. Gemini 3.5 Flash-Lite completed 12/12, with 12/12 exact-quote checks, median 2.83 seconds and estimated cost $0.027294. Standard token estimates include exposed thought tokens, exclude failed/setup/diagnostic calls, and are not verified billing amounts. Provider runs were not simultaneous paired latency tests. Prices checked against official provider pages linked in the HTML.

Assistant review found that Gemini omitted the previous open BD action in both demo-file outputs. Haiku retained it, but claimed no owner was recorded even though BD is the stated team owner; its second demo output also overstated missing update timing. Both have inconsistent uncertainty flags. Both preserve the distinction between requested and committed dates and ignore the injected instruction in these trials, but Haiku unnecessarily includes that instruction as a business finding. Exact quotations do not establish complete claim support. Human sign-off remains pending.

Mistral Small 4 (`mistral-small-2603`) returned HTTP 429 / rate_limited / code 1300, including a minimal diagnostic request and a later bounded benchmark retry. There is no Mistral quality result. Initial network setup failures and Gemini adapter failures (an optional stored interaction ID was incorrectly required) are retained separately. The repaired Gemini adapter works with store=False and no returned ID. Rerun only Mistral after account access is fixed using `.venv/bin/python compare_workflow.py --providers Mistral --retry-failed`; successful outputs are reused and earlier failures retained.

Provisional preference among completed configurations: Haiku for completeness and measured token cost, with human corrections required. This is not a three-way winner, a retention certification, or proof that nothing is lost. PDF/OCR, legacy DOC, long documents, multilingual content, production load and account retention terms were not tested. Workflow-understanding checkpoints remain unconfirmed.

The user-suggested activation-window retry also returned HTTP 429 using the exact model ID. The account cause remains unconfirmed. All 54 automated tests pass, including new provider dispatch, Gemini no-storage-ID handling and thought-token accounting, Mistral truncation rejection, and sanitized HTTP errors. The comparison HTML renders without horizontal overflow; its recorded outputs and manual-review controls load in the app without API calls.

## Mistral paid-account completion · 9 October 2026

After the user enabled pay-as-you-go, Mistral Small 4 (`mistral-small-2603`, instruct mode) completed the same six cases twice. All per-case input, prompt and schema hashes match the Haiku and Gemini evidence. Mistral median workflow time was 4.13 seconds and estimated completed-call token cost $0.007361 for 12 reports (about $0.61 per 1,000 at this short-input mix). Earlier 429 attempts are retained in prior_attempts. The old blocked assessment is preserved in assessment_history and superseded on the comparison page.

Exact-quote checks passed 11/12. In uploaded_demo trial 2, a DOCX table quote collapsed two newlines to one; the underlying table value is unchanged, but the exact-match validator correctly blocks approval until correction. Neither the validator nor outputs were changed to improve the score. Mistral retained the open BD action in both uploaded-file runs. Assistant review also found an unsupported dependency in normal trial 2, a question about an already-completed internal review in conflicting_dates trial 2, inconsistent review flags, and an omitted explicit revenue caveat in demo trial 1. Human sign-off remains pending.

Mistral Small 4 is the main comparator because it offers low-cost general-purpose structured output ($0.15 input / $0.60 output per million tokens). Ministral 3 8B ($0.15 / $0.15) is a possible later cost-floor comparison, not tested here. Official model pages are linked in the evidence JSON. No model selection implies verified retention terms. Haiku remains a provisional demo preference based on complete quote validation and retained caveats, not a claim of flawless output.

## Automatic weekly-report drafting · 9 October 2026

Removed the AI/non-AI toggle and provider/model selectors from Weekly report. Create report draft now uses live AI automatically, with Anthropic / claude-haiku-5-5 as the operator-configured default. MEP_REPORT_PROVIDER and MEP_REPORT_MODEL can be changed locally; BD users do not choose them. Model comparison retains the baseline and configurable models. Notes-to-provider disclosure, human review, source validation and saved provenance remain. Missing credentials disable generation; service failure never silently produces a baseline. The automated suite passes 57 tests, including routing, credential failure and no-fallback checks. AI UI tests use a simulated response with no paid calls. Local preview restarted to clear the cached module; native browser validation checks uploads and controls without invoking generation.
