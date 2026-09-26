# Comparing webpage rendering

Use the same Chromium version, viewport and page state for the archived reference and local environment. Suggested viewports are 1440×1000 and 1280×800.

1. Select the same data, filters, sort order, page number and expanded controls.
2. Load fonts and wait for the relevant content to finish rendering.
3. Capture the full page or an explicitly named content region on both sides.
4. Compare controls, text, layout, focus behavior and navigation separately.
5. Save screenshots alongside the source date, viewport and reproduction steps.

When comparing only a content region, label that region. Keep task-specific result screenshots in author-side evidence rather than runtime files. See each environment's data guide for field omissions, map sources and explicit local adaptations.

For arXiv, workflow scripts are documented in [tests/workflows/arxiv](../tests/workflows/arxiv/README.md); for Census, see [tests/workflows/census](../tests/workflows/census/README.md).
