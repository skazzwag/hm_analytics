#!/usr/bin/env python3
"""Check a small set of notebook conventions without importing notebook code.

This is not a complete marimo linter, SQL validator, security sandbox or secret
scanner. It performs AST checks only. Use the installed ``marimo check`` and
separately approved runtime/visual tests for stronger verification.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Sequence

FORBIDDEN_PLOTTING = frozenset({"matplotlib", "seaborn", "plotly", "bokeh", "holoviews", "hvplot"})


def qualified_name(node: ast.AST) -> str:
    """Return a dotted expression name, or an empty string when not static."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = qualified_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def is_ui_call(node: ast.AST, marimo_aliases: set[str]) -> bool:
    """Identify direct marimo UI construction and chained form construction."""
    if not isinstance(node, ast.Call):
        return False
    name = qualified_name(node.func)
    if any(name.startswith(f"{alias}.ui.") for alias in marimo_aliases):
        return True
    if isinstance(node.func, ast.Attribute) and node.func.attr == "form":
        return is_ui_call(node.func.value, marimo_aliases)
    return False


def check_source(source: str) -> list[str]:
    """Return static policy findings without executing or importing source.

    Parameters
    ----------
    source : str
        UTF-8 Python notebook source already read by the caller.

    Returns
    -------
    list[str]
        Findings with stable codes. An empty list is only a static pass.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [f"SYNTAX: line {error.lineno}: {error.msg}"]

    findings: list[str] = []
    imported_roots: set[str] = set()
    marimo_aliases: set[str] = set()
    vegafusion_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                root = name.name.split(".")[0]
                imported_roots.add(root)
                if root == "marimo":
                    marimo_aliases.add(name.asname or root)
                if root == "vegafusion":
                    vegafusion_aliases.add(name.asname or root)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".")[0])

    if "marimo" not in imported_roots:
        findings.append("MARIMO: notebook must import marimo")
    for library in sorted(FORBIDDEN_PLOTTING & imported_roots):
        findings.append(f"PLOTTING: use Altair instead of {library}")

    cells = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(dec, ast.Attribute) and dec.attr == "cell"
            or isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "cell"
            for dec in node.decorator_list
        )
    ]
    if not cells:
        findings.append("CELLS: no @app.cell definitions found")

    exports: dict[str, int] = {}
    for cell in cells:
        created_widgets: set[str] = set()
        for node in ast.walk(cell):
            if isinstance(node, ast.Assign) and is_ui_call(node.value, marimo_aliases):
                created_widgets.update(target.id for target in node.targets if isinstance(target, ast.Name))
            elif isinstance(node, ast.AnnAssign) and node.value is not None and is_ui_call(node.value, marimo_aliases):
                if isinstance(node.target, ast.Name):
                    created_widgets.add(node.target.id)
        for node in ast.walk(cell):
            if isinstance(node, ast.Attribute) and node.attr == "value" and isinstance(node.value, ast.Name):
                if node.value.id in created_widgets:
                    findings.append(f"UI_VALUE: line {node.lineno}: read {node.value.id}.value in a dependent cell")
        for statement in cell.body:
            if not isinstance(statement, ast.Return) or statement.value is None:
                continue
            values = statement.value.elts if isinstance(statement.value, (ast.Tuple, ast.List)) else [statement.value]
            for value in values:
                if not isinstance(value, ast.Name) or value.id.startswith("_"):
                    continue
                previous = exports.get(value.id)
                if previous is not None and previous != cell.lineno:
                    findings.append(f"EXPORT: {value.id} returned by multiple cells (lines {previous}, {cell.lineno})")
                exports[value.id] = cell.lineno

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = qualified_name(node.func)
        if name.endswith(".disable_max_rows"):
            findings.append(f"ROW_LIMIT: line {node.lineno}: do not disable the row budget automatically")
        if any(name in {f"{alias}.enable", f"{alias}.runtime.set_connection"} for alias in vegafusion_aliases):
            findings.append(f"LEGACY_CONNECTOR: line {node.lineno}: VegaFusion 1.x connection/rendering API")

    # Keep repeated findings deterministic without hiding distinct line numbers.
    return list(dict.fromkeys(findings))


def check_file(path: Path) -> list[str]:
    """Read a Python notebook and return static findings, never execute it."""
    if path.suffix != ".py":
        return ["FORMAT: use a marimo .py notebook"]
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [f"READ: {error}"]
    return check_source(source)


def main(argv: Sequence[str] | None = None) -> int:
    """Check supplied files and print JSON with truthful static-only status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    results = [{"path": str(path), "findings": check_file(path)} for path in args.paths]
    passed = all(not result["findings"] for result in results)
    print(json.dumps({
        "status": "static-pass" if passed else "static-fail",
        "executed_notebooks": False,
        "verified_warehouse_data": False,
        "limitations": "AST policy subset only; run marimo check and separately approved runtime/visual tests.",
        "results": results,
    }, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
