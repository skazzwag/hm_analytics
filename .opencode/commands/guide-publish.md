---
description: Prepare a Guide PR/CI deployment handoff; never publish locally
agent: product-owner
---
This compatibility command does NOT publish. Read the diff, validation evidence and known CI status for $ARGUMENTS. Explain that the existing main-branch CI owns publication/reconciliation. Report missing IDs or first-deploy inventory gates and request the normal reviewed PR/merge process. Do not push, merge, run workflows, call Guide mutations or execute guides-push/sync.sh. Never report a deployment without observed evidence.
