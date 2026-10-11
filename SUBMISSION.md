# Submission verification

Prepared 10 October 2026; business-case documentation revised 11 October 2026. Repository: https://github.com/Cklintenberg/nig-mep-reporting

## Completed

- Candidate confirmed calculations, omitted information and uncertain delivery dates in the chosen demo output. This is candidate review, not independent review of every benchmark run.
- Created a new Python environment from `uv.lock` in the staged package, with no `.env` or author-side runtime configuration. CPython 3.13.16 on macOS arm64; Node 24.15.0; public npm dependencies installed from `package-lock.json`.
- Ran **72 tests: all passed, none skipped**, in 15.78 seconds. Provider calls are simulated in the tests. Portable PowerPoint rendering is exercised for real.
- Parsed the actual five demo files, checked 1,200 users / +20%, generated a figures-only HTML report and portable PowerPoint without any model request. Verified XML/ZIP integrity, editable chart workbooks and missing-value preservation. Included these synthetic outputs in `examples`.
- Existing author-side environment also passed 72 tests. The default on the author's Mac preserves its existing Artifact Tool renderer; fresh checkouts use public PptxGenJS. The original runtime is not redistributed.
- Source links in the packaged HTML speaker notes now point to GitHub instead of personal absolute filesystem paths.
- Inspected the selected files and archive contents. Excluded credentials, personal run history, local runtime configuration, environments, caches and working backups. Exact configured secrets and common credential patterns are checked without printing secret values.

## Limits and outstanding work

- This is a fresh dependency environment on the same Mac, **not** a Windows/Linux test or an independently verified external machine. PowerPoint file structure and content were checked; visual layout in the recipient's presentation software still needs acceptance. The two renderers may wrap text and draw charts differently.
- No new live provider calls were made for packaging. Provider access and model IDs may change. The reviewer supplies their own approved credentials; recorded synthetic evaluation remains dated evidence.
- Benchmark-wide independent human sign-off, production security approval, measured time savings and native-platform comparison remain open, as documented in the technical design.
- The recording is supplied separately. No video file is included in this package.
- The seven-hour estimate was given before packaging and portability work. This additional work has no updated candidate time estimate.

## Contents and exclusions

Included: prototype source, dependency lockfiles, tests, README for humans and agents, synthetic cases, recorded synthetic benchmarks, executive summary, technical design, demo guide, HTML presentation/canvas and example exports.

Excluded: `.env`, all credentials, `prototype/runs`, `.local`, `.venv`, `node_modules`, `runtime.local.json`, OS files, temporary backups, reference screenshots, private original assignment PDF and local browser state. Dependencies are installed through package managers.

The ZIP is made from committed repository files and includes no `.git` history. `MANIFEST.sha256` lists the shipped files' hashes (excluding itself). The ZIP and repository identify the same source snapshot; the recording is a separate deliverable.

## Final submission documents

The executive summary and technical design are included as PDFs and Markdown. The HTML presentation is `NIG - Final Presentation.html`; it includes a separate speaker-notes window. The reporting workflow canvas and model-evaluation evidence are included alongside it.

The PDFs were rendered and visually checked. Presentation numbering, internal links, JavaScript syntax and planned timings were checked. The final ZIP is verified against tracked files and `MANIFEST.sha256`. Application test results above remain dated verification, not a claim that documentation edits repeated live provider tests.
