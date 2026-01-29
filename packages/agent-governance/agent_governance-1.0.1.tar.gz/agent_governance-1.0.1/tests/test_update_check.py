from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_governance import update_check


def test_compare_versions_semver() -> None:
    assert update_check.compare_versions("1.0.0", "1.0.1") == 1
    assert update_check.compare_versions("1.0.0", "1.0.0") == 0
    assert update_check.compare_versions("1.0.0", "1.0.1rc1") == 0


def test_should_check_ttl(tmp_path: Path) -> None:
    env = {"AGENT_GOVERNANCE_ROOT": str(tmp_path)}
    installed_version, _source = update_check.get_installed_version(env)
    now = datetime.now(timezone.utc)
    cache = update_check.CacheEntry(
        checked_at_utc=update_check.format_time(now),
        installed_version=installed_version,
        latest_version="1.0.1",
        source="pypi",
        etag=None,
        last_error=None,
    )
    should_run, reason = update_check.should_check(
        now, env, cache, "auto", False, True
    )
    assert should_run is False
    assert reason == "cache fresh"

    old = now - timedelta(hours=7)
    cache = update_check.CacheEntry(
        checked_at_utc=update_check.format_time(old),
        installed_version=installed_version,
        latest_version="1.0.1",
        source="pypi",
        etag=None,
        last_error="timeout",
    )
    should_run, reason = update_check.should_check(
        now, env, cache, "auto", False, True
    )
    assert should_run is True
    assert reason == "cache stale"


def test_ci_suppression() -> None:
    now = datetime.now(timezone.utc)
    should_run, reason = update_check.should_check(
        now, {"CI": "true"}, None, "auto", True, True
    )
    assert should_run is False
    assert reason == "ci auto disabled"


def test_banner_formatting(monkeypatch, tmp_path: Path) -> None:
    env = {
        "XDG_CACHE_HOME": str(tmp_path),
        "AGENT_GOVERNANCE_ROOT": str(tmp_path),
    }

    def fake_fetch(cache, installed):
        return "1.2.0", None, None

    def fake_installed(env):
        return "1.0.0", "pyproject"

    monkeypatch.setattr(update_check, "fetch_latest", fake_fetch)
    monkeypatch.setattr(update_check, "get_installed_version", fake_installed)

    buffer = io.StringIO()
    update_check.maybe_check(Path("."), "on", env, None, out=buffer)
    assert (
        buffer.getvalue().strip()
        == "agent-governance update available: installed 1.0.0, latest 1.2.0 (source: pypi)."
    )


def test_fetch_latest_parses_response(monkeypatch) -> None:
    class FakeResponse:
        status = 200

        def __init__(self):
            self.headers = {"ETag": "etag"}

        def read(self):
            return b'{"info": {"version": "2.0.0"}}'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout=0):
        return FakeResponse()

    monkeypatch.setattr(update_check.urllib.request, "urlopen", fake_urlopen)
    latest, etag, error = update_check.fetch_latest(None, "1.0.0")
    assert latest == "2.0.0"
    assert etag == "etag"
    assert error is None
