---
description: Create or update a marimo analysis notebook using Altair, without implicit execution or dependency installation.
agent: data-analyst
---

Build or update the notebook for: $ARGUMENTS

Load `marimo-build-notebook`. For an explicitly approved live interactive session, also load `marimo-pair`; never start a server or execute cells without approval. Use the named analysis plan or the existing task context; do not invent a pipeline, table, metric, Guide ID or result. Keep all charts in Altair and all output under root ignored `analysis/`; do not stage or commit this workspace. No formal engineering review for these local drafts. Ask for missing material context only when it cannot be obtained from approved repository/catalog reads.

Validate source statically using the installed project tools. Do not start a server, execute remote queries, install dependencies or export data merely because the notebook was requested. Return file paths and precise validation/execution status.
