# MotherDuck Guides

Guides are markdown documents stored in MotherDuck. Agents read them before
writing SQL. This directory is the git source of truth; CI publishes to the
warehouse with the MotherDuck CLI.

A **database can have many Guides**. Put each one in its own folder:

```text
transformation/guides/
  warehouse-overview/              # root Guide (no topic) — which database to use
  prod_analytics/
    overview/
    waypoints/
    sessions-and-predictions/
  prod_operations/
    overview/
    access/
    odls/
    platform-usage/
    fido-plus-reports/
  prod_edge/
    overview/
    relays-and-sensors/
  prod_revenue/overview/
  prod_correlation/overview/
  prod_engineering/overview/
  hub_fido/overview/
  hub_thames/overview/
```

Each Guide folder contains:

- `guide.md` — the body agents read
- `guide.metadata.json` — title, topic, organisation access, catalog references, and (after first publish) the warehouse UUID

## Topics and references

- The warehouse overview is a root Guide (`topic` is empty) so it appears in every `get_query_guide` listing.
- Other Guides use a topic of `<database-with-hyphens>` or a nested topic such as `prod-operations/reports`.
- Catalog `references` must use the **share URL** (`md:_share/...`), not the `prod_*` alias. Analysts and agents attach these databases as shares; `list_tables` only surfaces a Guide when the URL matches.

Current share URLs (from the org catalog):

| Database | Share URL |
| --- | --- |
| prod_analytics | `md:_share/prod_analytics/b57bb6cc-f153-49c4-92c6-36f40631858b` |
| prod_operations | `md:_share/prod_operations/0d5d6529-30b9-4de1-88ab-245a57fe518d` |
| prod_edge | `md:_share/prod_edge/f66ac8bb-bcde-4296-a7fb-6c5457eb6adc` |
| prod_revenue | `md:_share/prod_revenue/a520297c-05b8-4c65-92f4-3e22a38211a1` |
| prod_correlation | `md:_share/prod_correlation/6fc7d523-8ae1-4247-ac00-0b40f863dab1` |
| prod_engineering | `md:_share/prod_engineering/29deedb7-e6df-4fa1-bcdc-26ca0297e23e` |
| hub_fido | `md:_share/hub_fido/fcf49b5b-8a5b-4270-a33a-5169c9056b4a` |
| hub_thames | `md:_share/hub_thames/3ca754c3-5d07-49e7-aa1d-3ea2e47c63f4` |

## Local workflow

```bash
# Install the MotherDuck CLI once
curl -s https://install.motherduck.com | SKIP_DUCKDB_CLI=1 sh

make guides-validate

# Optional pre-flight before a deploy that must not create new Guides:
# fails when any guide.metadata.json is missing its warehouse UUID.
transformation/guides/validate.sh --require-id

# Publish (requires MOTHERDUCK_TOKEN with org-Guide permission, typically the prod service account)
export MOTHERDUCK_TOKEN=...
make guides-push
```

After the first successful push, `guide.metadata.json` files gain an `id`.
Commit those IDs immediately. The next push updates the existing Guide;
without the id, the CLI would create a duplicate.

Do not `motherduck guide push` from a laptop against organisation Guides
once CI owns them — edit markdown here and merge.

## CI

`.github/workflows/motherduck-guides.yaml`:

- **Pull request:** validate Guide folders (no publish).
- **Push to `main`:** validate, then `motherduck guide push` with
  `MOTHERDUCK_PROD_TOKEN` and `external_id=$GITHUB_SHA`, then remove any
  published Guide that is no longer in this repository (`sync.sh`).

The prod service account must be allowed to set Guide access to
`organization` (MotherDuck admin / builder permission for org Guides).

## Removing a Guide

Git is the source of truth. Delete the Guide folder in a PR; once the change
deploys from `main`, CI removes the published Guide from MotherDuck
(`motherduck guide delete` — a soft delete, version history is preserved).

Reconciliation is scoped and fail-safe:

- Only Guides on managed topics (`prod-analytics`, `prod-operations`,
  `prod-edge`, `prod-revenue`, `prod-correlation`, `prod-engineering`,
  `hub-fido`, `hub-thames`) are ever auto-deleted.
- Root-topic Guides and Guides on other topics are never deleted; stray
  root Guides are listed in the deploy log for manual review.
- If the committed UUIDs and the remote listing do not reconcile, nothing
  is deleted and the deploy fails loudly.

Before the first deploy that runs `sync.sh`, any published organisation
Guide on a managed topic that is not in this repository will be removed.
Port manually-pushed Guides into git (or move them to an unmanaged topic)
first.

## Adding a Guide

1. Create `transformation/guides/<database>/<guide-slug>/`.
2. Add `guide.md` (rules and working SQL, not a file inventory).
3. Add `guide.metadata.json` with `access: organization`, a topic under
   that database, and at least one catalog reference to the share URL.
4. Run `make guides-validate`.
5. Merge. The first production deploy writes the UUID; commit it.
