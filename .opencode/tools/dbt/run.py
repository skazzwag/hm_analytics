#!/usr/bin/env python3
"""Opt-in dbt development runner. This is an accident guardrail, NOT a sandbox.

Database permissions and removal of all accessible production credentials are the
security boundary. See docs/setup-dbt-safety.md before enabling this runner.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
from typing import Any

COMMANDS = {"parse": ["parse"], "compile": ["compile"], "build": ["build"],
            "test": ["test"], "catalog": ["docs", "generate"]}
TOKEN_ENV = "MOTHERDUCK_AGENT_DEV_TOKEN"
TARGET = "agent_dev"
PROFILE = "fido_agent"
CONFIG_KEYS = {"enabled", "boundary_verified_by_user", "dbt_executable", "database",
               "attachments", "timeout_seconds"}
EXCLUDED = {"target", "logs", ".git", ".venv", "__pycache__", "guides"}
SOURCE_SUFFIXES = {".sql", ".py", ".yml", ".yaml", ".csv", ".json", ".toml", ".lock"}


class Blocked(ValueError):
    """The approved development execution conditions are not satisfied."""


def load_config(path: Path) -> dict[str, Any]:
    """Read non-secret policy; reject disabled, unknown or unsafe fields."""
    cfg = json.loads(path.read_text())
    if not isinstance(cfg, dict) or set(cfg) - CONFIG_KEYS:
        raise Blocked("Policy must be an object containing only documented fields.")
    if cfg.get("enabled") is not True or cfg.get("boundary_verified_by_user") is not True:
        raise Blocked("Development boundary is disabled or not verified by the user.")
    database = cfg.get("database", "")
    if not isinstance(database, str) or not re.fullmatch(r"agent_dev_[a-z0-9_]{1,48}", database):
        raise Blocked("Database must be an explicit agent_dev_* identifier, not a URL or prod name.")
    exe = Path(cfg.get("dbt_executable", ""))
    if not exe.is_absolute() or not exe.is_file() or not os.access(exe, os.X_OK):
        raise Blocked("dbt_executable must be a reviewed absolute executable path.")
    timeout = cfg.get("timeout_seconds", 600)
    if type(timeout) is not int or not 1 <= timeout <= 3600:
        raise Blocked("timeout_seconds must be an integer from 1 to 3600.")
    attachments = cfg.get("attachments", [])
    if not isinstance(attachments, list):
        raise Blocked("attachments must be a list of approved share references.")
    aliases: set[str] = set()
    for item in attachments:
        if not isinstance(item, dict) or set(item) != {"path", "alias"}:
            raise Blocked("Each attachment requires only path and alias.")
        if not isinstance(item["path"], str) or not re.fullmatch(
            r"md:_share/[A-Za-z0-9_-]+/[0-9a-fA-F-]{36}", item["path"]
        ):
            raise Blocked("Only explicit md:_share/name/UUID attachments are accepted.")
        if not isinstance(item["alias"], str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", item["alias"]):
            raise Blocked("Share alias must be a simple identifier.")
        if item["alias"] in aliases or item["alias"] == database:
            raise Blocked("Duplicate or destination-conflicting share alias.")
        aliases.add(item["alias"])
    return cfg


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse only supported commands; never pass arbitrary flags to dbt."""
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument("command", choices=sorted(COMMANDS))
    p.add_argument("--actor", choices=["implementer", "reviewer"], required=True)
    p.add_argument("--session", required=True)
    p.add_argument("--select", dest="selection")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", a.session):
        p.error("session must use lowercase letters/digits/underscores, starting with a letter")
    if a.command == "parse" and a.selection:
        p.error("parse is project-wide and does not take --select")
    if a.command != "parse" and not a.selection:
        p.error("an explicit --select is required, including for catalog")
    # Selectors can still be broad; approval must inspect their resolved scope.
    if a.selection and not re.fullmatch(r"[A-Za-z0-9_.,:+/ @*=-]{1,240}", a.selection):
        p.error("unsupported characters in selection")
    if a.selection and any(v.startswith("-") for v in a.selection.split()):
        p.error("selection cannot contain options")
    return a


