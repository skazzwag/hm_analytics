---
name: opencode-review
description: 'OpenCode workflow: Independently review code, contracts and exact-revision evidence. Use after implementation or for targeted confirmation. No source edits; approved development verification is allowed.'
---

# Review protocol

> **Primary tool:** OpenCode agent and skill workflows (project coordination, no standalone execution engine).
Load reviewer instructions and matching rules. Inspect source status/diff and identify exact revision/digest. Challenge assumptions, tests, runtime scope and Guide accuracy. Inspect project code before executing it. Source read-only does not mean test/build has no side effects.
Request only permitted commands: dev dbt runner with actor reviewer and a separate session, approved local Altimate helpers, inspected fixture pytest or existing Guide validation. Missing dev isolation means runtime blocked. Never raw dbt, prod execution, notebook execution without its separate approval, Guide publishing or CI deployment.
Record actual commands/results and source identity; report Required fixes and Suggestions. Include coverage gaps and the distinction between inspected implementer evidence and independently executed checks. Return control to product-owner; stop after fixes unless a targeted recheck is separately approved. Do not claim the final revision passed from an earlier run.
