# Warehouse Guides
Source: supplied PR README preserved in .opencode/docs/reference/motherduck-guides-readme.md. Canonical tree is transformation/guides/, NOT documentation/warehouse-guides/.
Load motherduck-guides on demand. Analytics-engineer owns bodies/metadata; data-engineer owns deploy scripts when explicitly tasked; all agents can read relevant context, no agent publishes.
Follow root empty topic, database hyphenated/nested topics, share URL catalog references, organization access, stable committed UUIDs and CI Git-SHA external_id. Do not introduce private defaults or mandatory review/evidence sidecars. The actual metadata schema/scripts were not supplied.
Validate via existing make guides-validate. CI main publishes and reconciles managed topics; first-deploy inventory/UUID persistence remain operator gates. No local push/delete/sync. A Git merge does not prove the modeled prod behavior is deployed.
