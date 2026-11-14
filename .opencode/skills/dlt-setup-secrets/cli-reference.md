# CLI-first dlt secrets guidance

The core dlt CLI does not require a separate dlt MCP. Agent tooling must not inspect, print or modify `.dlt/secrets.toml`, cloud credentials or environment token values. The user configures credentials locally or in a secret store. Even tools advertising redacted output must not be used as a workaround for this project's secret-read policy.

Safe commands, subject to normal shell approvals:

```bash
uv run dlt --version
uv run dlt pipeline --list-pipelines
```

These commands do not establish that credentials are present or authorized. Commands that connect to destinations or launch pipelines need separately approved development credentials and scope. Do not use production secrets simply to verify connectivity.

Credentials documentation: https://dlthub.com/docs/general-usage/credentials/setup and https://dlthub.com/docs/general-usage/credentials/advanced.
