from __future__ import annotations

import json
import os
from pathlib import Path

from agent_governance import agentctl


class _FakeDist:
    def __init__(self, direct_url: dict[str, object] | None) -> None:
        self._direct_url = direct_url

    def read_text(self, name: str) -> str | None:
        if name != "direct_url.json":
            return None
        if self._direct_url is None:
            return None
        return json.dumps(self._direct_url)


def _write_agents_md(root: Path, require_pinned: bool) -> None:
    root.joinpath("AGENTS.md").write_text(
        "\n".join(
            [
                "# Agent Governance Contract",
                "",
                "policy_schema_version: 1",
                f"require_pinned_tool: {str(require_pinned).lower()}",
                "",
                "## agent init behavior",
                "",
                "- ok",
                "",
            ]
        )
    )


def test_require_pinned_blocks_editable(monkeypatch, tmp_path: Path) -> None:
    _write_agents_md(tmp_path, True)
    monkeypatch.setattr(agentctl, "ROOT", tmp_path)
    monkeypatch.setenv("CI", "false")
    monkeypatch.setattr(agentctl, "get_version", lambda: "1.0.0")
    monkeypatch.setattr(
        agentctl.metadata,
        "distribution",
        lambda _name: _FakeDist({"dir_info": {"editable": True}}),
    )
    assert agentctl._enforce_tool_policy() == 2


def test_require_pinned_allows_wheel(monkeypatch, tmp_path: Path) -> None:
    _write_agents_md(tmp_path, True)
    monkeypatch.setattr(agentctl, "ROOT", tmp_path)
    monkeypatch.setenv("CI", "false")
    monkeypatch.setattr(agentctl, "get_version", lambda: "1.0.0")
    monkeypatch.setattr(
        agentctl.metadata,
        "distribution",
        lambda _name: _FakeDist(None),
    )
    assert agentctl._enforce_tool_policy() == 0
