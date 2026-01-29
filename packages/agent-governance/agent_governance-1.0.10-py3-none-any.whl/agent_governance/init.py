#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml

from agent_governance import PACKAGE_NAME

IGNORED_PATH_PARTS = {".git", ".venv", "node_modules", ".agents"}

try:
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


RISK_PATH_CANDIDATES = [
    "data",
    "schemas",
    "migrations",
    "infra",
    "terraform",
    "docker",
    "k8s",
    ".github/workflows",
    "scripts",
    "config",
    "db",
]

ROUTING_TRIGGERS = {
    "schemas/": "schema_guard",
    "migrations/": "migration_guard",
    "infra/": "infra_guard",
    "terraform/": "infra_guard",
    "k8s/": "infra_guard",
    "docker/": "container_guard",
    "db/": "data_guard",
    "data/": "data_guard",
    ".github/workflows/": "ci_guard",
}


@dataclass
class Signal:
    path: str
    line_start: int
    line_end: int
    snippet: str
    note: str


@dataclass
class Fact:
    fact_type: str
    value: Any
    source: dict[str, Any]


class ParseError(Exception):
    def __init__(self, path: Path, message: str) -> None:
        super().__init__(message)
        self.path = path
        self.message = message


def read_text_file(path: Path, required: bool = False) -> str | None:
    try:
        data = path.read_bytes()
    except OSError as exc:
        if required:
            raise ParseError(path, str(exc)) from exc
        return None
    if b"\x00" in data:
        if required:
            raise ParseError(path, "binary file not supported")
        return None
    return data.decode("utf-8", errors="replace")


def read_lines(path: Path, required: bool = False) -> list[str]:
    text = read_text_file(path, required=required)
    if text is None:
        return []
    return text.splitlines()


def find_line_number(lines: list[str], predicate: re.Pattern[str]) -> int | None:
    for idx, line in enumerate(lines, start=1):
        if predicate.search(line):
            return idx
    return None


def make_signal(
    root: Path,
    path: Path,
    line_start: int,
    line_end: int,
    note: str,
    lines: list[str] | None = None,
) -> Signal:
    lines = lines if lines is not None else read_lines(path)
    snippet_lines = lines[line_start - 1 : line_end] if lines else []
    snippet = "\n".join(snippet_lines).strip()
    return Signal(
        path=str(path.relative_to(root)),
        line_start=line_start,
        line_end=line_end,
        snippet=snippet,
        note=note,
    )


def make_signal_path_only(root: Path, path: Path, note: str) -> Signal:
    return Signal(
        path=str(path.relative_to(root)),
        line_start=1,
        line_end=1,
        snippet="",
        note=note,
    )


def add_fact(facts: list[Fact], fact_type: str, value: Any, signal: Signal) -> None:
    facts.append(
        Fact(
            fact_type=fact_type,
            value=value,
            source={
                "path": signal.path,
                "line_start": signal.line_start,
                "line_end": signal.line_end,
            },
        )
    )


