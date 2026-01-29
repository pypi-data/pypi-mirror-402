#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from importlib import resources
from pathlib import Path
import shlex

import yaml
from jsonschema import validate, ValidationError

from importlib import metadata

from packaging.version import InvalidVersion, Version

from agent_governance import PACKAGE_NAME, get_version
from agent_governance.init import (
    ParseError,
    check_agents_md,
    parse_agents_policy,
    render_error_report,
    run_init,
)

CANONICAL_ROLES = [
    {"name": "triage", "purpose": "Clarify scope, risks, and next steps."},
    {"name": "testing", "purpose": "Add/adjust tests and verify coverage."},
    {"name": "bugfix", "purpose": "Fix defects with minimal scope."},
    {"name": "refactor", "purpose": "Improve structure without behavior changes."},
    {"name": "docs", "purpose": "Update documentation and usage notes."},
    {"name": "data_contract", "purpose": "Define or validate data contracts."},
    {"name": "perf", "purpose": "Profile and improve performance."},
    {"name": "security", "purpose": "Harden security and address threats."},
]

DEFAULT_MIN_TOOL_VERSION = "1.0.10"
from agent_governance.update_check import maybe_check, resolve_mode


def resolve_repo_root() -> Path:
    env_root = os.environ.get("AGENT_GOVERNANCE_ROOT")
    if env_root:
        return Path(env_root).resolve()
    start = Path.cwd().resolve()
    for parent in [start, *start.parents]:
        git_marker = parent / ".git"
        if git_marker.exists():
            return parent
    return start


ROOT = resolve_repo_root()
CONTRACTS = ROOT / "agents" / "contracts"
TEMPLATES = CONTRACTS / "templates"
REPORTS_TASKS = ROOT / "reports" / "tasks"
REPORTS_GATES = ROOT / "reports" / "gates"
LOGS_AGENTS = ROOT / "logs" / "agents"


def _load_agents_policy(strict: bool) -> dict[str, object] | None:
    path = ROOT / "AGENTS.md"
    if not path.exists():
        return None
    try:
        policy, _block = parse_agents_policy(path)
    except ParseError:
        if strict:
            raise
        return None
    version = policy.get("policy_schema_version")
    if not isinstance(version, int):
        if strict:
            raise ParseError(path, "policy_schema_version must be an integer")
        return None
    if version < 1 or version > 1:
        if strict:
            raise ParseError(path, f"unsupported policy_schema_version: {version}")
        return None
    return policy


def load_allowed_roles() -> list[str]:
    policy = _load_agents_policy(strict=True)
    if not policy:
        raise ParseError(ROOT / "AGENTS.md", "missing policy block")
    allowed_roles = policy.get("allowed_roles")
    if not isinstance(allowed_roles, list) or not allowed_roles:
        raise ParseError(ROOT / "AGENTS.md", "allowed_roles must be a non-empty list")
    for role in allowed_roles:
        if not isinstance(role, str):
            raise ParseError(ROOT / "AGENTS.md", "allowed_roles must be a list of strings")
    return allowed_roles


def _fail_disallowed_role(role: str, allowed_roles: list[str]) -> None:
    print(f"disallowed role: {role}", file=sys.stderr)
    print(f"allowed_roles: {', '.join(allowed_roles)}", file=sys.stderr)
    print("source: AGENTS.md", file=sys.stderr)
    raise SystemExit(2)


def _report_disallowed_role(role: str, allowed_roles: list[str]) -> None:
    print(f"disallowed role: {role}", file=sys.stderr)
    print(f"allowed_roles: {', '.join(allowed_roles)}", file=sys.stderr)
    print("source: AGENTS.md", file=sys.stderr)


def _collect_task_packets_for_gate() -> list[Path]:
    task_paths: dict[str, Path] = {}
    tasks_dir = REPORTS_TASKS
    if tasks_dir.exists():
        for path in tasks_dir.glob("*.task.yaml"):
            task_paths[str(path)] = path

    logs_dir = LOGS_AGENTS
    if logs_dir.exists():
        for log_path in logs_dir.glob("*.log"):
            try:
                for line in log_path.read_text().splitlines():
                    if line.startswith("task_id: "):
                        task_id = line.split("task_id: ", 1)[1].strip()
                        if not task_id:
                            continue
                        candidate = tasks_dir / f"{task_id}.task.yaml"
                        if candidate.exists():
                            task_paths[str(candidate)] = candidate
            except OSError:
                continue

    return sorted(task_paths.values())


