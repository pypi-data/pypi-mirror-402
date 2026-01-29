from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from agent_governance.init import parse_agents_policy

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "bootstrap"


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    dest = tmp_path / name
    shutil.copytree(FIXTURES / name, dest)
    return dest


def _run_bootstrap(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    src_path = Path(__file__).resolve().parents[1] / "src"
    if src_path.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
        )
    cmd = [sys.executable, "-m", "agent_governance.agentctl", "bootstrap", *args]
    return subprocess.run(
        cmd,
        cwd=repo,
        text=True,
        capture_output=True,
        env=env,
    )


def _read(path: Path) -> str:
    return path.read_text()


def _expected(path: Path) -> str:
    return (path / "expected_agents_md.md").read_text()


def test_bootstrap_preview_does_not_write(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "no_agents_md")
    result = _run_bootstrap(repo, "--allow", "triage,testing")
    assert result.returncode == 0
    assert not (repo / "AGENTS.md").exists()

    repo = _copy_fixture(tmp_path, "agents_md_with_policy_block")
    before = _read(repo / "AGENTS.md")
    result = _run_bootstrap(repo, "--allow", "docs,triage")
    assert result.returncode == 0
    after = _read(repo / "AGENTS.md")
    assert before == after


def test_bootstrap_create_matches_golden(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "no_agents_md")
    result = _run_bootstrap(repo, "--allow", "triage,testing", "--write")
    assert result.returncode == 0
    content = _read(repo / "AGENTS.md")
    assert content == _expected(repo)
    policy, _block = parse_agents_policy(repo / "AGENTS.md")
    assert policy["allowed_roles"] == ["testing", "triage"]


def test_bootstrap_appends_when_no_block(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "agents_md_no_policy_block")
    result = _run_bootstrap(repo, "--allow", "triage,testing", "--write")
    assert result.returncode == 0
    assert _read(repo / "AGENTS.md") == _expected(repo)


def test_bootstrap_updates_block_only(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "agents_md_with_policy_block")
    result = _run_bootstrap(repo, "--allow", "docs,triage", "--write")
    assert result.returncode == 0
    assert _read(repo / "AGENTS.md") == _expected(repo)
    first = _read(repo / "AGENTS.md")
    result = _run_bootstrap(repo, "--allow", "docs,triage", "--write")
    assert result.returncode == 0
    second = _read(repo / "AGENTS.md")
    assert first == second


def test_bootstrap_updates_weird_formatting(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "agents_md_weird_formatting")
    result = _run_bootstrap(repo, "--allow", "triage,testing", "--write")
    assert result.returncode == 0
    assert _read(repo / "AGENTS.md") == _expected(repo)


def test_bootstrap_two_blocks_fails(tmp_path: Path) -> None:
    repo = _copy_fixture(tmp_path, "agents_md_with_two_blocks")
    before = _read(repo / "AGENTS.md")
    result = _run_bootstrap(repo, "--allow", "triage", "--write")
    assert result.returncode == 2
    after = _read(repo / "AGENTS.md")
    assert before == after
