#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

from agent_governance import PACKAGE_NAME, __version__

try:
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

DEFAULT_TTL_HOURS = 24
ERROR_TTL_HOURS = 6
PYPI_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"


@dataclass
class CacheEntry:
    checked_at_utc: str
    installed_version: str
    latest_version: str
    source: str
    etag: str | None = None
    last_error: str | None = None


def resolve_mode(cli_mode: str | None, env: dict[str, str]) -> str:
    env_mode = env.get("AGENT_UPDATE_CHECK")
    if env_mode:
        return env_mode
    return cli_mode or "auto"


def is_ci(env: dict[str, str]) -> bool:
    return env.get("CI", "").lower() == "true"


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_time(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_cache(cache_path: Path) -> CacheEntry | None:
    try:
        if not cache_path.exists():
            return None
        data = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return CacheEntry(
        checked_at_utc=data.get("checked_at_utc", ""),
        installed_version=data.get("installed_version", ""),
        latest_version=data.get("latest_version", ""),
        source=data.get("source", ""),
        etag=data.get("etag"),
        last_error=data.get("last_error"),
    )


def write_cache(cache_path: Path, entry: CacheEntry) -> None:
    payload = {
        "checked_at_utc": entry.checked_at_utc,
        "installed_version": entry.installed_version,
        "latest_version": entry.latest_version,
        "source": entry.source,
        "etag": entry.etag,
        "last_error": entry.last_error,
    }
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    except OSError:
        try:
            fallback = fallback_cache_path()
            fallback.parent.mkdir(parents=True, exist_ok=True)
            fallback.write_text(json.dumps(payload, indent=2, sort_keys=True))
        except OSError:
            return


def get_cache_path(env: dict[str, str]) -> Path:
    cache_root = env.get("XDG_CACHE_HOME")
    if cache_root:
        return Path(cache_root) / "agent_governance" / "update_check.json"
    return Path.home() / ".cache" / "agent_governance" / "update_check.json"


def fallback_cache_path() -> Path:
    return Path.home() / ".agent_governance" / "cache" / "update_check.json"


def should_check(
    now: datetime,
    env: dict[str, str],
    cache: CacheEntry | None,
    mode: str,
    ci: bool,
    interactive: bool,
) -> tuple[bool, str]:
    mode = mode or "auto"
    if mode == "off":
        return False, "mode off"
    if mode == "auto":
        if ci:
            return False, "ci auto disabled"
        if not interactive:
            return False, "non-interactive auto disabled"
    if mode == "verbose":
        if ci:
            return False, "ci verbose disabled"
        if not interactive:
            return False, "non-interactive verbose disabled"
    if mode == "on":
        return True, "forced on"

    if not cache:
        return True, "no cache"

    checked_at = parse_time(cache.checked_at_utc)
    if not checked_at:
        return True, "cache timestamp invalid"

    installed_version, _source = get_installed_version(env)
    if cache.installed_version and cache.installed_version != installed_version:
        return True, "installed version changed"

    ttl_hours = ERROR_TTL_HOURS if cache.last_error else DEFAULT_TTL_HOURS
    if now - checked_at < timedelta(hours=ttl_hours):
        return False, "cache fresh"
    return True, "cache stale"


def _source_root_from_env(env: dict[str, str]) -> Path | None:
    root = env.get("AGENT_GOVERNANCE_ROOT")
    if root:
        return Path(root).resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists() or (parent / "VERSION").exists():
            return parent
    return None


def _version_from_pyproject(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        data = tomllib.loads(pyproject.read_text())
    except tomllib.TOMLDecodeError:
        return None
    if not isinstance(data, dict):
        return None
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
    return None


def _version_from_source(root: Path) -> str | None:
    version = _version_from_pyproject(root)
    if version:
        return version
    version_path = root / "VERSION"
    if version_path.exists():
        value = version_path.read_text().strip()
        if value:
            return value
    return None


def get_installed_version(env: dict[str, str]) -> tuple[str, str]:
    try:
        return metadata.version(PACKAGE_NAME), "metadata"
    except metadata.PackageNotFoundError:
        root = _source_root_from_env(env)
        if root:
            version = _version_from_source(root)
            if version:
                return version, "source"
        return __version__, "unknown"


def compare_versions(installed: str, latest: str) -> int:
    try:
        installed_v = Version(installed)
        latest_v = Version(latest)
    except InvalidVersion:
        return 0
    if latest_v.is_prerelease and not installed_v.is_prerelease:
        return 0
    if latest_v > installed_v:
        return 1
    return 0


def fetch_latest(
    cache: CacheEntry | None, installed_version: str
) -> tuple[str | None, str | None, str | None]:
    headers = {
        "User-Agent": f"{PACKAGE_NAME}/{installed_version}",
    }
    if cache and cache.etag:
        headers["If-None-Match"] = cache.etag
    req = urllib.request.Request(PYPI_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            if resp.status == 304 and cache:
                return cache.latest_version, cache.etag, None
            payload = json.loads(resp.read().decode("utf-8"))
            latest = payload.get("info", {}).get("version")
            if not isinstance(latest, str):
                return None, None, "invalid version"
            etag = resp.headers.get("ETag")
            return latest, etag, None
    except urllib.error.HTTPError as exc:
        if exc.code == 304 and cache:
            return cache.latest_version, cache.etag, None
        return None, None, f"http error {exc.code}"
    except Exception as exc:  # pragma: no cover - network errors
        return None, None, str(exc)


def maybe_check(
    root: Path,
    mode: str,
    env: dict[str, str],
    policy: str | None,
    out: Any = sys.stderr,
) -> None:
    if policy == "off":
        if mode == "verbose":
            out.write("update check disabled by policy\n")
        return

    now = datetime.now(timezone.utc)
    cache_path = get_cache_path(env)
    cache = read_cache(cache_path)
    ci = is_ci(env)
    interactive = sys.stderr.isatty()
    should_run, reason = should_check(now, env, cache, mode, ci, interactive)
    if not should_run:
        if mode == "verbose":
            out.write(f"update check skipped: {reason}\n")
        return

    installed_version, _source = get_installed_version(env)
    latest, etag, error = fetch_latest(cache, installed_version)
    if error or not latest:
        entry = CacheEntry(
            checked_at_utc=format_time(now),
            installed_version=installed_version,
            latest_version=cache.latest_version if cache else "",
            source="pypi",
            etag=etag or (cache.etag if cache else None),
            last_error=error or "unknown error",
        )
        write_cache(cache_path, entry)
        if mode == "verbose":
            out.write(f"update check failed: {entry.last_error}\n")
        return

    entry = CacheEntry(
        checked_at_utc=format_time(now),
        installed_version=installed_version,
        latest_version=latest,
        source="pypi",
        etag=etag,
        last_error=None,
    )
    write_cache(cache_path, entry)

    if compare_versions(installed_version, latest) > 0:
        out.write(
            f"{PACKAGE_NAME} update available: installed {installed_version}, "
            f"latest {latest} (source: pypi).\n"
        )
