"""Dependency-free tests of notebook AST policies, not marimo execution."""
from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
CHECKER = ROOT / ".opencode/tools/notebooks/check.py"
ASSETS = ROOT / ".opencode/skills/marimo-build-notebook/assets"
spec = importlib.util.spec_from_file_location("notebook_check", CHECKER)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = '''import marimo
app = marimo.App()
@app.cell
def _():
    import marimo as mo
    import altair as alt
    return mo, alt
'''


@pytest.mark.parametrize("name", ["synthetic_demo.py", "approved_snapshot.py", "motherduck_readonly.py"])
def test_templates_pass_static_policy(name: str) -> None:
    assert module.check_file(ASSETS / name) == []


def test_syntax_error_is_reported() -> None:
    assert module.check_source("not valid python !")[0].startswith("SYNTAX:")


def test_plain_python_is_not_marimo() -> None:
    result = module.check_source("print('hello')")
    assert any(item.startswith("MARIMO:") for item in result)
    assert any(item.startswith("CELLS:") for item in result)


@pytest.mark.parametrize("library", ["matplotlib", "seaborn", "plotly", "bokeh", "holoviews", "hvplot"])
def test_other_plotting_libraries_rejected(library: str) -> None:
    assert any(item.startswith("PLOTTING:") for item in module.check_source(BASE + f"\nimport {library}\n"))


def test_from_import_plotting_rejected() -> None:
    assert any(item.startswith("PLOTTING:") for item in module.check_source(BASE + "\nfrom matplotlib import pyplot\n"))


def test_no_automatic_max_rows_disable() -> None:
    assert any(item.startswith("ROW_LIMIT:") for item in module.check_source(BASE + "\nalt.data_transformers.disable_max_rows()\n"))


@pytest.mark.parametrize("call", ["vf.enable()", "vf.runtime.set_connection('duckdb')"])
def test_legacy_connector_is_not_suggested(call: str) -> None:
    source = BASE + f"\nimport vegafusion as vf\n{call}\n"
    assert any(item.startswith("LEGACY_CONNECTOR:") for item in module.check_source(source))


def test_current_transformer_not_rejected() -> None:
    assert module.check_source(BASE + "\nalt.data_transformers.enable('vegafusion')\n") == []


def test_same_cell_widget_value_rejected() -> None:
    source = BASE + '''
@app.cell
def _(mo):
    control = mo.ui.slider(1, 5)
    answer = control.value
    return control, answer
'''
    assert any(item.startswith("UI_VALUE:") for item in module.check_source(source))


def test_same_cell_form_value_rejected() -> None:
    source = BASE + '''
@app.cell
def _(mo):
    control = mo.ui.dictionary({}).form()
    answer = control.value
    return control, answer
'''
    assert any(item.startswith("UI_VALUE:") for item in module.check_source(source))


def test_dependent_cell_widget_value_allowed() -> None:
    source = BASE + '''
@app.cell
def _(mo):
    control = mo.ui.slider(1, 5)
    control
    return (control,)
@app.cell
def _(control):
    answer = control.value
    return (answer,)
'''
    assert module.check_source(source) == []


def test_duplicate_exports_rejected() -> None:
    source = BASE + '''
@app.cell
def _():
    result = 1
    return (result,)
@app.cell
def _():
    result = 2
    return (result,)
'''
    assert any(item.startswith("EXPORT:") for item in module.check_source(source))


def test_cell_local_names_do_not_conflict() -> None:
    source = BASE + '''
@app.cell
def _():
    _chart = 1
    _chart
    return
@app.cell
def _():
    _chart = 2
    _chart
    return
'''
    assert module.check_source(source) == []


def test_missing_file_reported(tmp_path: Path) -> None:
    assert module.check_file(tmp_path / "missing.py")[0].startswith("READ:")


def test_non_python_notebook_rejected(tmp_path: Path) -> None:
    assert module.check_file(tmp_path / "notebook.ipynb")[0].startswith("FORMAT:")


def test_checker_never_executes_notebook(tmp_path: Path) -> None:
    marker = tmp_path / "not_executed.txt"
    notebook = tmp_path / "source.py"
    notebook.write_text(BASE + f"\nopen({str(marker)!r}, 'w').write('bad')\n")
    assert module.check_file(notebook) == []
    assert not marker.exists()


def test_cli_json_does_not_claim_runtime_verification() -> None:
    result = subprocess.run([sys.executable, str(CHECKER), str(ASSETS / "approved_snapshot.py")], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["status"] == "static-pass"
    assert data["executed_notebooks"] is False
    assert data["verified_warehouse_data"] is False


def test_cli_failure_exit_code(tmp_path: Path) -> None:
    notebook = tmp_path / "bad.py"
    notebook.write_text("import seaborn\n")
    result = subprocess.run([sys.executable, str(CHECKER), str(notebook)], check=False, capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "static-fail"


def test_live_template_gates_before_connecting() -> None:
    source = (ASSETS / "motherduck_readonly.py").read_text()
    tree = ast.parse(source)
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
    flag = [node for node in assignments if any(isinstance(target, ast.Name) and target.id == "runtime_scope_approved" for target in node.targets)]
    assert len(flag) == 1 and isinstance(flag[0].value, ast.Constant) and flag[0].value.value is False
    assert source.index("mo.stop(not runtime_scope_approved") < source.index("with duckdb.connect")
    assert source.index("mo.stop(query_controls.value is None") < source.index("with duckdb.connect")
    assert ".execute(query_sql, [_start, _end])" in source
    assert "__REPLACE_WITH_VERIFIED_RELATION__" in source


def test_snapshot_detects_overflow_not_silent_truncation() -> None:
    source = (ASSETS / "approved_snapshot.py").read_text()
    assert "nrows=5001" in source
    assert "len(snapshot_data) > 5000" in source
    assert "disable_max_rows" not in source


def test_synthetic_example_has_no_warehouse_connection() -> None:
    source = (ASSETS / "synthetic_demo.py").read_text()
    assert "synthetic" in source.lower()
    assert "duckdb.connect" not in source
    assert "motherduck_token" not in source
