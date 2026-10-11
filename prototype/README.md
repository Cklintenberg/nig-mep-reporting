# MEP weekly reporting prototype

A local prototype for the fictional NIG Analytics and Strategy case. It turns platform figures in CSV/Excel and ordinary meeting transcripts, documents or pasted notes into a weekly BD–engineering report, with review of the downloaded report before use.

## Start here

Open this **prototype** folder in VS Code. For an existing installed Python environment, run:

```sh
.venv/bin/python -m streamlit run app.py --server.headless true
```

Open http://127.0.0.1:8501. The **Overview** shows the fictional portfolio. In **Weekly report**, select the report type and week, upload a spreadsheet, meeting documents, or both, and click **Create report draft**. Haiku 5.5 drafts automatically; no AI toggle or model selection is shown to BD users. Download a written HTML report or an editable PowerPoint directly. Review and edit the downloaded file before use. No message is sent. Credentials must be configured locally.

For a fresh checkout with Python 3.12/3.13, uv and Node.js 20+ with npm installed:

```sh
uv sync --locked
npm ci --prefix presentation --ignore-scripts
cp .env.example .env
# Add your own approved Anthropic API key to .env for meeting-note drafting.
uv run streamlit run app.py --server.headless true
```

Do not run the copy command over a populated `.env`. PowerPoint export uses the public, pinned PptxGenJS dependency installed by `npm ci`. A fresh checkout needs no Codex-specific runtime. See [renderer setup](presentation/README.md). Clean-environment verification is documented in the submission README; no cross-OS execution is claimed.

## Enable AI

Enter credentials locally in `.env`. The default report provider is Anthropic. Other provider adapters can be configured separately for evaluation:

```dotenv
OPENAI_API_KEY=your-local-key
ANTHROPIC_API_KEY=your-local-key
MEP_OPENAI_MODEL=gpt-6-luna
MEP_ANTHROPIC_MODEL=claude-haiku-5-5
ANTHROPIC_WORKSPACE_ID=your-workspace-id-if-required
```

Do not paste credentials into chat, source code, screenshots or submission files. `.env` is excluded by `.gitignore`. The app only displays whether a key is configured. Nonblank local values take precedence over environment variables; blank local values allow shell variables to be used. Settings are read on each rerun, so refresh after adding a key.