def _is_ignored_path(root: Path, path: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    parts = rel.parts
    if any(part in IGNORED_PATH_PARTS for part in parts):
        return True
    if "tests" in parts and "fixtures" in parts:
        if parts.index("tests") < parts.index("fixtures"):
            return True
    return False


def find_first_match(root: Path, filename: str) -> Path | None:
    direct = root / filename
    if direct.exists() and not _is_ignored_path(root, direct):
        return direct
    matches = sorted(
        p for p in root.rglob(filename) if p.is_file() and not _is_ignored_path(root, p)
    )
    return matches[0] if matches else None


def detect_python(
    root: Path, signals: list[Signal], facts: list[Fact]
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    detected = False
    build_tools: list[str] = []
    verify_commands: list[dict[str, Any]] = []

    pyproject = find_first_match(root, "pyproject.toml")
    if pyproject:
        detected = True
        text = read_text_file(pyproject, required=True)
        lines = read_lines(pyproject, required=True)
        try:
            data = tomllib.loads(text or "")
        except tomllib.TOMLDecodeError as exc:
            raise ParseError(pyproject, str(exc)) from exc
        tool = data.get("tool", {}) if isinstance(data, dict) else {}
        if "poetry" in tool:
            line = find_line_number(lines, re.compile(r"^\s*\[tool\.poetry\]")) or 1
            signal = make_signal(
                root, pyproject, line, line, "pyproject tool.poetry", lines=lines
            )
            signals.append(signal)
            add_fact(facts, "detected_build_tool", "poetry", signal)
            build_tools.append("poetry")
            verify_commands.append(
                {
                    "cwd": ".",
                    "command": ["poetry", "run", "pytest", "-q"],
                    "reason": "pyproject tool.poetry",
                    "source": signal,
                }
            )
        if "uv" in tool:
            line = find_line_number(lines, re.compile(r"^\s*\[tool\.uv\]")) or 1
            signal = make_signal(
                root, pyproject, line, line, "pyproject tool.uv", lines=lines
            )
            signals.append(signal)
            add_fact(facts, "detected_build_tool", "uv", signal)
            build_tools.append("uv")
            verify_commands.append(
                {
                    "cwd": ".",
                    "command": ["uv", "run", "pytest", "-q"],
                    "reason": "pyproject tool.uv",
                    "source": signal,
                }
            )
        for section in ["ruff", "pytest", "mypy", "pyright"]:
            if section in tool:
                pattern = re.compile(rf"^\s*\[tool\.{section}(\.|\\])")
                line = find_line_number(lines, pattern) or 1
                signal = make_signal(
                    root,
                    pyproject,
                    line,
                    line,
                    f"pyproject tool.{section}",
                    lines=lines,
                )
                signals.append(signal)
                add_fact(facts, "detected_python_tool", section, signal)
        if not build_tools:
            line = find_line_number(lines, re.compile(r"^\s*\[project\]")) or 1
            signal = make_signal(
                root, pyproject, line, line, "pyproject project", lines=lines
            )
            signals.append(signal)
            add_fact(facts, "detected_build_tool", "pip", signal)
            build_tools.append("pip")
            verify_commands.append(
                {
                    "cwd": ".",
                    "command": ["python", "-m", "pytest", "-q"],
                    "reason": "pyproject project",
                    "source": signal,
                }
            )
    else:
        for name in ["requirements.txt", "setup.cfg", "setup.py"]:
            path = find_first_match(root, name)
            if path:
                detected = True
                signal = make_signal(root, path, 1, 1, f"{name} present")
                signals.append(signal)
                add_fact(facts, "detected_build_tool", "pip", signal)
                build_tools.append("pip")
                verify_commands.append(
                    {
                        "cwd": ".",
                        "command": ["python", "-m", "pytest", "-q"],
                        "reason": f"{name} present",
                        "source": signal,
                    }
                )
                break

    return detected, build_tools, verify_commands


def _find_json_key_line(lines: list[str], key: str) -> int:
    pattern = re.compile(rf'"{re.escape(key)}"\s*:')
    return find_line_number(lines, pattern) or 1


def detect_node(
    root: Path, signals: list[Signal], facts: list[Fact]
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    pkg = find_first_match(root, "package.json")
    if not pkg:
        return False, [], []

    detected = True
    text = read_text_file(pkg, required=True)
    lines = read_lines(pkg, required=True)
    try:
        data = json.loads(text or "")
    except json.JSONDecodeError as exc:
        raise ParseError(pkg, str(exc)) from exc

    build_tools: list[str] = []
    verify_commands: list[dict[str, Any]] = []

    package_manager = data.get("packageManager", "")
    runner = "npm"
    if isinstance(package_manager, str):
        if package_manager.startswith("pnpm"):
            runner = "pnpm"
            build_tools.append("pnpm")
        elif package_manager.startswith("yarn"):
            runner = "yarn"
            build_tools.append("yarn")
        elif package_manager.startswith("npm"):
            runner = "npm"
            build_tools.append("npm")
    if not build_tools:
        build_tools.append("npm")

    signal_line = _find_json_key_line(lines, "scripts")
    signal = make_signal(
        root, pkg, signal_line, signal_line, "package.json scripts", lines=lines
    )
    signals.append(signal)
    add_fact(facts, "detected_build_tool", build_tools[-1], signal)

    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    if isinstance(scripts, dict):
        script_map = [
            ("test", "test"),
            ("lint", "lint"),
            ("typecheck", "typecheck"),
        ]
        for script_key, kind in script_map:
            if script_key in scripts:
                line = _find_json_key_line(lines, script_key)
                script_signal = make_signal(
                    root,
                    pkg,
                    line,
                    line,
                    f"package.json script {script_key}",
                    lines=lines,
                )
                signals.append(script_signal)
                add_fact(facts, "detected_node_script", script_key, script_signal)
                if runner in ["pnpm", "yarn"]:
                    cmd = [runner, "-s", script_key]
                elif script_key == "test":
                    cmd = ["npm", "test"]
                else:
                    cmd = ["npm", "run", script_key]
                verify_commands.append(
                    {
                        "cwd": ".",
                        "command": cmd,
                        "reason": f"package.json script {script_key}",
                        "source": script_signal,
                    }
                )

    return detected, build_tools, verify_commands


def detect_rust(
    root: Path, signals: list[Signal], facts: list[Fact]
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    cargo = find_first_match(root, "Cargo.toml")
    if not cargo:
        return False, [], []

    lines = read_lines(cargo, required=True)
    line = find_line_number(lines, re.compile(r"^\s*\[package\]")) or 1
    signal = make_signal(root, cargo, line, line, "Cargo.toml package", lines=lines)
    signals.append(signal)
    add_fact(facts, "detected_build_tool", "cargo", signal)

    return (
        True,
        ["cargo"],
        [
            {
                "cwd": ".",
                "command": ["cargo", "test"],
                "reason": "Cargo.toml package",
                "source": signal,
            }
        ],
    )


def detect_go(
    root: Path, signals: list[Signal], facts: list[Fact]
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    go_mod = find_first_match(root, "go.mod")
    if not go_mod:
        return False, [], []

    signal = make_signal(root, go_mod, 1, 1, "go.mod present")
    signals.append(signal)
    add_fact(facts, "detected_build_tool", "go", signal)

    return (
        True,
        ["go"],
        [
            {
                "cwd": ".",
                "command": ["go", "test", "./..."],
                "reason": "go.mod present",
                "source": signal,
            }
        ],
    )


def detect_ci(
    root: Path, signals: list[Signal], facts: list[Fact]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.exists():
        return [], []

    commands: list[dict[str, Any]] = []
    ci_gates: list[dict[str, Any]] = []

    for workflow in sorted(workflows_dir.glob("*.y*ml")):
        lines = read_lines(workflow)
        run_entries = extract_run_commands(lines)
        for cmd, line_no in run_entries:
            label = "ci run step"
            signal = make_signal(root, workflow, line_no, line_no, label, lines=lines)
            signals.append(signal)

            if not is_repo_local_ci_command(cmd):
                continue

            command_array = shlex.split(cmd)
            commands.append(
                {
                    "cwd": ".",
                    "command": command_array,
                    "reason": f"ci workflow {workflow.name}",
                    "source": signal,
                }
            )

            kind = classify_ci_command(cmd)
            if kind:
                ci_gates.append(
                    {
                        "kind": kind,
                        "cwd": ".",
                        "command": command_array,
                    }
                )
                add_fact(
                    facts, "ci_gate", {"kind": kind, "command": command_array}, signal
                )

    return commands, ci_gates


def extract_run_commands(lines: list[str]) -> list[tuple[str, int]]:
    results: list[tuple[str, int]] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if re.match(r"^\s*run:\s*\|\s*$", line):
            base_indent = len(line) - len(line.lstrip())
            idx += 1
            block_lines = []
            while idx < len(lines):
                next_line = lines[idx]
                indent = len(next_line) - len(next_line.lstrip())
                if indent <= base_indent:
                    break
                stripped = next_line.strip()
                if stripped:
                    block_lines.append((stripped, idx + 1))
                idx += 1
            if block_lines:
                results.append(block_lines[0])
            continue
        match = re.match(r"^\s*run:\s*(.+)$", line)
        if match:
            results.append((match.group(1).strip(), idx + 1))
        idx += 1
    return results


def is_repo_local_ci_command(command: str) -> bool:
    markers = [
        "pytest",
        "ruff",
        "mypy",
        "pyright",
        "cargo test",
        "go test",
        "npm",
        "pnpm",
        "yarn",
    ]
    return any(marker in command for marker in markers)


def classify_ci_command(command: str) -> str | None:
    lowered = command.lower()
    if "pytest" in lowered or "cargo test" in lowered or "go test" in lowered:
        return "test"
    if "npm" in lowered or "pnpm" in lowered or "yarn" in lowered:
        if "test" in lowered:
            return "test"
    if "lint" in lowered or "ruff" in lowered:
        return "lint"
    if "mypy" in lowered or "pyright" in lowered or "typecheck" in lowered:
        return "typecheck"
    return None


def detect_risk_paths(
    root: Path, signals: list[Signal], facts: list[Fact]
) -> list[str]:
    risk_paths: list[str] = []
    for candidate in RISK_PATH_CANDIDATES:
        path = root / candidate
        if not path.exists():
            continue
        evidence = find_evidence_file(path)
        if evidence is None:
            continue
        signal = make_signal_path_only(root, evidence, f"risk path {candidate}")
        signals.append(signal)
        value = f"{candidate}/"
        risk_paths.append(value)
        add_fact(facts, "risk_path", value, signal)
    return risk_paths


def find_evidence_file(path: Path) -> Path | None:
    if path.is_file():
        return path
    root = path
    while root.parent != root and not (root / ".git").exists():
        root = root.parent
    files = sorted(
        p for p in path.rglob("*") if p.is_file() and not _is_ignored_path(root, p)
    )
    return files[0] if files else None


def dedupe_commands(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for command in commands:
        key = tuple(command["command"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(command)
    return deduped


def _normalize_python_command(command: list[str]) -> list[str]:
    if not command:
        return command
    tool = command[0]
    if tool == "python3":
        if shutil.which("python3"):
            return command
        if shutil.which("python"):
            return ["python", *command[1:]]
        return command
    if tool == "python":
        if shutil.which("python3"):
            return ["python3", *command[1:]]
        if shutil.which("python"):
            return command
        return command
    return command


def normalize_verify_commands(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for command in commands:
        normalized.append(
            {
                "cwd": command["cwd"],
                "command": _normalize_python_command(command["command"]),
            }
        )
    return normalized


def dedupe_verify_details(commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for command in commands:
        normalized_command = _normalize_python_command(command["command"])
        key = tuple(normalized_command)
        if key in seen:
            continue
        seen.add(key)
        updated = dict(command)
        updated["command"] = normalized_command
        deduped.append(updated)
    return deduped


def merge_overlay(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key in ["verify_commands", "risk_paths"]:
        base_list = merged.get(key, [])
        overlay_list = overlay.get(key, [])
        merged[key] = base_list + overlay_list
    for key in overlay:
        if key not in ["verify_commands", "risk_paths"]:
            merged[key] = overlay[key]
    return merged


def render_report(
    summary: dict[str, Any],
    signals: list[Signal],
    facts: list[Fact],
    write: bool,
    out_dir: Path,
    agents_status: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = []
    lines.append("# Repo Init Report")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- repo_root: .")
    lines.append(f"- detected_languages: {', '.join(summary['languages']) or 'none'}")
    lines.append(
        f"- detected_build_tools: {', '.join(summary['build_tools']) or 'none'}"
    )
    lines.append(f"- verify_commands: {len(summary['verify_commands'])}")
    lines.append("")
    lines.append("## Detected signals")
    if not signals:
        lines.append("- none")
    else:
        for signal in sorted(signals, key=lambda s: (s.path, s.line_start, s.note)):
            location = f"{signal.path}:{signal.line_start}-{signal.line_end}"
            snippet = signal.snippet.replace("\n", " ")
            lines.append(f"- {location} | {signal.note} | {snippet}")
    lines.append("")
    lines.append("## Evidence")
    if not facts:
        lines.append("- none")
    else:
        for fact in sorted(
            facts,
            key=lambda f: (
                f.source["path"],
                f.source["line_start"],
                f.fact_type,
                str(f.value),
            ),
        ):
            location = (
                f"{fact.source['path']}:{fact.source['line_start']}-"
                f"{fact.source['line_end']}"
            )
            lines.append(f"- {fact.fact_type}: {fact.value} | {location}")
    lines.append("")
    lines.append("## Proposed verify pipeline")
    if not summary["verify_commands"]:
        lines.append("- none")
    else:
        for item in summary["verify_commands"]:
            cmd = " ".join(item["command"])
            lines.append(f"- {cmd} (from {item['reason']})")
    lines.append("")
    lines.append("## Proposed risk paths")
    if not summary["risk_paths"]:
        lines.append("- none")
    else:
        for risk in summary["risk_paths"]:
            lines.append(f"- {risk}")
    lines.append("")
    lines.append("## AGENTS.md status")
    if not agents_status:
        lines.append("- unknown")
    else:
        lines.append(f"- status: {agents_status['status']}")
        if agents_status.get("details"):
            for detail in agents_status["details"]:
                lines.append(f"- {detail}")
        if agents_status.get("status") in {"missing", "incompatible"}:
            lines.append("- action: run agentctl bootstrap to create/update policy block")
    lines.append("")
    if not write:
        lines.append("## Planned file writes")
        lines.append(f"- {out_dir / 'AGENTS.repo.overlay.yaml'}")
        lines.append(f"- {out_dir / 'init_report.md'}")
        lines.append(f"- {out_dir / 'init_facts.json'}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _display_path(root: Path, path: Path) -> str:
    root = root.resolve()
    path = path.resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        temp_root = Path(tempfile.gettempdir()).resolve()
        try:
            rel = path.relative_to(temp_root)
            return f"<tmp>/{rel.as_posix()}"
        except ValueError:
            return path.name


def _normalize_error_message(root: Path, message: str) -> str:
    root_str = str(root.resolve())
    temp_root = str(Path(tempfile.gettempdir()).resolve())
    normalized = message.replace(root_str, "..")
    normalized = normalized.replace(temp_root, "<tmp>")
    return normalized


def render_error_report(root: Path, path: Path, message: str) -> str:
    lines: list[str] = []
    lines.append("# Repo Init Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("- status: failed")
    lines.append("")
    lines.append("## Errors")
    display_path = _display_path(root, path)
    normalized_message = _normalize_error_message(root, message)
    lines.append(f"- {display_path}: {normalized_message}")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_outputs(
    out_dir: Path,
    overlay: dict[str, Any],
    report: str,
    facts: list[Fact],
    init_tool_version: str,
    generated_at_utc: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = out_dir / "AGENTS.repo.overlay.yaml"
    report_path = out_dir / "init_report.md"
    facts_path = out_dir / "init_facts.json"

    overlay_path.write_text(yaml.safe_dump(overlay, sort_keys=False))
    report_path.write_text(report)
    facts_payload = {
        "init_tool_version": init_tool_version,
        "generated_at_utc": generated_at_utc,
        "facts": [
            {
                "fact_type": fact.fact_type,
                "value": fact.value,
                "source": fact.source,
            }
            for fact in facts
        ],
    }
    facts_path.write_text(json.dumps(facts_payload, indent=2, sort_keys=True))


def write_default_repo_profile(root: Path) -> None:
    profile_path = root / "agents" / "repo_profile.yaml"
    if profile_path.exists():
        return
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile_schema_version": 1,
        "gate_pr": {"steps": ["verify"]},
    }
    profile_path.write_text(yaml.safe_dump(payload, sort_keys=False))


def update_gitignore(root: Path, out_dir: Path) -> None:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return
    line = f"{out_dir.as_posix()}/"
    content_text = read_text_file(gitignore)
    if content_text is None:
        return
    content = content_text.splitlines()
    if line in content:
        return
    content.append(line)
    gitignore.write_text("\n".join(content) + "\n")


def build_overlay(
    root: Path,
) -> tuple[dict[str, Any], list[Signal], list[Fact], list[dict[str, Any]]]:
    signals: list[Signal] = []
    facts: list[Fact] = []

    detected_languages: set[str] = set()
    detected_build_tools: list[str] = []
    verify_commands: list[dict[str, Any]] = []

    ci_commands, ci_gates = detect_ci(root, signals, facts)
    if ci_commands:
        verify_commands.extend(ci_commands)

    python_detected, python_tools, python_commands = detect_python(root, signals, facts)
    if python_detected:
        detected_languages.add("python")
    detected_build_tools.extend(python_tools)
    verify_commands.extend(python_commands)

    node_detected, node_tools, node_commands = detect_node(root, signals, facts)
    if node_detected:
        detected_languages.add("node")
    detected_build_tools.extend(node_tools)
    verify_commands.extend(node_commands)

    rust_detected, rust_tools, rust_commands = detect_rust(root, signals, facts)
    if rust_detected:
        detected_languages.add("rust")
    detected_build_tools.extend(rust_tools)
    verify_commands.extend(rust_commands)

    go_detected, go_tools, go_commands = detect_go(root, signals, facts)
    if go_detected:
        detected_languages.add("go")
    detected_build_tools.extend(go_tools)
    verify_commands.extend(go_commands)

    risk_paths = detect_risk_paths(root, signals, facts)

    detected_build_tools = sorted(set(detected_build_tools))
    detected_languages = sorted(detected_languages)

    verify_details = dedupe_verify_details(verify_commands)
    normalized_verify = normalize_verify_commands(verify_details)

    routing_triggers = []
    for risk_path in sorted(risk_paths):
        gate = ROUTING_TRIGGERS.get(risk_path)
        if gate:
            routing_triggers.append({"path_glob": risk_path + "*", "gate": gate})

    overlay = {
        "repo_root": ".",
        "detected_languages": detected_languages,
        "detected_build_tools": detected_build_tools,
        "verify_commands": normalized_verify,
        "risk_paths": sorted(risk_paths),
        "ci_gates": ci_gates,
        "suggested_routing_triggers": routing_triggers,
    }

    for command in verify_details:
        if command.get("source"):
            add_fact(
                facts,
                "verify_command",
                {"cwd": command["cwd"], "command": command["command"]},
                command["source"],
            )

    return overlay, signals, facts, verify_details


def run_init(
    root: Path,
    write: bool = False,
    out_dir: str = ".agents/generated",
    force: bool = False,
    print_agents_template: bool = False,
    strict: bool = False,
) -> int:
    try:
        agents_status, agents_template = check_agents_md(
            root, signals=None, facts=None, strict=strict
        )
    except ParseError as exc:
        report = render_error_report(root, exc.path, exc.message)
        print(report, end="")
        if print_agents_template:
            print(check_agents_md(root, None, None, strict=False)[1], end="")
        return 2
    try:
        overlay, signals, facts, verify_details = build_overlay(root)
    except ParseError as exc:
        report = render_error_report(root, exc.path, exc.message)
        print(report, end="")
        if agents_status["status"] == "missing" and print_agents_template:
            print(agents_template, end="")
        return 2
    try:
        agents_status, _agents_template = check_agents_md(
            root, signals=signals, facts=facts, strict=strict
        )
    except ParseError as exc:
        report = render_error_report(root, exc.path, exc.message)
        print(report, end="")
        return 2
    out_path = root / out_dir
    out_dir_display = Path(out_dir)
    init_tool_version = _resolve_init_tool_version()
    generated_at_utc = _generated_timestamp()

    summary = {
        "languages": overlay["detected_languages"],
        "build_tools": overlay["detected_build_tools"],
        "verify_commands": verify_details,
        "risk_paths": overlay["risk_paths"],
    }
    report = render_report(
        summary, signals, facts, write, out_dir_display, agents_status
    )
    ordered_overlay = {
        "repo_root": overlay["repo_root"],
        "init_tool_version": init_tool_version,
        "generated_at_utc": generated_at_utc,
        "detected_languages": overlay["detected_languages"],
        "detected_build_tools": overlay["detected_build_tools"],
        "verify_commands": overlay["verify_commands"],
        "risk_paths": overlay["risk_paths"],
        "ci_gates": overlay["ci_gates"],
        "suggested_routing_triggers": overlay["suggested_routing_triggers"],
    }

    if write:
        outputs = [
            out_path / "AGENTS.repo.overlay.yaml",
            out_path / "init_report.md",
            out_path / "init_facts.json",
        ]
        if not force:
            existing = [str(path) for path in outputs if path.exists()]
            if existing:
                report = render_error_report(
                    root,
                    out_path,
                    f"outputs exist; rerun with --force: {', '.join(existing)}",
                )
                print(report, end="")
                return 3
        try:
            write_outputs(
                out_path,
                ordered_overlay,
                report,
                facts,
                init_tool_version,
                generated_at_utc,
            )
            write_default_repo_profile(root)
            update_gitignore(root, out_dir_display)
        except OSError as exc:
            report = render_error_report(root, out_path, f"write failed: {exc}")
            print(report, end="")
            return 3

    print(report, end="")
    if agents_status["status"] == "missing" and print_agents_template:
        print(agents_template, end="")
    return 0


def _generated_timestamp() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def parse_agents_policy(path: Path) -> tuple[dict[str, Any], str | None]:
    content_text = read_text_file(path, required=True)
    content = content_text.splitlines() if content_text else []
    managed_begin = "<!-- AGENTCTL:BEGIN -->"
    managed_end = "<!-- AGENTCTL:END -->"
    begin_indices = [idx for idx, line in enumerate(content) if line.strip() == managed_begin]
    end_indices = [idx for idx, line in enumerate(content) if line.strip() == managed_end]
    if begin_indices or end_indices:
        if len(begin_indices) != 1 or len(end_indices) != 1:
            raise ParseError(path, "multiple managed policy blocks found")
        begin = begin_indices[0]
        end_marker = end_indices[0]
        if begin >= end_marker:
            raise ParseError(path, "managed policy block is malformed")
        start = begin + 1
        end = end_marker - 1
        block = "\n".join(content[start : end + 1])
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            raise ParseError(path, str(exc)) from exc
        if not isinstance(data, dict):
            raise ParseError(path, "policy block must be a YAML mapping")
        return data, f"{path.name}:{start + 1}-{end + 1}"
    fence_indices = [idx for idx, line in enumerate(content) if line.strip() == "```yaml"]
    if fence_indices:
        if len(fence_indices) > 1:
            raise ParseError(path, "multiple policy blocks found")
        fence_start = fence_indices[0]
        fence_end = None
        for idx in range(fence_start + 1, len(content)):
            if content[idx].strip() == "```":
                fence_end = idx
                break
        if fence_end is None:
            raise ParseError(path, "unterminated policy block")
        for idx, line in enumerate(content):
            if fence_start <= idx <= fence_end:
                continue
            if line.lstrip().startswith("policy_schema_version:"):
                raise ParseError(path, "multiple policy blocks found")
        start = fence_start + 1
        end = fence_end - 1
    else:
        starts = [
            idx
            for idx, line in enumerate(content)
            if line.lstrip().startswith("policy_schema_version:")
        ]
        if not starts:
            raise ParseError(path, "missing policy block")
        if len(starts) > 1:
            raise ParseError(path, "multiple policy blocks found")
        start = starts[0]
        start_indent = len(content[start]) - len(content[start].lstrip())
        end = start
        for idx in range(start + 1, len(content)):
            line = content[idx]
            if not line.strip():
                break
            if re.match(r"^#{1,6}\s", line.lstrip()):
                break
            line_indent = len(line) - len(line.lstrip())
            if line_indent < start_indent:
                break
            end = idx
    block = "\n".join(content[start : end + 1])
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise ParseError(path, str(exc)) from exc
    if not isinstance(data, dict):
        raise ParseError(path, "policy block must be a YAML mapping")
    return data, f"{path.name}:{start + 1}-{end + 1}"


def check_agents_md(
    root: Path,
    signals: list[Signal] | None,
    facts: list[Fact] | None,
    strict: bool,
) -> tuple[dict[str, Any], str]:
    path = root / "AGENTS.md"
    template = (
        "<!-- AGENTCTL:BEGIN -->\\n"
        "policy_schema_version: 1\\n"
        "allowed_roles:\\n"
        "  - triage\\n"
        "<!-- AGENTCTL:END -->\\n\\n"
        "## agent init behavior\\n"
        "- init is evidence-only (no LLM)\\n"
        "- ignore: .venv/, node_modules/, .git/\\n"
        "\\n"
        "## Notes\\n"
        "- Add human context here.\\n"
    )
    if not path.exists():
        return {"status": "missing", "details": ["AGENTS.md not found"]}, template

    lines = read_lines(path, required=True)
    details: list[str] = []
    status = "ok"
    try:
        policy, block_range = parse_agents_policy(path)
    except ParseError as exc:
        if strict:
            raise
        status = "incompatible"
        details.append(f"{exc.path}: {exc.message}")
        return {"status": status, "details": details}, template

    version = policy.get("policy_schema_version")
    if not isinstance(version, int):
        if strict:
            raise ParseError(path, "policy_schema_version must be an integer")
        status = "incompatible"
        details.append("policy_schema_version must be an integer")
    elif version < 1 or version > 1:
        if strict:
            raise ParseError(path, f"unsupported policy_schema_version: {version}")
        status = "incompatible"
        details.append(f"unsupported policy_schema_version: {version}")
    else:
        details.append(f"policy_schema_version: {version}")

    required_sections = ["## agent init behavior"]
    for section in required_sections:
        line = find_line_number(lines, re.compile(re.escape(section))) or 0
        if not line:
            status = "incompatible"
            details.append(f"missing section: {section}")
        else:
            details.append(f"{section} at {path.name}:{line}-{line}")

    if signals is not None and block_range:
        block_start = block_range.split(":")[1].split("-")[0]
        line_no = int(block_start)
        signal = make_signal(root, path, line_no, line_no, "AGENTS.md policy block")
        signals.append(signal)
        if facts is not None:
            add_fact(facts, "agents_md_policy", {"range": block_range}, signal)

    return {"status": status, "details": details}, template


def _resolve_init_tool_version() -> str:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "pyproject.toml"
        if not candidate.exists():
            continue
        text = read_text_file(candidate)
        if text is None:
            return "unknown"
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            return "unknown"
        if not isinstance(data, dict):
            return "unknown"
        project = data.get("project", {})
        if isinstance(project, dict):
            version = project.get("version")
            if isinstance(version, str) and version.strip():
                return version.strip()
        tool = data.get("tool", {})
        if isinstance(tool, dict):
            poetry = tool.get("poetry", {})
            if isinstance(poetry, dict):
                version = poetry.get("version")
                if isinstance(version, str) and version.strip():
                    return version.strip()
        return "unknown"

    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "unknown"
