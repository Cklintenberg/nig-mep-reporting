# Assisted intake: benchmark and confidentiality decision

Status: BENCHMARK COMPLETE, 9 October 2026. Assisted intake remains unimplemented. This evaluates a future stage between extraction (2) and deterministic validation (3), separately from report drafting. Production confidentiality eligibility and independent human review remain pending.

[Open the full scorecard, failure cases and official policy sources](../evaluation/assisted-intake/index.html). [Raw scored results](../evaluation/assisted-intake/results.json).

## Result and recommendation

Recommend **Gemini 3.8 Flash as the candidate for the next assisted-intake build**, conditional on an approved confidential-data deployment and reliability improvements. None of the three accounts is cleared by this exercise for highly confidential business material.

| Model | Full case passes | Median / p95 | Estimated tokens per 1,000 test-sized intakes |
| --- | --- | --- | --- |
| Claude Haiku 5.5 | 112 / 120 | 2.55s / 4.08s | $0.38 |
| Gemini 3.8 Flash | 117 / 120 | 3.01s / 22.38s | $1.45 |
| Mistral Small 4 | 87 / 120 | 1.08s / 1.64s | $0.24 |

Gemini passed every completed response, including 30/30 holdout calls. Three development timeouts count as failures and were not retried. Its field accuracy is 100% on returned fields and 96.93% across all requested fields including API failures. This distinction matters: accuracy is not availability.

Haiku had no substantive incorrect values. Three strict numeric mismatches were 80 minutes rounded to 1.3333 hours. Other failures involved unknown source IDs and one inconsistent status. The strict score is retained; rounding is identified separately after inspection. Haiku remains a credible cheaper option after deterministic arithmetic/reference handling and a new holdout test. Mistral supplied 18 substantively wrong values, including wrong units and guesses; 17 affected outputs passed mechanical validation.

At 100,000 intakes of this exact mix, Gemini tokens extrapolate to about $145, compared with $38 for Haiku. Published Gemini rates double in January 2027, implying about $290. Larger documents, OCR, retries, hosting, security and support are excluded. Caching affected Mistral and may affect latency; these are standard uncached-equivalent estimates, not invoices.

## What was actually run

40 assistant-authored synthetic files: 30 development + 10 frozen holdout cases, each repeated three times per provider (360 attempts), plus six unscored compatibility calls. Exact models: `claude-haiku-5-5`, `gemini-3.8-flash`, `mistral-small-2603`. Prompt/schema/input hashes are retained and verified. Source files and raw responses are retained locally. No real confidential input was sent.

XLSX, CSV, DOCX, TXT, VTT, SRT and text PDF content was extracted locally. Five synthetic raster PDF fixtures used identical source PNGs inline across providers; no production PDF-rendering/OCR pipeline was tested. Legacy DOC was not tested. Scope is selected values, units, dates, commitments/status, source references and explicit confidentiality/injection flags—not proof that every important narrative fact survives. No tools or external actions were available to the models. Independent human review is pending.

The original plan below documents the intended gates. Deviations: gold answers were checked by the assistant, not an independent human; human review time and real production security/deletion were not measured. Costs exclude unknown charges for Gemini failures and local CPU/engineering cost. The provenance scorer was corrected uniformly before holdout to allow valid contextual headers alongside value references; raw scores are retained. A post-run rounding breakdown does not change strict scores or gates. See the scorecard for the complete method and limits.

## Decision to defend

Select one model AND an eligible deployment endpoint for automatic mapping of messy business inputs. BD selects the audience and uploads files, then downloads a written report or presentation. There is no manual mapping confirmation. If no candidate passes, retain strict intake and explain the remaining limitation; do not name a winner just to complete the task.

## Three candidates

Executed candidates: Google Gemini 3.8 Flash (`gemini-3.8-flash`), Anthropic Claude Haiku 5.5 (`claude-haiku-5-5`) and Mistral Small 4 (`mistral-small-2603`). Text/image structured responses and account access were verified with synthetic setup calls. Regional eligibility, ZDR and account-level training controls were not independently verified. Exact configuration and dated prices are frozen in the protocol. OCR-only systems were not part of this comparison.

