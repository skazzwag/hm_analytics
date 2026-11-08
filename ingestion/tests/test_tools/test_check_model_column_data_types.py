from pathlib import Path

from tools.check_model_column_data_types import validate_model_column_data_types


def test_staging_yaml_declares_data_types() -> None:
    """Staging models should document column data types."""

    properties_file = Path("transformation/models/1_staging/stg_movie_catalogue.yml")
    assert validate_model_column_data_types(properties_file) == []