def project_digest(project: Path) -> str:
    """Hash relevant source and packages, not generated target/logs or Guide prose."""
    digest = hashlib.sha256()
    for path in sorted(project.rglob("*")):
        rel = path.relative_to(project)
        if set(rel.parts) & EXCLUDED or path.suffix not in SOURCE_SUFFIXES:
            continue
        if path.is_symlink():
            raise Blocked("Symlinked source is unsupported; review provenance separately.")
        if not path.is_file() or path.name.startswith(".env") or "secret" in path.name.lower():
            continue
        digest.update(str(rel).encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def make_profile(cfg: dict[str, Any], actor: str, session: str) -> dict[str, Any]:
    """Construct one literal development target; no credentials enter profiles.yml."""
    output: dict[str, Any] = {
        "type": "duckdb", "path": f"md:{cfg['database']}",
        "schema": f"dbt_{actor}_{session}", "threads": 2,
    }
    if cfg.get("attachments"):
        output["attach"] = [dict(item, read_only=True) for item in cfg["attachments"]]
    return {PROFILE: {"target": TARGET, "outputs": {TARGET: output}}}


def clean_environment(cfg: dict[str, Any], home: Path, parent: dict[str, str]) -> dict[str, str]:
    """Do not inherit prod/cloud tokens, profiles paths, dotenv hooks or cached HOME."""
    token = parent.get(TOKEN_ENV, "").strip()
    if not token:
        raise Blocked(f"Required explicit development credential {TOKEN_ENV} is absent.")
    # No token contents or token-bearing URL are printed or written to profile/receipts.
    return {
        "PATH": str(Path(cfg["dbt_executable"]).parent) + ":/usr/bin:/bin",
        "HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
        "LANG": "C.UTF-8", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "motherduck_token": token,
        "DBT_ENV_SECRET_MOTHERDUCK_DEV_TOKEN": token,
        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false", "DBT_USE_COLORS": "false",
    }


def build_command(cfg: dict[str, Any], args: argparse.Namespace, project: Path, out: Path) -> list[str]:
    """Build argv with fixed target/profile/output; no shell evaluation."""
    cmd = [cfg["dbt_executable"], *COMMANDS[args.command],
           "--project-dir", str(project), "--profiles-dir", str(out / "profiles"),
           "--profile", PROFILE, "--target", TARGET,
           "--target-path", str(out / "target"), "--log-path", str(out / "logs")]
    if args.selection:
        cmd += ["--select", args.selection]
    return cmd


def execute(args: argparse.Namespace, cfg: dict[str, Any], root: Path,
            parent: dict[str, str]) -> int:
    """Run approved code, record evidence and invalidate checks if source changes."""
    project = root / "transformation"
    if not (project / "dbt_project.yml").is_file():
        raise Blocked("No transformation/dbt_project.yml; this overlay is not the dbt project.")
    expected = root / ".analysis" / "dbt" / args.actor / args.session
    # Prevent an obvious pre-existing symlink from redirecting generated output.
    if expected.resolve() != expected.absolute():
        raise Blocked("Runner output ancestors cannot be symlinks.")
    out = expected
    for relative in ["profiles", "profiles/profiles.yml", "home", "target", "logs", "session.json"]:
        generated = out / relative
        if generated.resolve() != generated.absolute():
            raise Blocked("Generated profile/home/artifact paths cannot be symlinks.")
    profile = make_profile(cfg, args.actor, args.session)
    before = project_digest(project)
    cmd = build_command(cfg, args, project, out)
    if args.dry_run:
        print(json.dumps({"status": "dry-run-only", "argv": cmd,
                          "profile_without_credentials": profile,
                          "source_digest": before,
                          "warning": "No authentication or permission check was performed."}, indent=2))
        return 0
    env = clean_environment(cfg, out / "home", parent)
    session_file = out / "session.json"
    record = {"source_digest": before, "database": cfg["database"],
              "schema": profile[PROFILE]["outputs"][TARGET]["schema"]}
    if session_file.exists() and json.loads(session_file.read_text()) != record:
        raise Blocked("Session source/destination changed; use a new session name.")
    os.umask(0o077)
    for folder in [out, out / "profiles", out / "home", out / "target", out / "logs"]:
        folder.mkdir(parents=True, exist_ok=True)
    session_file.write_text(json.dumps(record, indent=2) + "\n")
    (out / "profiles/profiles.yml").write_text(json.dumps(profile, indent=2) + "\n")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    status = "blocked"
    returncode = 2
    output = ""
    # No shell=True: arbitrary project macros/Python can STILL execute code.
    try:
        proc = subprocess.Popen(cmd, cwd=project, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, stderr = proc.communicate(timeout=cfg.get("timeout_seconds", 600))
        except subprocess.TimeoutExpired:
            # WSL/Linux process-group cleanup; deliberately detached children remain
            # outside this guardrail. A proper OS sandbox is still required.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = proc.communicate()
            output = "dbt process group timed out and was terminated.\n" + stdout + stderr
            status = "timeout"
        else:
            returncode = proc.returncode
            output = stdout + "\n" + stderr
            status = "passed" if returncode == 0 else "failed"
    except OSError:
        status, returncode = "execution-error", 2
        output = "Unable to start the approved dbt executable.\n"
    # Redact the literal dev token from captured output. Project logs may contain data;
    # all evidence stays private/ignored. This is not a general secret scanner.
    output = output.replace(env["motherduck_token"], "[REDACTED]")
    log = out / f"{timestamp}-{args.command}.output.txt"
    log.write_text(output)
    after = project_digest(project)
    if before != after:
        status, returncode = "source-changed-inconclusive", 2
    receipt = {"status": status, "exit_code": returncode, "command": args.command,
               "selection": args.selection, "actor": args.actor, "session": args.session,
               "target": TARGET, "database": cfg["database"], "schema": record["schema"],
               "source_digest_before": before, "source_digest_after": after,
               "output": str(log.relative_to(root)), "artifacts": str((out / "target").relative_to(root)),
               "production_verified": False}
    path = out / f"{timestamp}-{args.command}.receipt.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return returncode if 0 <= returncode <= 125 else 2


def main(argv: list[str] | None = None) -> int:
    """Exit 2 on absent/invalid policy without attempting database authentication."""
    args = parse_args(argv)
    try:
        config_path = os.environ.get("DBT_AGENT_CONFIG")
        if not config_path or not Path(config_path).is_absolute():
            raise Blocked("User must set DBT_AGENT_CONFIG to a reviewed absolute policy file.")
        cfg = load_config(Path(config_path))
        root = Path(__file__).resolve().parents[3]
        return execute(args, cfg, root, dict(os.environ))
    except (Blocked, OSError, json.JSONDecodeError) as exc:
        # Policy contains no secrets; do not print arbitrary configuration values.
        print(f"BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
