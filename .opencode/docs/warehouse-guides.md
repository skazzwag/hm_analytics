# Guide workflow aligned to the supplied README
The exact supplied README is in reference/motherduck-guides-readme.md. It supersedes the previous generic Guide draft/publish implementation. This package does not overwrite your real transformation/guides files, Makefile or CI workflow.

## Canonical layout and versions
Use transformation/guides/warehouse-overview/ for the empty-topic root Guide; use transformation/guides/<database>/<slug>/ for domain Guides. Each Guide has guide.md and guide.metadata.json. A database may have multiple Guides. Topics use hyphens, catalog references use the README's md:_share/... URL. New domain Guides use access organization. Preserve IDs and existing metadata shape.
Git is source of truth. PR validates; main publishes through the MotherDuck CLI with external_id=$GITHUB_SHA. Warehouse UUID identifies a Guide; Git revision identifies the deployed source. Do not add a parallel version or approval file format.

## Ownership
Analytics-engineer updates canonical content during normal modeling/DQ work, or reports no Guide impact. Analyst writes candidates under Git-ignored root analysis/context-candidates/ and sends an explicit evidence handoff; files in that local directory are not themselves visible in PRs or CI. Reviewer checks factual/source/deployment consistency and can request the existing validator. Agents never call remote create/update/delete, make guides-push or sync.sh. guide-publish now only prepares the CI handoff.

## Operational gates still to inspect
1. Verify actual metadata files, Makefile, validate.sh, sync.sh and motherduck-guides.yaml against this README; they were not supplied here.
2. First publish writes UUIDs. Determine how the CI-produced metadata reaches a committed PR/commit before another publish; do not assume an ephemeral runner writes back to Git. Do not fabricate IDs.
3. Inventory existing org Guides on managed topics before first reconciliation. The README explicitly warns unmanaged-in-Git Guides on managed topics will be removed. Root and other topics are excluded; check exact/nested matching in the actual sync code.
4. Verify Guide CI cannot describe a model fix as live before the dbt production deployment. Stage Guide content or gate deployment as your actual workflows require.
5. Pin/review CLI behavior and confirm validation/deletion/reconciliation with a test identity before production deployment. No remote tests were performed here.

## Migration from earlier assistant package
Remove the obsolete provisional documentation/warehouse-guides tree and tools/guides checker ONLY if they are untouched generated examples. Review/diff any real content you added and move it manually into your canonical tree. Apply the supplied patch (which deletes obsolete files), or use the removal list; copying a ZIP over existing files alone does not remove them.
