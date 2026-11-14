# Data protection (UK GDPR)

This rule operationalises the UK GDPR and the Data Protection Act 2018 for this
platform. It is an engineering guardrail, not legal advice or a compliance
record: it reduces personal-data exposure in code, but it does not establish
lawful basis, controller/processor roles, DPIAs, or Article 30 records. Confirm
lawful basis and roles with the data owner before implementing any new feed of
personal data.

## Principles

- Personal data is any data relating to an identifiable living person: direct
  identifiers (name, email, phone, account ID, address) and indirect
  identifiers (order ID plus timestamp plus postcode can identify a person).
- Every stage is processing: ingestion, warehouse storage, transformation,
  analysis, notebooks, and reverse ETL outputs all fall under the same duties.
- Prompts to model APIs are disclosures to a processor. Never paste personal data
  into a prompt, a PR description, a commit message, or a Guide body.

## Minimisation and purpose limitation at ingestion

- Before adding a field or endpoint, state the downstream purpose. If no model
  or analysis needs it, do not ingest it. Do not ingest raw free-text fields
  (notes, messages, comments) unless a purpose is declared.
- Apply minimisation at the dlt contract level: exclude columns there, not
  only in downstream models, so unused personal data never lands in the
  warehouse.
- Do not commit sample payloads, dlt traces, or fixture files containing
  personal data. Test fixtures use synthetic data only.

## Pseudonymisation

- Hash or token direct identifiers in `1_staging` when analysis can use the
  pseudonymous form. Keep the mapping table out of the warehouse where possible.
- Pseudonymised data is still personal data: apply the same handling. Aggregation
  is the only route to non-personal data; tables with stable per-person keys are
  personal data regardless of label.

## Retention and deletion

- Every new personal-data table states a retention period and a deletion path:
  a Dagster job, a dbt full-refresh policy, or a documented manual step.
- Reverse ETL outputs are copies: retention applies at the destination too.
  State it in the change that creates the feed.
- Rights requests (access, erasure) must be executable: the platform needs to
  locate and delete a person's rows across ingestion, warehouse, and reverse ETL.
  Flag any feed that makes this impossible, such as no stable person-level ID or
  append-only state without replay.

## Exposure boundaries

- No personal data in notebooks under `analysis/`, exports, Guides, charts,
  logs, prompts, or test fixtures. Aggregate before visualising.
- Uploading local personal data to MotherDuck requires explicit approval (see
  `data-access.md`).
- Shared MotherDuck databases and published Guides are broadcast surfaces:
  check provenance before adding anything derived from personal data.

## New data flows (DPIA-lite)

For each new partner API feed or new personal-data category, run a short check
with the data architect and record it in the PR description:

1. What personal data, which fields, and roughly what volume.
2. Why it is needed (purpose) and the lawful basis, confirmed with the data
   owner.
3. Where it lands: source, staging, warehouse, reverse ETL destinations.
4. Who can see it at each stage; which identifiers are pseudonymised.
5. How long it is kept and how it is deleted.

## Review hooks

- `reviewer`: a new personal-data column without a stated purpose is a finding.
- `security-reviewer`: full security and data-protection checks for any change
  in its scope of engagement.
