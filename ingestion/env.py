"""Environment variable helpers shared by ingestion components."""

from __future__ import annotations

import os


def require_env(name: str) -> str:
    """
    Return a required environment variable.

    Parameters
    ----------
    name : str
        Name of the environment variable.

    Returns
    -------
    str
        The variable value.

    Raises
    ------
    OSError
        If the variable is unset.
    """

    value = os.getenv(name)
    if value is None:
        raise OSError(f"Missing environment variable: {name}")
    return value