Anthropic keys that are not scoped to a workspace also require `ANTHROPIC_WORKSPACE_ID`. This prototype is configured locally for the existing Default workspace; the example file leaves the value blank. Workspace-scoped keys can leave it blank. See [Anthropic authentication](https://platform.claude.com/docs/en/manage-claude/authentication).

Weekly report uses `MEP_REPORT_PROVIDER` (default `Anthropic`) and `MEP_REPORT_MODEL` (default `claude-haiku-5-5` for Anthropic). These are operator settings in `.env`, separate from comparison model defaults. A provider change requires checking data permissions and terms. Missing credentials disable generation when meeting material needs AI; metrics-only reports need no key; a service error never falls back to a non-AI report. Provider/model selectors and the non-AI baseline remain in **Model comparison**. Every saved report retains the actual provider and model in its run details.

Changing between two models at one provider usually uses the same provider key. Switching providers selects a different local key and API adapter. Only source notes are sent to the provider. CSV arithmetic, validation, review and export run locally. A ChatGPT or Claude chat subscription is not an API credential.

## Reopen reports

New drafts autosave under `runs/drafts/`. Open **Report library**, select a report and choose **Open saved report** to download it without another model call. Changed input files do not silently replace an existing report. Historical approved exports may still appear, but the current UI does not request approval or provide inline editing. Review/edit the downloaded artifact.

Local records include extracted source text. There is no multiuser access control, managed retention, backup or concurrent-edit protection. Business exports omit full transcripts, but downloaded summaries may still contain sensitive information. Nothing is sent automatically.

## Compare models

In **Model comparison**, **Load Haiku / Gemini / Mistral evaluation — no API calls** opens the current recorded drafting comparison: six synthetic engineering cases, twice per model. Earlier OpenAI/Anthropic results remain separately available as historical evidence. Independent human review remains pending. New comparisons can use explicit provider/model choices and the non-AI baseline; these controls are not shown in Weekly report. See [the current technical design](docs/technical-design.md#5-ai-configuration-and-evaluation) for results, observed failures and limitations.

The CLI also supports comparisons:

```sh
uv run python benchmark.py
uv run python benchmark.py --provider OpenAI --models gpt-6-luna gpt-6.1-sol
uv run python benchmark.py --provider Anthropic --models claude-haiku-5-5 claude-sonnet-5-5
```

A full two-model comparison makes 10 model calls across five synthetic cases. API costs are separate from chat subscriptions. Results and local report history are saved under `runs/`, which is excluded from version control. Failures remain in the comparison denominator. Exact matching quotes do not establish factual correctness of the summary.

Automatic model recommendation is a future design concept only. See **Design & scope** and `docs/technical-design.md` for the proposed evaluation criteria and routing approach. No new candidate benchmark is claimed by adding it to the dropdown.

## Code map

| File | Responsibility |
| --- | --- |
| `app.py` | Navigation, uploads, automatic drafting, downloads and model-comparison controls |
| `dashboard.py` and `ui.css` | Business overview, portfolio trends and shared visual styling |
| `ingestion.py` | Extracts text from office files, preserves source traceability and normalises spreadsheet inputs |
| `schemas.py` | Shared contracts for source notes, findings and evidence |
| `metrics.py` | Numeric validation and deterministic changes |
| `ai.py` | OpenAI, Anthropic, Gemini and Mistral adapters, operator configuration and usage estimates |
| `prompts/report.txt` | Explicit drafting instructions and uncertainty rules |
| `workflow.py` | Coordinates inputs, draft generation and evidence checks |
| `report_store.py` | Local draft autosave and reopening draft/approved history |
| `exports.py` | Export checks, content hash and HTML escaping; retained legacy approval helpers |
| `benchmark.py` | Repeatable paired runs and failure accounting |
| `sample_data/` | Fictional normal and adversarial examples |
| `evaluation/criteria.json` | Human review criteria, kept outside model input |
| `tests/` | Data failures, source checks, provider dispatch, saved history and download behaviour |

## Sidebar expansion previews

Every sidebar item opens a page. Search workspace, Applications, Customers, Partners, Meetings, Insights & forecasts, Integrations and Settings are interactive mock pages, clearly labelled as previews. `sample_data/workspace_preview.json` contains 48 fictional application records, 312 fictional customer accounts and six meeting examples. Partner assignments and totals match the overview snapshot. Filters, record details, search and a simple growth-assumption chart work locally. Integration setup is explanatory only; settings save demo preferences to the current session without changing real configuration.

Overview, Weekly report, Report library, Model comparison and Design & scope retain their working behaviour. Mock pages neither feed the reporting workflow nor make API calls. The portfolio data remains a fixed illustrative snapshot even after uploading reports. `preview_pages.py` owns the preview views; the sidebar marks them Mock.

## Portfolio overview

The overview reads fictional weekly snapshots and partner accounts from `sample_data/portfolio.json`. Applications and business customers are distinct portfolio counts; weekly active users count people within the matched application cohort. The latest two weeks of usage, availability and analytics delay match the normal reporting sample. App listings can overlap across partners and must not be summed. Customers are attributed to a primary partner in this fixture.

The trend selector changes the chart history; headline changes always compare the latest two weeks. Search and region filters apply to the partner table. Uploaded report inputs do not update the portfolio. This view gives BD context and an entry point into report preparation; it does not add live analytics ingestion to the implemented workflow.

## Upload ordinary meeting material

In **Weekly report**, choose the report week, add one platform CSV or Excel workbook together with transcript/Word files in the single Report files upload area, or paste additional notes below. Files are classified by extension. A spreadsheet, meeting material, or both are accepted; multiple spreadsheets or an invalid supplied spreadsheet block generation. No JSON preparation is required. Open `sample_data/Demo files/` for ready-to-upload sets, including the existing workbook and office files. The reporting page is upload-only; scenario fixtures remain available to automated tests and Model comparison. These are fictional examples, not certified exports from any meeting platform.

| Material | Supported input |
| --- | --- |
| Meeting transcript | `.txt`, `.vtt`, `.srt` or a text-based `.docx` |
| Word notes | `.docx` body paragraphs and tables |
| Google Docs | Export as `.docx`/`.txt`, or copy and paste |
| Apple Notes, emails, personal notes | Copy and paste the text |
| Platform figures | `.csv` or `.xlsx`; detect the unique matching worksheet by first-row column headings |

Dates and participants stated in the text are preserved. A missing calendar meeting date remains unknown and triggers a review warning; transcript timecodes are not calendar dates. Files are parsed locally, without an AI request. The drafting call receives the extracted source text. File names, original file hashes, chunk offsets, worksheet name and spreadsheet row mapping are retained in the JSON audit record. Raw uploaded binary files are not persisted by the app. Review the downloaded output against its source files before using or sharing it; the current UI has no approval form.

Images, scans, audio, OCR, legacy `.doc`/`.xls`, document comments, headers/footers, text boxes and live service integrations are outside this parser's scope. Word support covers body paragraphs and tables; embedded images are not read. Image-only documents are rejected. Text must be UTF-8 or BOM-marked UTF-16. Up to 12 uploaded note files plus pasted notes are accepted; each file is limited to 10 MB and the combined extracted text to 40,000 characters. Long notes are split into contiguous excerpts of at most 5,800 characters with provenance offsets, not silently summarised or truncated.

## Spreadsheet contract

The first row must contain **Week start, Cohort, Metric, Value, Unit**. Snake-case headers also work. Extra columns are explicitly listed as ignored. Use one row per metric and week, at most 500 data rows and 50 Excel columns. Dates are the report Monday and preceding Monday. Supply already-aggregated values for one consistently defined application cohort; the app cannot detect a real-world cohort definition change hidden behind the same label. Arbitrary dashboard layouts and pivot tables are not interpreted.

Supported metrics are `weekly_active_users` (users), `availability` (%), `analytics_freshness` (hours), and `api_error_rate` (%). Omit unavailable rows; never replace unknown values with zero. Formula cells in required columns are rejected: export calculated values first. Excel percentage-formatted numeric cells are converted from their stored fraction to the 0–100 percentage scale, and conversions are retained in the intake provenance in the JSON audit record. A plain numeric cell with unit `%` is already interpreted on that scale. Dates stored as Excel date cells are converted to ISO calendar dates.

Define weekly availability as the percentage of scheduled observation time available, API error rate as failed requests / total requests, and analytics freshness as the supplied weekly summary of data age. The fixture assumes consistent measurement rules; production requires an agreed metric dictionary and timezone. The canonical CSV and structured source JSON are internal contracts. The original curated JSON fixtures remain for reproducible evaluation; users do not need to author them.

## Verify

```sh
uv run pytest -q
```

The pre-handover check on 10 October 2026 passed 70 tests. Packaging adds portable-renderer checks; see the submission verification record for the latest result. Tests simulate provider calls; actual model responses are in the recorded benchmark evidence. Review the generated artifact yourself before presenting it. Mechanical checks do not establish factual completeness or confidential-data safety. Current submission documents: [technical design](docs/technical-design.md), [executive summary](docs/executive-summary.md), [demo guide](docs/demo-guide.md). `evaluation/status.md` is a historical development log, not the current UX specification.

## Meeting briefs and visual identity

Weekly report offers Engineering, Vendor and Partner audiences, all using the same internal BD preparation workflow. Audience is retained in saved reports and export titles and changes the AI instructions. Baseline excerpts are not filtered by audience. These are internal preparation briefs, not externally cleared reports. Local history contains source evidence; business downloads omit full transcripts. The original engineering comparison remains historical evidence, because the current audience prompt adds new instructions.

Meetings now shows an interactive week/month calendar over the six fictional records. Event buttons reveal the existing notes; navigation changes the displayed period. No real calendar is connected.

The NIG mark in `assets/nig.svg` is an original concept identity for this fictional case. Product logo SVGs are stored locally: Teams, OneDrive, Google and Zoom from Iconify's Logos collection (`https://api.iconify.design/logos:microsoft-teams.svg`, `logos:microsoft-onedrive.svg`, `logos:google-workspace.svg`, `logos:zoom.svg`); SharePoint from Microsoft's product asset CDN (`https://res.cdn.office.net/files/fabric-cdn-prod_20230815.002/assets/brand-icons/product/svg/sharepoint_48x1.svg`). Generic analytics and email symbols are original SVGs. Brand marks identify the proposed integrations; they do not indicate live connections.

PDF ingestion uses pypdf locally, preserves page markers in extracted text, and supports up to 50 text-bearing pages and 40,000 combined note characters. Encrypted, malformed, empty-page or image-only PDFs are rejected explicitly; no OCR or visual/table interpretation is performed. A PDF supplements meeting notes; the numerical metric table still requires a CSV/XLSX file. The upload limit is 10 MB (10 × 1024² bytes); file size and extracted-text limits are separate.
