from __future__ import annotations

from importlib import metadata
from pathlib import Path

try:
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

PACKAGE_NAME = "agent-governance"
__version__ = "unknown"


def _version_from_pyproject() -> str | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "pyproject.toml"
        if not candidate.exists():
            continue
        try:
            data = tomllib.loads(candidate.read_text())
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
    return None


def get_version() -> str:
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return _version_from_pyproject() or __version__


__all__ = ["PACKAGE_NAME", "__version__", "get_version"]
