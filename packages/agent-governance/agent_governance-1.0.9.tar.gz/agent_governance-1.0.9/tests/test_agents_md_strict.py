from __future__ import annotations

import io
import shutil
from contextlib import redirect_stdout
from pathlib import Path

from agent_governance.init import run_init

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def test_agents_md_invalid_yaml_strict(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "python_poetry_repo", repo)
    (repo / "AGENTS.md").write_text(
        "# Agent Governance Contract\n\npolicy_schema_version: [\n"
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = run_init(repo, strict=True)
    output = buffer.getvalue()
    assert code == 2
    assert "AGENTS.md" in output