def _validate_task_roles_for_gate() -> None:
    task_paths = _collect_task_packets_for_gate()
    if not task_paths:
        return

    try:
        allowed_roles = load_allowed_roles()
    except ParseError as exc:
        report = render_error_report(ROOT, exc.path, exc.message)
        print(report, end="")
        raise SystemExit(2)

    failures = 0
    for path in task_paths:
        try:
            validate_packet(path, "task_packet.schema.json")
        except ValidationError as exc:
            print(f"task packet INVALID: {path}", file=sys.stderr)
            print(exc.message, file=sys.stderr)
            failures += 1
            continue

        data = load_yaml(path) or {}
        role = data.get("role")
        if role not in allowed_roles:
            _report_disallowed_role(str(role), allowed_roles)
            failures += 1

    if failures:
        raise SystemExit(2)


def _detect_installation() -> tuple[str, bool, str]:
    version = get_version()
    if version == "unknown":
        return version, False, "unknown_version"
    try:
        dist = metadata.distribution(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return version, False, "no_metadata"
    direct_url = dist.read_text("direct_url.json")
    if direct_url:
        try:
            data = json.loads(direct_url)
        except json.JSONDecodeError:
            return version, False, "direct_url_invalid"
        dir_info = data.get("dir_info", {}) if isinstance(data, dict) else {}
        if isinstance(dir_info, dict) and dir_info.get("editable") is True:
            return version, False, "editable"
        url = data.get("url")
        if isinstance(url, str) and url.startswith("file:"):
            return version, False, "file_url"
    return version, True, "pinned"


def _enforce_tool_policy() -> int:
    strict = os.environ.get("CI", "").lower() == "true"
    policy = _load_agents_policy(strict=strict)
    if not policy:
        return 0

    require_pinned = policy.get("require_pinned_tool")
    min_version = policy.get("min_tool_version")
    max_version = policy.get("max_tool_version")

    if require_pinned is not None and not isinstance(require_pinned, bool):
        raise ParseError(ROOT / "AGENTS.md", "require_pinned_tool must be boolean")
    if min_version is not None and not isinstance(min_version, str):
        raise ParseError(ROOT / "AGENTS.md", "min_tool_version must be a string")
    if max_version is not None and not isinstance(max_version, str):
        raise ParseError(ROOT / "AGENTS.md", "max_tool_version must be a string")

    installed_version, pinned, pin_reason = _detect_installation()

    if require_pinned and not pinned:
        print(
            f"policy requires pinned agent-governance install: detected {pin_reason}",
            file=sys.stderr,
        )
        return 2

    if min_version or max_version:
        try:
            current = Version(installed_version)
        except InvalidVersion as exc:
            raise ParseError(ROOT / "AGENTS.md", f"invalid installed version: {exc}")
        if min_version:
            try:
                minimum = Version(min_version)
            except InvalidVersion as exc:
                raise ParseError(
                    ROOT / "AGENTS.md", f"invalid min_tool_version: {exc}"
                )
            if current < minimum:
                print(
                    f"installed version {current} < min_tool_version {minimum}",
                    file=sys.stderr,
                )
                return 2
        if max_version:
            try:
                maximum = Version(max_version)
            except InvalidVersion as exc:
                raise ParseError(
                    ROOT / "AGENTS.md", f"invalid max_tool_version: {exc}"
                )
            if current > maximum:
                print(
                    f"installed version {current} > max_tool_version {maximum}",
                    file=sys.stderr,
                )
                return 2

    return 0


def _render_policy_block(
    allowed_roles: list[str],
    min_tool_version: str | None,
    max_tool_version: str | None,
    require_pinned_tool: bool | None,
) -> str:
    lines = ["policy_schema_version: 1"]
    if min_tool_version:
        lines.append(f"min_tool_version: {min_tool_version}")
    if max_tool_version:
        lines.append(f"max_tool_version: {max_tool_version}")
    if require_pinned_tool is not None:
        flag = "true" if require_pinned_tool else "false"
        lines.append(f"require_pinned_tool: {flag}")
    lines.append("allowed_roles:")
    for role in sorted(allowed_roles):
        lines.append(f"  - {role}")
    return "\n".join(lines + [""])


def _find_policy_block(lines: list[str]) -> tuple[int, int] | None:
    fenced_starts = [idx for idx, line in enumerate(lines) if line.strip().startswith("```yaml")]
    if fenced_starts:
        if len(fenced_starts) > 1:
            raise ParseError(ROOT / "AGENTS.md", "multiple policy blocks found")
        start = fenced_starts[0]
        end = None
        for idx in range(start + 1, len(lines)):
            if lines[idx].strip() == "```":
                end = idx
                break
        if end is None:
            raise ParseError(ROOT / "AGENTS.md", "unterminated policy block")
        for idx, line in enumerate(lines):
            if start <= idx <= end:
                continue
            if line.lstrip().startswith("policy_schema_version:"):
                raise ParseError(ROOT / "AGENTS.md", "multiple policy blocks found")
        return start, end

    starts = [
        idx
        for idx, line in enumerate(lines)
        if line.lstrip().startswith("policy_schema_version:")
    ]
    if not starts:
        return None
    if len(starts) > 1:
        raise ParseError(ROOT / "AGENTS.md", "multiple policy blocks found")
    start = starts[0]
    start_indent = len(lines[start]) - len(lines[start].lstrip())
    end = start
    for idx in range(start + 1, len(lines)):
        line = lines[idx]
        if not line.strip():
            break
        if line.strip() == MANAGED_BLOCK_END:
            break
        if re.match(r"^#{1,6}\s", line.lstrip()):
            break
        line_indent = len(line) - len(line.lstrip())
        if line_indent < start_indent:
            break
        end = idx
    return start, end


def _parse_allowed_roles(raw: str) -> list[str]:
    roles = [item.strip() for item in raw.split(",") if item.strip()]
    if not roles:
        raise ParseError(ROOT / "AGENTS.md", "no roles selected")
    known = {entry["name"] for entry in CANONICAL_ROLES}
    unknown = sorted(set(roles) - known)
    if unknown:
        raise ParseError(
            ROOT / "AGENTS.md",
            f"unknown roles: {', '.join(unknown)}",
        )
    return roles


def _interactive_role_selection() -> list[str]:
    if not sys.stdin.isatty():
        raise ParseError(
            ROOT / "AGENTS.md",
            "interactive selection requires a TTY; use --allow",
        )
    print("Available roles:")
    for idx, entry in enumerate(CANONICAL_ROLES, start=1):
        print(f"{idx}. {entry['name']} — {entry['purpose']}")
    selection = input("Select roles (comma-separated numbers or 'all'): ").strip()
    if not selection:
        raise ParseError(ROOT / "AGENTS.md", "no roles selected")
    if selection.lower() == "all":
        return [entry["name"] for entry in CANONICAL_ROLES]
    choices = []
    for item in selection.split(","):
        item = item.strip()
        if not item:
            continue
        if not item.isdigit():
            raise ParseError(ROOT / "AGENTS.md", f"invalid selection: {item}")
        choices.append(int(item))
    roles = []
    for idx in choices:
        if idx < 1 or idx > len(CANONICAL_ROLES):
            raise ParseError(ROOT / "AGENTS.md", f"invalid selection: {idx}")
        roles.append(CANONICAL_ROLES[idx - 1]["name"])
    if not roles:
        raise ParseError(ROOT / "AGENTS.md", "no roles selected")
    return roles


MANAGED_BLOCK_BEGIN = "<!-- AGENTCTL:BEGIN -->"
MANAGED_BLOCK_END = "<!-- AGENTCTL:END -->"

MANAGED_SECTIONS = [
    (
        "## agent init behavior",
        [
            "- init is evidence-only (no LLM)",
            "- ignore: .venv/, node_modules/, .git/",
        ],
    ),
]


def _render_managed_sections() -> list[str]:
    lines: list[str] = []
    for heading, items in MANAGED_SECTIONS:
        if lines:
            lines.append("")
        lines.append(heading)
        lines.extend(items)
    return lines


def _find_managed_block(lines: list[str]) -> tuple[int, int] | None:
    begins = [idx for idx, line in enumerate(lines) if line.strip() == MANAGED_BLOCK_BEGIN]
    ends = [idx for idx, line in enumerate(lines) if line.strip() == MANAGED_BLOCK_END]
    if not begins and not ends:
        return None
    if len(begins) != 1 or len(ends) != 1:
        raise ParseError(ROOT / "AGENTS.md", "multiple managed policy blocks found")
    start = begins[0]
    end = ends[0]
    if start > end:
        raise ParseError(ROOT / "AGENTS.md", "managed policy block is malformed")
    return start, end


def _find_section(lines: list[str], heading: str) -> tuple[int, int] | None:
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            start = idx
            end = len(lines) - 1
            for jdx in range(idx + 1, len(lines)):
                if re.match(r"^#{1,6}\s", lines[jdx].lstrip()):
                    end = jdx - 1
                    break
            return start, end
    return None


def _insert_section_after(
    lines: list[str], heading: str, body: list[str], after_idx: int
) -> list[str]:
    section = [heading] + body
    insert_at = after_idx + 1
    if after_idx >= 0 and lines[after_idx].strip():
        section = [""] + section
    if insert_at < len(lines) and lines[insert_at].strip():
        section = section + [""]
    return lines[:insert_at] + section + lines[insert_at:]


def _replace_or_insert_section(
    lines: list[str], heading: str, body: list[str], after_idx: int
) -> list[str]:
    section = [heading] + body
    found = _find_section(lines, heading)
    if found:
        start, end = found
        tail = lines[end + 1 :]
        if tail and tail[0].strip() and re.match(r"^#{1,6}\s", tail[0].lstrip()):
            section = section + [""]
        return lines[:start] + section + tail
    return _insert_section_after(lines, heading, body, after_idx)


def _ensure_notes_section(lines: list[str], after_idx: int) -> list[str]:
    if _find_section(lines, "## Notes") is not None:
        return lines
    return _insert_section_after(lines, "## Notes", ["- Add human context here."], after_idx)


def cmd_bootstrap(
    allow: str | None,
    write: bool,
    min_tool_version: str | None,
    max_tool_version: str | None,
    require_pinned_tool: bool | None,
) -> int:
    try:
        allowed_roles = _parse_allowed_roles(allow) if allow else _interactive_role_selection()
    except ParseError as exc:
        report = render_error_report(ROOT, exc.path, exc.message)
        print(report, end="")
        return 2

    policy_block = _render_policy_block(
        allowed_roles,
        min_tool_version,
        max_tool_version,
        require_pinned_tool,
    )
    managed_block = [MANAGED_BLOCK_BEGIN, *policy_block.splitlines(), MANAGED_BLOCK_END]

    target = ROOT / "AGENTS.md"
    if target.exists():
        lines = target.read_text().splitlines()
        try:
            managed_range = _find_managed_block(lines)
        except ParseError as exc:
            report = render_error_report(ROOT, exc.path, exc.message)
            print(report, end="")
            return 2
        if managed_range is not None:
            start, end = managed_range
            lines = lines[:start] + managed_block + lines[end + 1 :]
        else:
            try:
                block_range = _find_policy_block(lines)
            except ParseError as exc:
                report = render_error_report(ROOT, exc.path, exc.message)
                print(report, end="")
                return 2
            if block_range is not None:
                start, end = block_range
                lines = lines[:start] + managed_block + lines[end + 1 :]
            else:
                while lines and not lines[0].strip():
                    lines.pop(0)
                lines = managed_block + ([""] + lines if lines else [])
    else:
        lines = managed_block[:]
    managed_range = _find_managed_block(lines)
    managed_end = managed_range[1] if managed_range else -1
    for heading, items in MANAGED_SECTIONS:
        lines = _replace_or_insert_section(lines, heading, items, managed_end)
    agent_section = _find_section(lines, "## agent init behavior")
    notes_after = agent_section[1] if agent_section else managed_end
    lines = _ensure_notes_section(lines, notes_after)
    content = "\n".join(lines) + "\n"
    if not write:
        print(content)
        return 0
    target.write_text(content)
    return 0


def load_schema(name: str) -> dict:
    try:
        schema_path = resources.files("agent_governance.contracts").joinpath(name)
        with schema_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        pass
    if os.environ.get("AGENT_GOVERNANCE_SCHEMA_OVERRIDE") == "1":
        with open(CONTRACTS / name, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"schema not found: {name}")


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def write_yaml(path, data):
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug


def tool_version() -> str:
    return get_version()


def get_repo_context():
    try:
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=ROOT,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        commit = commit.decode().strip()
    except Exception:
        branch = "unknown"
        commit = "unknown"
    return branch, commit


def load_repo_profile() -> dict[str, object] | None:
    profile_path = ROOT / "agents" / "repo_profile.yaml"
    if not profile_path.exists():
        return None
    data = load_yaml(profile_path)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SystemExit("repo_profile.yaml must be a YAML mapping")
    return data


def load_repo_policy_update_check() -> str | None:
    profile_path = ROOT / "agents" / "repo_profile.yaml"
    if not profile_path.exists():
        return None
    profile = load_yaml(profile_path) or {}
    update_check = profile.get("update_check")
    if isinstance(update_check, str):
        return update_check
    return None


def validate_packet(packet_path, schema_name):
    schema = load_schema(schema_name)
    data = load_yaml(packet_path)
    validate(instance=data, schema=schema)


def cmd_validate(kind, files):
    if kind == "task":
        schema = "task_packet.schema.json"
    elif kind == "output":
        schema = "output_packet.schema.json"
    else:
        raise ValueError("kind must be 'task' or 'output'")

    if kind == "task":
        try:
            allowed_roles = load_allowed_roles()
        except ParseError as exc:
            report = render_error_report(ROOT, exc.path, exc.message)
            print(report, end="")
            raise SystemExit(2)
    else:
        allowed_roles = []

    failures = 0
    for file_path in files:
        try:
            validate_packet(file_path, schema)
        except ValidationError as e:
            print(f"{kind} packet INVALID: {file_path}")
            print(e.message)
            failures += 1
            continue

        if kind == "task":
            data = load_yaml(file_path) or {}
            role = data.get("role")
            if role not in allowed_roles:
                _report_disallowed_role(str(role), allowed_roles)
                failures += 1
                continue

        print(f"{kind} packet valid: {file_path}")

    if failures:
        raise SystemExit(2)


def load_task_template():
    template_path = TEMPLATES / "task.yaml"
    if template_path.exists():
        return load_yaml(template_path)
    return {
        "id": "",
        "title": "",
        "role": "",
        "goal": "TBD",
        "repo_context": {"branch": "unknown", "commit": "unknown", "paths": []},
        "inputs": [],
        "constraints": {"allowed_write_paths": [], "forbidden_actions": []},
        "deliverables": ["diff", "logs", "commands"],
        "stop_conditions": ["TBD"],
    }


def cmd_new_task(role, title):
    try:
        allowed_roles = load_allowed_roles()
    except ParseError as exc:
        report = render_error_report(ROOT, exc.path, exc.message)
        print(report, end="")
        raise SystemExit(2)
    if role not in allowed_roles:
        _fail_disallowed_role(role, allowed_roles)

    ensure_dir(REPORTS_TASKS)
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    slug = slugify(title)
    task_id = f"{now}_{slug}" if slug else now

    task = load_task_template()
    task["id"] = task_id
    task["title"] = title
    task["role"] = role

    repo_context = task.get("repo_context") or {}
    branch, commit = get_repo_context()
    repo_context.setdefault("branch", branch)
    repo_context.setdefault("commit", commit)
    task["repo_context"] = repo_context

    output_path = REPORTS_TASKS / f"{task_id}.task.yaml"
    write_yaml(output_path, task)
    print(str(output_path))


def cmd_log(run_id, task_file, append_file):
    ensure_dir(LOGS_AGENTS)
    output_path = LOGS_AGENTS / f"{run_id}.log"
    timestamp = datetime.utcnow().isoformat() + "Z"
    task_packet = load_yaml(task_file) or {}
    task_id = task_packet.get("id", "unknown")
    role = task_packet.get("role", "unknown")

    with open(output_path, "a") as out:
        out.write("---\n")
        out.write(f"task_id: {task_id}\n")
        out.write(f"role: {role}\n")
        out.write(f"run_id: {run_id}\n")
        out.write(f"timestamp: {timestamp}\n")
        out.write("---\n")
        with open(append_file, "r") as src:
            content = src.read()
            out.write(content)
            if content and not content.endswith("\n"):
                out.write("\n")

    print(str(output_path))


def run_gate_command(name, command, run_dir, cwd):
    if isinstance(command, str):
        command_display = command
        completed = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            text=True,
            capture_output=True,
        )
    else:
        command_display = " ".join(command)
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                shell=False,
                text=True,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            stdout_path = run_dir / f"{name}.stdout.log"
            stderr_path = run_dir / f"{name}.stderr.log"
            stdout_path.write_text("")
            stderr_path.write_text(str(exc))
            missing = exc.filename or (command[0] if command else "unknown")
            return {
                "name": name,
                "command": command_display,
                "returncode": 127,
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
                "stdout_content": "",
                "stderr_content": str(exc),
                "reason": f"tool missing: {missing}",
            }
    stdout_path = run_dir / f"{name}.stdout.log"
    stderr_path = run_dir / f"{name}.stderr.log"
    stdout_path.write_text(completed.stdout)
    stderr_path.write_text(completed.stderr)
    return {
        "name": name,
        "command": command_display,
        "returncode": completed.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "stdout_content": completed.stdout,
        "stderr_content": completed.stderr,
    }


