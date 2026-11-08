import pathlib

import dagster

HERE = pathlib.Path(__file__).parent


@dagster.definitions
def definitions():
    """Return the Dagster definitions for the project."""

    return dagster.load_from_defs_folder(path_within_project=HERE)
