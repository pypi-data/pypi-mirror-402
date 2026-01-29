from __future__ import annotations

import re
import shutil
from pathlib import Path

from agent_governance.init import _resolve_init_tool_version

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def test_init_tool_version_format_nonempty(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURES / "python_poetry_repo", repo)
    version = _resolve_init_tool_version()
    assert version
    assert re.match(r"^\d+\.\d+\.\d+$", version)