def _validate_repo_profile(profile: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    version = profile.get("profile_schema_version")
    if not isinstance(version, int):
        raise SystemExit("repo_profile.yaml missing profile_schema_version")
    gate_pr = profile.get("gate_pr")
    if not isinstance(gate_pr, dict):
        raise SystemExit("repo_profile.yaml missing gate_pr")
    steps = gate_pr.get("steps")
    if not isinstance(steps, list) or not all(isinstance(item, str) for item in steps):
        raise SystemExit("repo_profile.yaml missing gate_pr.steps")
    return gate_pr, steps


def _normalize_verify_commands(raw: object) -> list[dict[str, object]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise SystemExit("verify_commands must be a list")
    normalized: list[dict[str, object]] = []
    for idx, item in enumerate(raw):
        name = None
        cwd = "."
        command = None
        if isinstance(item, dict):
            name = item.get("name")
            cwd = item.get("cwd", ".")
            command = item.get("command")
        elif isinstance(item, str):
            command = shlex.split(item)
        else:
            raise SystemExit("verify_commands entries must be dict or string")
        if isinstance(command, str):
            command = shlex.split(command)
        if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
            raise SystemExit("verify_commands entries must include a command list")
        if command:
            tool = command[0]
            if tool == "python":
                if shutil.which("python3"):
                    command = ["python3", *command[1:]]
            elif tool == "python3":
                if not shutil.which("python3") and shutil.which("python"):
                    command = ["python", *command[1:]]
        normalized.append(
            {
                "name": name or f"verify_{idx + 1}",
                "command": command,
                "cwd": cwd,
            }
        )
    deduped: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    for item in normalized:
        key = tuple(item.get("command", []))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _build_gate_plan(
    overlay: dict[str, object] | None, profile: dict[str, object] | None
) -> dict[str, object] | None:
    if profile is None:
        if overlay is None:
            return None
        return {
            "verify_commands": _normalize_verify_commands(overlay.get("verify_commands", [])),
            "risk_paths": overlay.get("risk_paths", []),
        }

    gate_pr, steps = _validate_repo_profile(profile)
    verify_commands: list[dict[str, object]] = []
    if "verify" in steps:
        if "verify_commands" in gate_pr:
            verify_commands = _normalize_verify_commands(gate_pr.get("verify_commands"))
        elif overlay is not None:
            verify_commands = _normalize_verify_commands(overlay.get("verify_commands", []))
        else:
            return None
    risk_paths = gate_pr.get("risk_paths")
    if risk_paths is None:
        risk_paths = overlay.get("risk_paths", []) if overlay else []
    return {"verify_commands": verify_commands, "risk_paths": risk_paths}


def cmd_gate_pr():
    profile = load_repo_profile()
    overlay = _load_init_overlay(ROOT)
    if overlay is None:
        raise SystemExit("missing init overlay; run agentctl init --write")
    plan = _build_gate_plan(overlay, profile)
    if plan is None:
        raise SystemExit("missing init overlay; run agentctl init --write")
    verify_commands = plan.get("verify_commands", [])
    risk_paths = plan.get("risk_paths", [])

    _validate_task_roles_for_gate()

    ensure_dir(REPORTS_GATES)
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = REPORTS_GATES / now
    ensure_dir(run_dir)

    results = []
    for item in verify_commands:
        command = item.get("command", [])
        name = item.get("name") or "verify"
        cwd = item.get("cwd", ".")
        cwd_path = ROOT / cwd if isinstance(cwd, str) else ROOT
        result = run_gate_command(name, command, run_dir, cwd_path)
        results.append(result)
        if result.get("reason", "").startswith("tool missing"):
            break

    report_path = REPORTS_GATES / f"{now}.md"
    failed = [r for r in results if r["returncode"] != 0]

    lines = []
    lines.append(f"# Gate Report {now}\n")
    if risk_paths:
        lines.append("## Risk paths")
        for path in risk_paths:
            lines.append(f"- {path}")
        lines.append("")
    for result in results:
        status = "PASS" if result["returncode"] == 0 else "FAIL"
        lines.append(f"## {result['name']} — {status}")
        lines.append(f"- command: `{result['command']}`")
        lines.append(f"- stdout: {result['stdout']}")
        lines.append(f"- stderr: {result['stderr']}\n")
        if result.get("reason"):
            lines.append(f"- reason: {result['reason']}\n")
    summary = "PASS" if not failed else "FAIL"
    lines.append(f"## Summary — {summary}")
    lines.append(f"- total: {len(results)}")
    lines.append(f"- failed: {len(failed)}")
    report_path.write_text("\n".join(lines) + "\n")

    if failed:
        raise SystemExit(1)
    print(str(report_path))


def _load_init_overlay(root: Path) -> dict[str, object] | None:
    overlay_path = root / ".agents" / "generated" / "AGENTS.repo.overlay.yaml"
    if not overlay_path.exists():
        return None
    try:
        return load_yaml(overlay_path) or {}
    except Exception:
        return None


def _print_gate_plan(plan: dict[str, object] | None) -> None:
    print("## Gate plan")
    if not plan:
        print("- init overlay not found; no plan available")
        print("")
        return
    verify = plan.get("verify_commands", [])
    risk_paths = plan.get("risk_paths", [])
    if not verify:
        print("- verify_commands: none")
    else:
        print("- verify_commands:")
        for item in verify:
            cmd = " ".join(item.get("command", []))
            cwd = item.get("cwd", ".")
            print(f"  - {cmd} (cwd: {cwd})")
    if risk_paths:
        print("- risk_paths:")
        for path in risk_paths:
            print(f"  - {path}")
    print("")


def _check_tools_available(plan: dict[str, object] | None) -> None:
    print("## Tool availability")
    if not plan:
        print("- init overlay missing; tool checks skipped")
        print("")
        return
    verify = plan.get("verify_commands", [])
    if not verify:
        print("- no verify commands to check")
        print("")
        return
    for item in verify:
        command = item.get("command", [])
        if not command:
            print("- <empty command>: skipped")
            continue
        tool = command[0]
        available = shutil.which(tool) is not None
        status = "ok" if available else "missing"
        print(f"- {tool}: {status}")
    print("")


def cmd_gate_pr_dry_run() -> int:
    print("# Gate Dry Run")
    print("")
    try:
        agents_status, _template = check_agents_md(
            ROOT, signals=None, facts=None, strict=True
        )
    except Exception as exc:
        if hasattr(exc, "path") and hasattr(exc, "message"):
            report = render_error_report(ROOT, exc.path, exc.message)
            print(report, end="")
            return 2
        print(f"internal error: {exc}", file=sys.stderr)
        return 1

    print("## AGENTS.md status")
    print(f"- status: {agents_status['status']}")
    for detail in agents_status.get("details", []):
        print(f"- {detail}")
    print("")

    profile = load_repo_profile()
    overlay = _load_init_overlay(ROOT)
    plan = _build_gate_plan(overlay, profile)
    _print_gate_plan(plan)
    _check_tools_available(plan)
    return 0


def cmd_ops() -> int:
    lines = [
        "# Agent Governance Ops Contract",
        "",
        "## Recommended install method",
        "- Use a pinned version: agent-governance==<version>",
        "- Prefer pipx for global CLI use; use a venv for project-local installs",
        "",
        "## Pinning rule",
        "- Always install with an explicit version pin",
        "- CI must install the pinned version and run gate checks with it",
        "",
        "## Rollback one-liner",
        "- pipx: pipx install agent-governance==<prev_version> --force",
        "- venv: pip install --force-reinstall agent-governance==<prev_version>",
        "",
        "## Verify version",
        "- agentctl --version",
        "",
        "## Install commands",
        "- pipx: pipx install agent-governance==<version>",
        "- venv: pip install agent-governance==<version>",
        "",
        "## CI",
        "- Install pinned version (pipx or venv) before running gate checks",
        "- Run: agentctl gate pr",
        "",
    ]
    print("\n".join(lines))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agentctl",
        description=(
            "Agent governance CLI (init, gate, validate, ops guidance). "
            "Policy enforcement is driven by AGENTS.md."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {tool_version()}",
    )
    parser.add_argument(
        "--update-check",
        choices=["auto", "on", "off", "verbose"],
        default="auto",
        help="Enable update checks (auto|on|off|verbose)",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    new_task = subparsers.add_parser("new-task", help="Create a task packet")
    new_task.add_argument("--role", required=True, help="Role for the task")
    new_task.add_argument("--title", required=True, help="Task title")

    validate_cmd = subparsers.add_parser("validate", help="Validate a packet")
    validate_cmd.add_argument("kind", choices=["task", "output"])
    validate_cmd.add_argument("files", nargs="+")

    log_cmd = subparsers.add_parser("log", help="Append to agent run log")
    log_cmd.add_argument("--run-id", required=True)
    log_cmd.add_argument("--task", required=True, help="Task packet file")
    log_cmd.add_argument("--append", required=True, help="Text file to append")

    gate_cmd = subparsers.add_parser(
        "gate",
        help="Run repo gates",
        description=(
            "Run PR gate checks using the init overlay.\n"
            "Optional: agents/repo_profile.yaml can constrain the gate steps.\n"
            "Use --dry-run to validate AGENTS.md and print the planned checks."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    gate_cmd.add_argument("kind", choices=["pr"])
    gate_cmd.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate AGENTS.md and show planned gates",
    )

    subparsers.add_parser("ops", help="Print install/pin/rollback guidance")
    subparsers.add_parser("doctor", help="Alias for ops guidance")

    bootstrap_cmd = subparsers.add_parser(
        "bootstrap",
        help="Author AGENTS.md policy block from canonical roles",
    )
    bootstrap_cmd.add_argument(
        "--allow",
        help="Comma-separated role names (non-interactive)",
    )
    bootstrap_cmd.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write AGENTS.md (default is preview only)",
    )
    bootstrap_cmd.add_argument("--min-tool-version")
    bootstrap_cmd.add_argument("--max-tool-version")
    bootstrap_cmd.add_argument(
        "--require-pinned-tool",
        action="store_true",
        default=None,
        help="Require pinned (non-editable) installs",
    )

    init_description = (
        "Deterministic repo introspection (no LLM, evidence-only).\n"
        "When --write is set, writes:\n"
        "  - .agents/generated/AGENTS.repo.overlay.yaml\n"
        "  - .agents/generated/init_report.md\n"
        "  - .agents/generated/init_facts.json\n"
        "  - agents/repo_profile.yaml (if missing)\n"
        "Default out dir: .agents/generated\n"
        "If .gitignore exists, append one line for the out dir. Otherwise no change.\n"
        "Policy enforcement uses AGENTS.md (min/max tool version, pinned installs).\n"
        "Exit codes:\n"
        "  0  success (including dry-run)\n"
        "  nonzero  parse errors or write failures\n"
        "\n"
        "Examples:\n"
        "  agentctl init\n"
        "  agentctl init --write --out-dir .agents/custom"
    )
    init_cmd = subparsers.add_parser(
        "init",
        help="Generate a repo-specific policy overlay",
        description=init_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    init_cmd.add_argument("--write", action="store_true", default=False)
    init_cmd.add_argument("--out-dir", default=".agents/generated")
    init_cmd.add_argument("--force", action="store_true", default=False)
    init_cmd.add_argument(
        "--print-agents-template",
        action="store_true",
        default=False,
        help="Print AGENTS.md starter template when missing",
    )
    init_cmd.add_argument(
        "--strict",
        action="store_true",
        default=None,
        help="Fail on invalid AGENTS.md (default in CI)",
    )
    init_cmd.add_argument(
        "--no-strict",
        action="store_true",
        default=None,
        help="Warn on invalid AGENTS.md",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    env = dict(os.environ)
    env["AGENT_GOVERNANCE_ROOT"] = str(ROOT)

    if args.cmd == "new-task":
        mode = resolve_mode(args.update_check, env)
        policy = load_repo_policy_update_check()
        try:
            maybe_check(ROOT, mode, env, policy)
        except Exception:
            if mode == "verbose":
                print("update check failed", file=sys.stderr)
        cmd_new_task(args.role, args.title)
    elif args.cmd == "validate":
        mode = resolve_mode(args.update_check, env)
        policy = load_repo_policy_update_check()
        try:
            maybe_check(ROOT, mode, env, policy)
        except Exception:
            if mode == "verbose":
                print("update check failed", file=sys.stderr)
        cmd_validate(args.kind, args.files)
    elif args.cmd == "log":
        mode = resolve_mode(args.update_check, env)
        policy = load_repo_policy_update_check()
        try:
            maybe_check(ROOT, mode, env, policy)
        except Exception:
            if mode == "verbose":
                print("update check failed", file=sys.stderr)
        cmd_log(args.run_id, args.task, args.append)
    elif args.cmd == "gate":
        if args.kind != "pr":
            raise SystemExit("only 'pr' is supported")
        if args.dry_run:
            raise SystemExit(cmd_gate_pr_dry_run())
        mode = resolve_mode(args.update_check, env)
        policy = load_repo_policy_update_check()
        try:
            maybe_check(ROOT, mode, env, policy)
        except Exception:
            if mode == "verbose":
                print("update check failed", file=sys.stderr)
        try:
            policy_code = _enforce_tool_policy()
        except ParseError as exc:
            report = render_error_report(ROOT, exc.path, exc.message)
            print(report, end="")
            raise SystemExit(2)
        if policy_code != 0:
            raise SystemExit(policy_code)
        cmd_gate_pr()
    elif args.cmd == "init":
        mode = resolve_mode(args.update_check, env)
        policy = load_repo_policy_update_check()
        try:
            maybe_check(ROOT, mode, env, policy)
        except Exception:
            if mode == "verbose":
                print("update check failed", file=sys.stderr)
        try:
            policy_code = _enforce_tool_policy()
        except ParseError as exc:
            report = render_error_report(ROOT, exc.path, exc.message)
            print(report, end="")
            raise SystemExit(2)
        if policy_code != 0:
            raise SystemExit(policy_code)
        strict = False
        if os.environ.get("CI", "").lower() == "true":
            strict = True
        if args.strict is True:
            strict = True
        if args.no_strict is True:
            strict = False
        code = run_init(
            Path.cwd(),
            write=args.write,
            out_dir=args.out_dir,
            force=args.force,
            print_agents_template=args.print_agents_template,
            strict=strict,
        )
        raise SystemExit(code)
    elif args.cmd in ["ops", "doctor"]:
        try:
            policy_code = _enforce_tool_policy()
        except ParseError as exc:
            report = render_error_report(ROOT, exc.path, exc.message)
            print(report, end="")
            raise SystemExit(2)
        if policy_code != 0:
            raise SystemExit(policy_code)
        raise SystemExit(cmd_ops())
    elif args.cmd == "bootstrap":
        raise SystemExit(
            cmd_bootstrap(
                args.allow,
                args.write,
                args.min_tool_version,
                args.max_tool_version,
                args.require_pinned_tool,
            )
        )
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
