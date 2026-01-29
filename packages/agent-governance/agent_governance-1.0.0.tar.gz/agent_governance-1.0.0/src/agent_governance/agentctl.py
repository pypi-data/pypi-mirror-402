#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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


def load_schema(name):
    with open(CONTRACTS / name, "r") as f:
        return json.load(f)


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


def load_repo_profile():
    profile_path = ROOT / "agents" / "repo_profile.yaml"
    if not profile_path.exists():
        raise FileNotFoundError("missing agents/repo_profile.yaml")
    return load_yaml(profile_path)


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


def cmd_validate(kind, file_path):
    if kind == "task":
        schema = "task_packet.schema.json"
    elif kind == "output":
        schema = "output_packet.schema.json"
    else:
        raise ValueError("kind must be 'task' or 'output'")

    try:
        validate_packet(file_path, schema)
        print(f"{kind} packet valid: {file_path}")
    except ValidationError as e:
        print(f"{kind} packet INVALID:")
        print(e.message)
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


def run_gate_command(name, command, run_dir):
    stdout_path = run_dir / f"{name}.stdout.log"
    stderr_path = run_dir / f"{name}.stderr.log"
    completed = subprocess.run(
        command,
        cwd=ROOT,
        shell=True,
        text=True,
        capture_output=True,
    )
    stdout_path.write_text(completed.stdout)
    stderr_path.write_text(completed.stderr)
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "stdout_content": completed.stdout,
        "stderr_content": completed.stderr,
    }


def cmd_gate_pr():
    profile = load_repo_profile()
    commands = profile.get("commands", {})
    policies = profile.get("policies") or {}
    require_tests = bool(policies.get("require_tests", True))
    test_glob = policies.get("python_test_glob", "tests/test_*.py")
    required = ["test", "lint", "typecheck", "format"]
    missing = [name for name in required if not commands.get(name)]
    if missing:
        raise SystemExit(f"missing commands in repo_profile.yaml: {', '.join(missing)}")

    ensure_dir(REPORTS_GATES)
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = REPORTS_GATES / now
    ensure_dir(run_dir)

    results = []
    test_files = []
    if require_tests and test_glob:
        test_files = list(ROOT.glob(test_glob))
    for name in required:
        result = run_gate_command(name, commands[name], run_dir)
        if name == "test":
            reasons = []
            if require_tests and test_glob and not test_files:
                reasons.append(
                    f"require_tests true: no test files matched python_test_glob={test_glob}"
                )
            combined_output = f"{result['stdout_content']}\n{result['stderr_content']}"
            if require_tests and re.search(r"collected\\s+0\\s+items", combined_output):
                reasons.append("require_tests true: pytest collected 0 items")
            if reasons:
                result["returncode"] = 1
                result["reason"] = "; ".join(reasons)
        results.append(result)

    report_path = REPORTS_GATES / f"{now}.md"
    failed = [r for r in results if r["returncode"] != 0]

    lines = []
    lines.append(f"# Gate Report {now}\n")
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


def _print_gate_plan(overlay: dict[str, object] | None) -> None:
    print("## Gate plan")
    if not overlay:
        print("- init overlay not found; no plan available")
        print("")
        return
    verify = overlay.get("verify_commands", [])
    risk_paths = overlay.get("risk_paths", [])
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


def _check_tools_available(overlay: dict[str, object] | None) -> None:
    print("## Tool availability")
    if not overlay:
        print("- init overlay missing; tool checks skipped")
        print("")
        return
    verify = overlay.get("verify_commands", [])
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

    overlay = _load_init_overlay(ROOT)
    _print_gate_plan(overlay)
    _check_tools_available(overlay)
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
    validate_cmd.add_argument("file")

    log_cmd = subparsers.add_parser("log", help="Append to agent run log")
    log_cmd.add_argument("--run-id", required=True)
    log_cmd.add_argument("--task", required=True, help="Task packet file")
    log_cmd.add_argument("--append", required=True, help="Text file to append")

    gate_cmd = subparsers.add_parser(
        "gate",
        help="Run repo gates",
        description=(
            "Run PR gate checks using agents/repo_profile.yaml.\n"
            "Use --dry-run to validate AGENTS.md and print a plan without a profile."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    gate_cmd.add_argument("kind", choices=["pr"])
    gate_cmd.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate AGENTS.md and show planned gates without repo_profile.yaml",
    )

    subparsers.add_parser("ops", help="Print install/pin/rollback guidance")
    subparsers.add_parser("doctor", help="Alias for ops guidance")

    init_description = (
        "Deterministic repo introspection (no LLM, evidence-only).\n"
        "When --write is set, writes:\n"
        "  - .agents/generated/AGENTS.repo.overlay.yaml\n"
        "  - .agents/generated/init_report.md\n"
        "  - .agents/generated/init_facts.json\n"
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
        cmd_validate(args.kind, args.file)
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
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
