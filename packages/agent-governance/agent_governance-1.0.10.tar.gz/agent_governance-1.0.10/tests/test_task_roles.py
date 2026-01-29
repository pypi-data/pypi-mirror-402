from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _write_agents_md(root: Path, roles: list[str]) -> None:
    lines = [
        "# Agent Governance Contract",
        "",
        "<!-- AGENTCTL:BEGIN -->",
        "policy_schema_version: 1",
        "allowed_roles:",
    ]
    for role in roles:
        lines.append(f"  - {role}")
    lines += [
        "<!-- AGENTCTL:END -->",
        "",
        "## agent init behavior",
        "- init is evidence-only (no LLM)",
        "",
        "## Notes",
        "- test notes",
        "",
    ]
    (root / "AGENTS.md").write_text("\n".join(lines))


def _run_agentctl(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    src_root = ROOT / "src"
    env = dict(os.environ)
    env["AGENT_GOVERNANCE_ROOT"] = str(root)
    if src_root.exists():
        env["PYTHONPATH"] = str(src_root)
    return subprocess.run(
        [sys.executable, "-m", "agent_governance.agentctl", *args],
        cwd=root,
        text=True,
        capture_output=True,
        env=env,
    )


def test_new_task_rejects_disallowed_role(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _write_agents_md(root, ["docs", "triage"])

    result = _run_agentctl(
        root,
        ["new-task", "--role", "bugfix", "--title", "should fail if role not allowed"],
    )
    assert result.returncode == 2
    assert "disallowed role: bugfix" in result.stderr
    assert "allowed_roles: docs, triage" in result.stderr
    assert "source: AGENTS.md" in result.stderr


def test_validate_task_rejects_disallowed_role(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _write_agents_md(root, ["docs"])
    task_path = root / "task.yaml"
    task_path.write_text(
        "\n".join(
            [
                "id: test",
                "title: disallowed",
                "role: bugfix",
                "goal: test",
                "repo_context:",
                "  branch: main",
                "  commit: unknown",
                "constraints:",
                "  allowed_write_paths: []",
                "deliverables: [diff]",
                "stop_conditions: [stop]",
            ]
        )
    )

    result = _run_agentctl(root, ["validate", "task", str(task_path)])
    assert result.returncode == 2
    assert "disallowed role: bugfix" in result.stderr
    assert "allowed_roles: docs" in result.stderr
    assert "source: AGENTS.md" in result.stderr


def test_new_task_rejects_disallowed_role_in_repo(disallow_bugfix_in_repo: None) -> None:
    result = _run_agentctl(
        ROOT,
        [
            "new-task",
            "--role",
            "bugfix",
            "--title",
            "should fail if role not allowed",
        ],
    )
    assert result.returncode == 2
    assert "disallowed role: bugfix" in result.stderr
    assert "allowed_roles:" in result.stderr
    assert "source: AGENTS.md" in result.stderr


@pytest.fixture
def disallow_bugfix_in_repo() -> None:
    agents_md = ROOT / "AGENTS.md"
    original = agents_md.read_text()
    updated = original.replace("\n  - bugfix\n", "\n")
    if original == updated:
        raise AssertionError("AGENTS.md did not contain bugfix role")
    agents_md.write_text(updated)
    try:
        yield
    finally:
        agents_md.write_text(original)
