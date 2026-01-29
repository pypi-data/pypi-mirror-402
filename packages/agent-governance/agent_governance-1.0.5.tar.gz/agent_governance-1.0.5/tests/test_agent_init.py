from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AGENTCTL = ROOT / "agents" / "tools" / "agentctl.py"
FIXTURES = ROOT / "tests" / "fixtures"


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    dest = tmp_path / name
    shutil.copytree(FIXTURES / name, dest)
    return dest


def _run_init(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(AGENTCTL), "init", *args]
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = "1700000000"
    return subprocess.run(
        cmd,
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_deterministic_output(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    first = _run_init(repo)
    second = _run_init(repo)
    assert first.returncode == 0
    assert second.returncode == 0
    assert first.stdout == second.stdout


def test_verify_command_selection(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    result = _run_init(repo)
    assert "poetry run pytest -q" in result.stdout

    repo = _copy_fixture(tmp_path, "python_pyproject_uv_repo")
    result = _run_init(repo)
    assert "uv run pytest -q" in result.stdout

    repo = _copy_fixture(tmp_path, "node_pnpm_repo")
    result = _run_init(repo)
    assert "pnpm -s test" in result.stdout
    assert "pnpm -s lint" in result.stdout
    assert "pnpm -s typecheck" in result.stdout

    repo = _copy_fixture(tmp_path, "rust_repo")
    result = _run_init(repo)
    assert "cargo test" in result.stdout


def test_risk_path_detection(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "monorepo_mixed")
    result = _run_init(repo)
    assert "schemas/" in result.stdout


def test_report_contains_citations(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    result = _run_init(repo, "--write")
    assert result.returncode == 0
    report_path = repo / ".agents" / "generated" / "init_report.md"
    facts_path = repo / ".agents" / "generated" / "init_facts.json"
    report = report_path.read_text()
    facts_payload = json.loads(facts_path.read_text())
    facts = facts_payload["facts"]
    assert "## Evidence" in report
    for fact in facts:
        source = fact["source"]
        location = f"{source['path']}:{source['line_start']}-{source['line_end']}"
        assert location in report


def test_write_false_does_not_write(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    result = _run_init(repo)
    assert result.returncode == 0
    assert not (repo / ".agents").exists()
    assert not (repo / ".gitignore").exists()
    assert "AGENTS.md not found" in result.stdout


def test_write_true_creates_outputs(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "github_actions_repo")
    result = _run_init(repo, "--write")
    assert result.returncode == 0
    out_dir = repo / ".agents" / "generated"
    overlay_path = out_dir / "AGENTS.repo.overlay.yaml"
    report_path = out_dir / "init_report.md"
    facts_path = out_dir / "init_facts.json"
    assert overlay_path.exists()
    assert report_path.exists()
    assert facts_path.exists()
    overlay = yaml.safe_load(overlay_path.read_text())
    assert "verify_commands" in overlay
    facts_payload = json.loads(facts_path.read_text())
    assert facts_payload["init_tool_version"]
    assert _is_iso8601(facts_payload["generated_at_utc"])
    facts = facts_payload["facts"]
    assert facts
    assert "source" in facts[0]


def test_gitignore_only_modified_when_present(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    gitignore = repo / ".gitignore"
    gitignore.write_text("node_modules/\n")
    result = _run_init(repo, "--write")
    assert result.returncode == 0
    content = gitignore.read_text().splitlines()
    assert ".agents/generated/" in content
    assert content.count(".agents/generated/") == 1


def test_missing_gitignore_not_created(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    result = _run_init(repo, "--write")
    assert result.returncode == 0
    assert not (repo / ".gitignore").exists()


def test_agents_md_present_ok(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    agents_md = repo / "AGENTS.md"
    agents_md.write_text(
        "# Agent Governance Contract\n\npolicy_schema_version: 1\n\n## agent init behavior\n\n- ok\n"
    )
    result = _run_init(repo)
    assert result.returncode == 0
    assert "status: ok" in result.stdout


def test_golden_report_and_overlay(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo")
    result = _run_init(repo)
    assert result.returncode == 0
    expected_report = (repo / "expected_init_report.md").read_text()
    assert result.stdout == expected_report
    result = _run_init(repo, "--write")
    assert result.returncode == 0
    overlay_path = repo / ".agents" / "generated" / "AGENTS.repo.overlay.yaml"
    expected_overlay = yaml.safe_load((repo / "expected_overlay.yaml").read_text())
    overlay = yaml.safe_load(overlay_path.read_text())
    assert overlay["init_tool_version"] == expected_overlay["init_tool_version"]
    assert _is_iso8601(overlay["generated_at_utc"])
    overlay.pop("generated_at_utc", None)
    expected_overlay.pop("generated_at_utc", None)
    assert overlay == expected_overlay


def test_non_utf8_files_ignored(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "python_poetry_repo_with_binary")
    result = _run_init(repo)
    assert result.returncode == 0
    expected_report = (repo / "expected_init_report.md").read_text()
    assert result.stdout == expected_report


def _is_iso8601(value: str) -> bool:
    return bool(
        re.match(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+00:00$",
            value,
        )
    )
