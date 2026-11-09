# Context handoffs

## Specialist brief (aim under 400 words)

Goal and owner; approved scope; relevant paths; source and target environment; acceptance criteria; known constraints; relevant Guide UUID/version or local draft path; evidence pointers; blockers. Include only necessary excerpts. Do not send raw full catalogs, all Guides, entire manifests, transcripts or query results.

## Specialist receipt (aim under 300 words; expand only for material findings)

- Outcome and changed files.
- Decisions and evidence: code paths, SQL/artifact hashes, approved target, observed timestamp, Guide UUID/version.
- Checks actually executed and exact status: passed / findings / blocked / not run; paths to details.
- Durable context: draft paths and claims changed, or `no durable context change`; deployment state; Git draft / validated / CI status unverified / published observed / blocked.
- Required user actions and unresolved questions; returned task/session ID when available.

Persist technical outputs in ignored `.analysis/altimate/`. Keep reusable, non-sensitive evidence summaries in PR notes or ignored task evidence (not required per-Guide sidecars); do not commit row-level result dumps. Local scratch files, including Git-ignored `analysis/`, are not shared organization memory; include important findings in explicit handoffs. Do not stage or publish analyst notebooks as a substitute for Guide review.

Keep `product-owner` focused on coordination. Delegate one coherent work unit, not every small file or read. Reuse prior specialist sessions where supported, but repeat changed acceptance criteria. After compaction, re-open evidence and the relevant Guide rather than relying on an unsupported recollection.

Bind every receipt to the exact Git revision and working-tree source digest. After fixes, identify which checks applied to earlier source. Dev runtime, source review, production deployment and Guide CI publication are separate states. Never copy tokens or raw row dumps into receipts.
