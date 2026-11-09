# DuckDB, MotherDuck, Altair and marimo

Verified documentation: 2026-10-25. Inspect the project's installed versions and lockfile before depending on a particular API. See `sources.md` for primary sources.

## Default integration (no special Altair connector required)

```text
Agent:    MotherDuck MCP -> Guides/catalog -> approved exploratory SQL
Notebook: approved snapshot OR approved DuckDB/MotherDuck runtime
          -> filtered/aggregated, bounded data -> pandas/Arrow -> Altair -> marimo
```

Altair consumes tabular data. marimo renders Altair and provides `mo.ui.altair_chart` when frontend selections should become Python data. An explicit small materialized dataframe is the compatibility-first default. The runtime connection and notebook environment are separate from the assistant's MCP session.

For local `.duckdb` files, use a read-only local connection where appropriate. For MotherDuck, use DuckDB's `md:` connection with user-provisioned authentication and read-only warehouse privileges. Do not present a local `read_only` flag as a universal guarantee of cloud authorization. Check the provider's actual identity/token permissions.

Use parameter binding for values, for example `connection.execute(sql, [start, end]).fetchdf()`. Keep date semantics explicit, verify fully qualified relation names and materialize before closing the connection. Do not query all records then hope the plotting library will reduce them.

## Is there an official connector?

There is an officially documented ecosystem integration, but distinguish the versions:

- Older VegaFusion 1.x documentation demonstrates `vf.runtime.set_connection(duckdb_connection)` and `table://...` chart sources. Those examples are historical.
- VegaFusion 2.0 explicitly removed its DuckDB SQL connection and `vf.enable()`. It supports DuckDB relations as inline data with column pruning before Arrow conversion. This is not the old push-down connector.
- Current Altair documentation supports enabling the `vegafusion` transformer for pre-evaluated transformations. That alone does not mean chart transformations run remotely in MotherDuck.
- marimo documents DuckDB-compatible dataframe support and its own `marimo_csv` transformer for `mo.ui.altair_chart`. Do not assume that enabling VegaFusion globally preserves all widget selection/export behavior.

No VegaFusion dependency is enabled by default in this setup. Consider relation/Arrow or VegaFusion optimization only after an actual bottleneck is measured, the exact version pair is tested, the transformed data matches SQL totals, and query locations/data movement are understood. Never replace a simple bounded dataframe with untested legacy connector code to make a chart look nicer; visual styling is independent of this choice.

## Authentication and approved execution

marimo officially documents MotherDuck integration using DuckDB and SQL cells. Browser authentication or the `motherduck_token` environment variable belongs to the user. Do not ask the user to paste a token into chat, SQL, notebook source or a Guide. The library may consume a configured token without exposing it to the agent.

A user requesting a notebook authorizes creating the requested code, not any unrestricted warehouse query. Obtain separate approval before executing a direct runtime route when required by the project. A denied MCP action must stay denied. Keep manual gates, loopback binding and authentication; show no-data, stale-data and blocked states rather than claiming success.

## Dependency choice

The examples use `marimo`, `altair`, `duckdb` and `pandas`. `marimo[sql]` is useful when the SQL editor integration is desired. Arrow, Ibis and VegaFusion are optional. Reuse the repo's existing group/lockfile; dependency changes need owner approval. Do not install a second version through `uvx` just to run lint.
