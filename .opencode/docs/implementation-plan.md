# Implemented overlay decisions
- Fully Git-ignored root analysis/ is data-analyst's personal workspace; transformation/ belongs to analytics-engineer.
- product-owner is a context-enabled custom primary agent; remove the previous plan.md override to restore stock Plan.
- Ingestion DQ uses core dlt contracts/fixtures/pytest with data-engineer; transformation DQ uses dbt Core tests with analytics-engineer. Optional licensed integrations are not prerequisites.
- Canonical Guide workflow follows the supplied README, not the previous provisional design. Actual scripts/metadata must still be inspected in the repository.
- Reviewer can request the opt-in development runner; direct dbt stays denied. Runner and flags are guardrails; server-side identity permissions and production credential removal are the boundary.
- Pipeline code, deployment code, live data, grants and native Altimate behavior were not changed or validated here.

- Investigations are lightweight: direct data-analyst routing, no routine engineering plan/review for ignored files. Tracked changes require the orchestrator's formal approval/verification path.
- Merge `/analysis/` into the repository-root `.gitignore`; no tracking, force-add or CI dependence on analyst scratch files.
