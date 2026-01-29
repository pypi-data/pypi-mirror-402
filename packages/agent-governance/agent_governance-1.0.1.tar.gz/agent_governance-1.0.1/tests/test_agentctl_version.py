from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_agentctl_version_no_git_stderr(tmp_path: Path) -> None:
    src_path = Path(__file__).resolve().parents[1] / "src"
    env = dict(os.environ)
    if src_path.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
        )
    result = subprocess.run(
        [sys.executable, "-m", "agent_governance.agentctl", "--version"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        env=env,
    )
    assert result.returncode == 0
    assert result.stderr == ""
