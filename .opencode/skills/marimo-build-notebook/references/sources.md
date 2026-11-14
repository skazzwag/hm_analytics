# Primary-source notes

Checked 2026-10-25; documentation availability is not a live test of the user's environment.

| Source | What it supports |
|---|---|
| https://docs.marimo.io/api/plotting/ | Altair rendering, `mo.ui.altair_chart`, Python selections, transformer behavior |
| https://docs.marimo.io/guides/working_with_data/sql/ | SQL cells, result types, explicit connections and query controls |
| https://docs.marimo.io/integrations/motherduck/ | MotherDuck/DuckDB connection and user-managed authentication |
| https://docs.marimo.io/cli/ | `marimo check`, editor commands, host/headless/token options |
| https://docs.marimo.io/guides/lint_rules/ | Static notebook linting, not semantic verification |
| https://altair-viz.github.io/user_guide/data.html | Altair data inputs |
| https://altair-viz.github.io/user_guide/large_datasets.html | Row limits, transforms and data embedded in chart specs |
| https://vegafusion.io/posts/2024/2024-11-13_Release_2.0.0.html | Removal of DuckDB SQL connection and `vf.enable`; inline relation support |
| https://github.com/vega/vegafusion/releases/tag/v2.0.0 | Breaking changes for the VegaFusion 2 release |
| https://opencode.ai/docs/skills/ | On-demand skills and recognized skill locations |

Do not use https://vegafusion.io/duckdb.html as a current API recipe without accounting for the later 2.0 breaking changes. This is a documented version discrepancy, not an assertion that all current library combinations have been tested.

The project-specific 5,000-row chart budget, analyst ownership, approval gates and evidence contract are local policy choices, not vendor guarantees.
