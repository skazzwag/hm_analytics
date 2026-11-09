# Python style

Load this file when writing or reviewing Python (`ingestion/`, notebooks, tests, tools).

- Numpy docstrings with Parameters, Returns/Yields, and Raises.
- Always give type hints in function/class definitions and docstrings.
- Define typed dictionary classes instead of using ambiguous type hints like Any, dict, list, object and tuple. When list and dict have types for what they contain (e.g. list[str], dict[str, int]) they are not ambiguous.
- Prefer functions over classes.
- Always use pytest for any python code testing.
- Always use `uv` for package management and executing python from CLI.
- Do not use a leading underscore on function names.
- Avoid try/except unless the exception is specific and necessary. Prefer logic that does not need it.
- Avoid nested if-statements unless absolutely needed.
- Avoid isinstance checks unless they serve a genuinely useful purpose.
- Do not wrap a single expression in its own function; use the expression at the call site. This includes one-line f-string builders (for example a function that only returns `f"{prefix}_{type}_{id}_service_account"`), trivial accessors, and one-line tuple/dict key builders. A helper must earn its existence with multiple statements or genuinely reusable non-trivial logic.
- Prefer the provider's documented API (Azure, dlt, Dagster, and similar) over custom wrapper classes around it.

## marimo-generated wrappers

For `@app.cell` wrappers only, preserve marimo's generated `def _(...)` naming and generated signatures/returns without forcing helper-style type hints or docstrings. This narrow exception does not apply to ordinary Python functions. Read `notebooks.md` and the `marimo-build-notebook` skill for reactive-cell conventions.
