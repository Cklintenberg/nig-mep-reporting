# PowerPoint export

The distributable renderer is `build-portable.mjs`, using public **PptxGenJS 4.0.1** (MIT). It creates editable text, tables, native charts and embedded chart workbooks from the checked report snapshot. No extra model request or network access is needed during rendering. Full transcripts and exact source quotations are omitted from the business deck; sensitive summaries still require review.

## Fresh checkout

Install Node.js 20+ with npm, then from `prototype`:

```sh
npm ci --prefix presentation --ignore-scripts
```

The app discovers `node` on PATH. Set `MEP_EXPORT_NODE` to an absolute Node executable path only if required. `MEP_EXPORT_RENDERER=portable` explicitly selects the portable renderer. Fonts use Arial, with local viewer substitution if unavailable.

## Existing rehearsal setup

`auto` is the default. An existing `runtime.local.json` with a valid Artifact Tool module preserves the original local `build.mjs` renderer. That local configuration and the bundled Artifact Tool dependency are **excluded** from the submission. A fresh checkout automatically selects PptxGenJS. `MEP_EXPORT_RENDERER=artifact` is only for separately provisioned compatible installations; it is not required for reviewers. These are two templates of the same checked report content, so line wrapping and chart styling may differ.

The Python boundary validates source quotations and error flags, uses a 120-second subprocess timeout, strips API credentials from the renderer subprocess, checks PPTX ZIP integrity and caches by report/template/dependency version. Rendering failures preserve the report and its written HTML download. No publishing or recorded human approval occurs.

See `tests/test_flexible_exports.py` for an actual portable-export integration check. After installing npm dependencies, it verifies editable charts/workbooks, findings and missing-value warnings. Large/long-field layouts and different PowerPoint viewers still need visual acceptance testing. The new renderer's export validation is structural; it does not claim cross-platform visual identity with the original renderer.

Library documentation: https://gitbrent.github.io/PptxGenJS/ and https://github.com/gitbrent/PptxGenJS . Dependency license text is installed with the package, not bundled third-party runtime binaries.
