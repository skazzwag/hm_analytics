---
name: dlt-setup-secrets
description: 'dlt CLI/Python: Safely manage dlt secrets in *.secrets.toml. Use when the user directly asks to set up, configure, or inspect credentials (API keys, database passwords, tokens). Also use when writing Python code that needs to read secrets via dlt.secrets without exposing values. Do NOT use for pipeline creation, source discovery, or debugging pipeline execution — those skills call dlt-setup-secrets when they need credentials configured.'
argument-hint: '[source-name]'
---

# Configure dlt secrets without exposing them to agents

> **Primary tool:** dlt CLI and Python library (dltHub-only features where explicitly noted).

Use this skill when a source or destination requires credentials. This project uses skills and CLIs, **not** a dlt MCP or dltHub AI secrets tools. Never read, enumerate, copy, echo or edit existing secrets (`.dlt/secrets.toml`, profile secrets, environment tokens, cloud credentials). A shell command that dumps variables or parses secrets is prohibited. Never add credentials to notebook code, SQL, Git or an agent brief.

1. Identify the *names and expected types* of the configuration fields from source code, exception text already supplied, and authoritative dlt/provider documentation. Do not inspect secret values or existing secret files.
2. Explain the least-privileged development identity and access scope required. Production service account credentials remain CI-only.
3. Show the user a **placeholder-only** TOML snippet or environment-variable names in the reply; the user places the actual values via their own secure editor or secret store. Do not create, merge or modify secrets files, even with placeholders, unless separately authorized through a reviewed non-secret mechanism.
4. Perform only approved **non-secret** checks such as `uv run dlt --version` or validated, isolated development runs. Do not infer a valid credential merely from file existence.
5. Request that the user confirm configuration is in place, without providing the credential values.

Use source-specific keys from the existing code rather than inventing their exact TOML path. See [credential-reference.md](cli-reference.md) for links and safe diagnostic boundaries.

Official dlt references: https://dlthub.com/docs/general-usage/credentials/setup and https://dlthub.com/docs/general-usage/credentials/advanced.
