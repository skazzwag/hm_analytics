# MotherDuck infrastructure

SQL in this tree is the source of truth for MotherDuck **databases, shares, and grants**.
Apply scripts deliberately from an approved session — there is no automated
apply workflow in this repo yet.
Do not create or delete these objects from ad-hoc MotherDuck sessions.

## Layout: directory is the service account

```
infrastructure/motherduck/
  prod/                 # prod service account → MOTHERDUCK_PROD_TOKEN
    horror_movies.sql
  ci/                   # CI service account → MOTHERDUCK_CI_TOKEN
    ci_horror_movies.sql
  hub/
    example/            # customer-facing hub database (optional)
```

- **Folder** = logical grouping of databases.
- **Filename** = database that the script manages.

Replace the example SQL with your organisation's databases, shares, and grants.