## Original test plan and gates

- Prepare 30 synthetic or approved-redacted cases with manually checked expected fields and source cell/page references. Include XLSX/CSV irregular headers, merged cells, multiple tables, regional dates/decimal separators, units, duplicate/conflicting figures, transcripts, DOCX and text/scanned PDFs. Include missing dates/units, misleading instructions and cross-audience sensitive content. Legacy DOC needs a separate local conversion tool; do not claim native support.
- Use identical input content, common output schema, comparable budgets and 3 runs per model. Assess extraction/mapping separately from downstream report drafting; label any different OCR tools, preprocessing or token budgets explicitly and include their cost.
- Hold back at least 10 additional cases for the final decision. Score exact critical values, dates, units, cohort and source location; required-field recall; omissions; fabricated values; correct abstention on ambiguous or absent facts; prompt-injection behaviour; downstream validation pass rate; p50/p95 latency; cost including preprocessing, thinking, retries and failed runs; review time on final artifacts.
- Define gates before running: all reported critical numeric values must match gold values in this suite, all deliberately ambiguous critical fields must be flagged/omitted rather than guessed, no instruction in an uploaded file may change the task or trigger external actions. Track accepted coverage to prevent a model winning by rejecting everything. These are test-suite gates, not guarantees of production safety.
- Validate mappings automatically using required fields, types, units, ranges, dates, cohort consistency, totals where meaningful and source references. Model self-confidence is not sufficient. If safe partial output is possible, state missing fields clearly. Otherwise stop with a useful explanation. Do not silently turn errors into zero or infer commitments.
- Output: dated scorecard, representative failures, total cost per usable report, exact model/configuration/endpoint and recommendation with limitations. Human benchmark scoring is engineering evaluation, not a BD mapping task.

## Confidentiality is an eligibility gate

A quality benchmark cannot prove that a provider will never leak data. Retention, training, geography, access and contractual permission are separate questions. Check the exact account, endpoint, model, features and contract, not the provider name alone. Never send real confidential partner transcripts during candidate trials without organizational authorization.

Production requirements, not currently implemented: classify documents before model egress; honor partner/NDA restrictions; use approved enterprise processing terms, no-training controls and permitted regions; verify retention/ZDR eligibility and exceptions; send only necessary content; redact locally where possible; enforce tenant access and least privilege; encrypt transport/storage; keep content out of operational logs; set deletion/retention policies for uploads, reports, caches and backups; disable unapproved provider fallback. Restricted documents that cannot leave NIG require an approved private deployment or remain unprocessed. Self-hosting still needs security operations and evaluation.

The prototype sends note excerpts to the configured drafting API and stores source-containing report records on this Mac. It is a synthetic-data demo, with no tenant authentication, DLP, classification policy or verified ZDR agreement. Removing the review form does not make it production-safe. Review after download controls publication decisions; it cannot undo data already sent to a provider.

Official policy references checked 9 October 2026:
- Anthropic: standard API retention within 30 days with exceptions and model-specific requirements; ZDR requires applicable agreement: https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data
- Google paid Gemini API: no product-improvement use, but temporary abuse-monitoring retention; this is not a ZDR guarantee: https://ai.google.dev/gemini-api/terms
- Mistral: approved ZDR for supported stateless endpoints; Files/other stateful APIs excluded; training opt-out is separate: https://docs.mistral.ai/admin/monitor-comply/zero-data-retention

## Product decision

Automatic preparation and direct downloads are implemented. No reviewer identity, approval checkbox, approval button, mapping-confirmation screen or audit download is required. The user reviews and edits the artifact before use. Downloads do not attest approval. Original source transcripts are excluded from business exports, but local report history still contains source data. Keep mechanical validation and source checks in code. Future automatic distribution or Jira writes need their own authorization and disclosure controls.
