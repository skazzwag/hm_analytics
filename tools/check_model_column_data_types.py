"""Validate that documented dbt model columns declare a data type."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

import yaml


class ModelColumn(TypedDict, total=False):
    """Documented dbt model column metadata."""

    name: str
    data_type: str


def validate_model_column_data_types(properties_file: Path) -> list[str]:
    """Return missing data-type errors for dbt models in a YAML properties file.

    Parameters
    ----------
    properties_file
        Path to a dbt YAML properties file.

    Returns
    -------
    list[str]
        Errors for documented model columns that have no non-empty `data_type`.
    """
    parsed_document = yaml.safe_load(properties_file.read_text())
    if not isinstance(parsed_document, Mapping):
        return []

    documented_models = parsed_document.get("models")
    if not isinstance(documented_models, Sequence):
        return []

    errors: list[str] = []
    for documented_model in documented_models:
        if not isinstance(documented_model, Mapping):
            continue

        model_name = documented_model.get("name", "<unnamed model>")
        documented_columns = documented_model.get("columns", [])
        if not isinstance(documented_columns, Sequence):
            continue

        for documented_column in documented_columns:
            if not isinstance(documented_column, Mapping):
                continue

            column_name = documented_column.get("name", "<unnamed column>")
            data_type = documented_column.get("data_type")
            if not isinstance(data_type, str) or not data_type.strip():
                errors.append(
                    f"{properties_file}: model '{model_name}' column "
                    f"'{column_name}' is missing data_type"
                )

    return errors


def main(arguments: list[str] | None = None) -> int:
    """Validate data-type documentation in dbt model YAML files.

    Parameters
    ----------
    arguments
        File paths supplied by pre-commit. Uses command-line arguments when omitted.

    Returns
    -------
    int
        Zero when every documented model column has a data type; otherwise one.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("properties_files", nargs="+", type=Path)
    parsed_arguments = parser.parse_args(arguments)

    errors = [
        error
        for properties_file in parsed_arguments.properties_files
        for error in validate_model_column_data_types(properties_file)
    ]
    if errors:
        print("\n".join(errors))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
