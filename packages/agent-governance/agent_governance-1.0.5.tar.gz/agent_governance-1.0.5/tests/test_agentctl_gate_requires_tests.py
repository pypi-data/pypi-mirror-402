from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def _make_repo(tmp_path: Path, include_policies: bool = True) -> Path:
    root = tmp_path / "repo"
    tools_dir = root / "agents" / "tools"
    tools_dir.mkdir(parents=True)

    src_root = Path(__file__).resolve().parents[1]
    src_agentctl = src_root / "agents" / "tools" / "agentctl.py"
    shutil.copy2(src_agentctl, tools_dir / "agentctl.py")
    shutil.copy2(src_root / "agents" / "__init__.py", root / "agents" / "__init__.py")
    shutil.copy2(
        src_root / "agents" / "tools" / "__init__.py",
        tools_dir / "__init__.py",
    )
    shutil.copytree(
        src_root / "agents" / "tools" / "init",
        tools_dir / "init",
    )
    shutil.copytree(
        src_root / "agents" / "tools" / "update_check",
        tools_dir / "update_check",
    )

    exe = shlex.quote(sys.executable)
    commands = {
        "test": f"{exe} -c 'print(\"collected 0 items\")'",
        "lint": f"{exe} -c 'print(\"ok\")'",
        "typecheck": f"{exe} -c 'print(\"ok\")'",
        "format": f"{exe} -c 'print(\"ok\")'",
    }

    profile: dict[str, object] = {
        "repo_name": "tmp",
        "primary_language": "python",
        "commands": commands,
    }
    if include_policies:
        profile["policies"] = {
            "require_tests": True,
            "python_test_glob": "tests/test_*.py",
        }

    repo_profile = root / "agents" / "repo_profile.yaml"
    repo_profile.write_text(yaml.safe_dump(profile, sort_keys=False))
    return root


def _run_gate(root: Path) -> tuple[int, str]:
    agentctl = root / "agents" / "tools" / "agentctl.py"
    src_path = Path(__file__).resolve().parents[1] / "src"
    env = dict(os.environ)
    if src_path.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{src_path}{os.pathsep}{existing}" if existing else str(src_path)
        )
    result = subprocess.run(
        [sys.executable, str(agentctl), "gate", "pr"],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )
    report = max((root / "reports" / "gates").glob("*.md"))
    return result.returncode, report.read_text()


def test_gate_requires_tests(tmp_path: Path) -> None:
    root = _make_repo(tmp_path)
    code, report = _run_gate(root)
    assert code == 1
    assert "require_tests true" in report
    assert "python_test_glob=tests/test_*.py" in report
