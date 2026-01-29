from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def _copy_agentctl(root: Path) -> None:
    tools_dir = root / "agents" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    src_root = Path(__file__).resolve().parents[1]
    shutil.copy2(src_root / "agents" / "tools" / "agentctl.py", tools_dir / "agentctl.py")
    shutil.copy2(src_root / "agents" / "__init__.py", root / "agents" / "__init__.py")
    shutil.copy2(src_root / "agents" / "tools" / "__init__.py", tools_dir / "__init__.py")
    shutil.copytree(src_root / "agents" / "tools" / "init", tools_dir / "init")
    shutil.copytree(
        src_root / "agents" / "tools" / "update_check",
        tools_dir / "update_check",
    )


def _write_overlay(root: Path, commands: list[list[str]], risk_paths: list[str]) -> None:
    overlay = {
        "repo_root": ".",
        "verify_commands": [{"cwd": ".", "command": cmd} for cmd in commands],
        "risk_paths": risk_paths,
    }
    overlay_path = root / ".agents" / "generated" / "AGENTS.repo.overlay.yaml"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.write_text(yaml.safe_dump(overlay, sort_keys=False))


def _write_minimal_profile(root: Path) -> None:
    profile = {"profile_schema_version": 1, "gate_pr": {"steps": ["verify"]}}
    profile_path = root / "agents" / "repo_profile.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False))


def _run_gate(root: Path, dry_run: bool = False) -> subprocess.CompletedProcess[str]:
    agentctl = root / "agents" / "tools" / "agentctl.py"
    src_path = Path(__file__).resolve().parents[1] / "src"
    env = dict(os.environ)
    if src_path.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
        )
    cmd = [sys.executable, str(agentctl), "gate", "pr"]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )


def _read_latest_report(root: Path) -> str:
    report = max((root / "reports" / "gates").glob("*.md"))
    return report.read_text()


def test_gate_pr_without_profile_runs_overlay_commands(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_agentctl(root)
    command = [sys.executable, "-c", "print('ok')"]
    _write_overlay(root, [command], ["infra/"])

    result = _run_gate(root)
    assert result.returncode == 0
    report = _read_latest_report(root)
    assert "infra/" in report
    assert " ".join(command) in report


def test_gate_pr_with_minimal_profile_runs(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_agentctl(root)
    command = [sys.executable, "-c", "print('ok')"]
    _write_overlay(root, [command], [])
    _write_minimal_profile(root)

    result = _run_gate(root)
    assert result.returncode == 0
    report = _read_latest_report(root)
    assert " ".join(command) in report


def test_gate_pr_dry_run_matches_run_plan(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _copy_agentctl(root)
    commands = [
        [sys.executable, "-c", "print('ok')"],
        [sys.executable, "-c", "print('more')"],
    ]
    _write_overlay(root, commands, ["infra/"])

    dry_run = _run_gate(root, dry_run=True)
    assert dry_run.returncode == 0
    output = dry_run.stdout
    for command in commands:
        assert " ".join(command) in output

    result = _run_gate(root)
    assert result.returncode == 0
    report = _read_latest_report(root)
    for command in commands:
        assert " ".join(command) in report
