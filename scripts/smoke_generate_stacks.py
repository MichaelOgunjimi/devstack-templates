"""Smoke-test generated project structure for every declared template stack."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "devstack-template.yaml"

GENERATED_PROJECT = "smoke-app"
PORTS = {
    "frontend": 3100,
    "backend": 3101,
    "postgres": 3102,
    "redis": 3103,
    "minio": 3104,
    "minio_console": 3105,
    "mailhog": 3106,
    "mailhog_ui": 3107,
    "elasticsearch": 3108,
}

BACKEND_REQUIRED_FILES = (
    "Dockerfile",
    "pyproject.toml",
    ".env.example",
    "main.py",
    "api/v1/router.py",
    "core/config.py",
    "core/database.py",
    "migrations/env.py",
)

FRONTEND_REQUIRED_CONTENT = {
    "fastapi-next": {
        "src/components/auth-shell.tsx": ("AuthShell", "DevStack Access"),
        "src/components/theme-toggle.tsx": ("Toggle color mode", "theme-sun"),
        "src/app/login/page.tsx": ("safeReturnTo", "returnTo"),
        "src/app/register/page.tsx": ("Create account", "AuthShell"),
        "src/app/dashboard/page.tsx": ("returnTo=/dashboard", "resendVerification"),
        "src/app/admin/page.tsx": ("returnTo=/admin", "Access denied"),
    },
    "fastapi-react": {
        "src/App.tsx": (
            "function safeReturnTo",
            "?returnTo=/dashboard",
            "?returnTo=/admin",
            "function Dashboard",
            "function Admin",
        ),
        "src/index.css": ("authShell", "sessionCard", "cardContent > .actions"),
    },
}

IGNORED_COPY_DIRS = (
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
)


def main() -> None:
    manifest = _load_manifest()
    stacks = _required_list(manifest, "stacks")
    services = _services_by_id(manifest)

    with tempfile.TemporaryDirectory(prefix="devstack-template-smoke-") as tmp:
        tmp_path = Path(tmp)
        for stack in stacks:
            _smoke_stack(stack, services, tmp_path)


def _load_manifest() -> dict[str, Any]:
    data = yaml.safe_load(MANIFEST.read_text())
    if not isinstance(data, dict):
        raise SystemExit("manifest root must be a mapping")
    return data


def _services_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    services = _required_list(manifest, "services")
    result: dict[str, dict[str, Any]] = {}
    for service in services:
        if not isinstance(service, dict):
            raise SystemExit("services entries must be mappings")
        service_id = _required_str(service, "id")
        result[service_id] = service
    return result


def _smoke_stack(
    stack: dict[str, Any],
    services_by_id: dict[str, dict[str, Any]],
    tmp_path: Path,
) -> None:
    stack_id = _required_str(stack, "id")
    project_path = tmp_path / stack_id
    project_path.mkdir()

    default_services = tuple(_string_list(stack.get("default_services", [])))
    optional_features = tuple(_string_list(stack.get("optional_features", [])))
    selected_services = (*default_services, *optional_features)
    context = _render_context(stack, default_services, optional_features)

    templates = _required_mapping(stack, "templates")
    _copy_backend_template(templates, project_path)
    _render_compose(templates, context, project_path)
    _copy_frontend_shared(templates, context, project_path)
    _render_outputs(stack, "project_outputs", context, project_path)
    _render_outputs(stack, "frontend_outputs", context, project_path / "frontend")
    _copy_service_files(selected_services, services_by_id, project_path)

    _assert_stack_shape(stack, services_by_id, project_path, selected_services)
    print(f"smoke ok: {stack_id}")


def _render_context(
    stack: dict[str, Any],
    services: tuple[str, ...],
    optional: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "project_name": GENERATED_PROJECT,
        "stack": _required_str(stack, "id"),
        "frontend": _required_str(stack, "frontend"),
        "services": services,
        "optional": optional,
        "ports": PORTS,
    }


def _copy_backend_template(templates: dict[str, Any], project_path: Path) -> None:
    backend_source = _source_path(_required_str(templates, "backend"))
    backend_target = project_path / "backend"
    shutil.copytree(backend_source, backend_target, ignore=_ignore_generated_artifacts)

    for required in BACKEND_REQUIRED_FILES:
        _assert_exists(backend_target / required, f"backend file {required}")


def _render_compose(
    templates: dict[str, Any],
    context: dict[str, Any],
    project_path: Path,
) -> None:
    compose_source = _required_str(templates, "compose")
    rendered = _render_template(compose_source, context)
    compose_target = project_path / "docker-compose.yml"
    compose_target.write_text(rendered)

    _assert_rendered(rendered, compose_source)
    if "backend:" not in rendered:
        raise SystemExit(f"{compose_source} did not render a backend service")
    if context["frontend"] and "frontend:" not in rendered:
        raise SystemExit(f"{compose_source} did not render a frontend service")


def _copy_frontend_shared(
    templates: dict[str, Any],
    context: dict[str, Any],
    project_path: Path,
) -> None:
    shared_source = templates.get("frontend_shared")
    if shared_source is None:
        return
    if not isinstance(shared_source, str):
        raise SystemExit("templates.frontend_shared must be a string when present")

    source_root = _source_path(shared_source)
    target = project_path / "frontend" / "src" / "lib"
    for source_path in source_root.rglob("*"):
        if source_path.is_dir():
            continue
        if _is_ignored_generated_artifact(source_path.name):
            continue

        relative_path = source_path.relative_to(source_root)
        if source_path.suffix == ".j2":
            destination = target / relative_path.with_suffix("")
            rendered = _render_relative_template(source_root, str(relative_path), context)
            _write_text(destination, rendered)
            _assert_rendered(rendered, str(source_path.relative_to(ROOT)))
        else:
            _copy_path(source_path, target / relative_path)

    if not any(target.rglob("*")):
        raise SystemExit(f"templates.frontend_shared copied no files: {shared_source}")


def _render_outputs(
    stack: dict[str, Any],
    key: str,
    context: dict[str, Any],
    base_target: Path,
) -> None:
    outputs = stack.get(key) or {}
    if not isinstance(outputs, dict):
        raise SystemExit(f"stacks.{context['stack']}.{key} must be a mapping")
    files = outputs.get("files", [])
    if not isinstance(files, list):
        raise SystemExit(f"stacks.{context['stack']}.{key}.files must be a list")

    for item in files:
        if not isinstance(item, dict):
            raise SystemExit(f"stacks.{context['stack']}.{key}.files entries must be mappings")
        source = _required_str(item, "from")
        destination = _required_str(item, "to")
        _render_or_copy(source, context, base_target / destination)


def _copy_service_files(
    selected_services: Iterable[str],
    services_by_id: dict[str, dict[str, Any]],
    project_path: Path,
) -> None:
    for service_id in selected_services:
        service = services_by_id[service_id]
        copy_files = service.get("copy_files", [])
        if not isinstance(copy_files, list):
            raise SystemExit(f"services.{service_id}.copy_files must be a list")
        for item in copy_files:
            if not isinstance(item, dict):
                raise SystemExit(f"services.{service_id}.copy_files entries must be mappings")
            source = _required_str(item, "from")
            destination = _required_str(item, "to")
            _copy_path(_source_path(source), project_path / destination)


def _assert_stack_shape(
    stack: dict[str, Any],
    services_by_id: dict[str, dict[str, Any]],
    project_path: Path,
    selected_services: tuple[str, ...],
) -> None:
    stack_id = _required_str(stack, "id")
    _assert_exists(project_path / "docker-compose.yml", f"{stack_id} compose output")

    for item in _manifest_files(stack, "project_outputs"):
        _assert_exists(project_path / item["to"], f"{stack_id} project output")

    for item in _manifest_files(stack, "frontend_outputs"):
        _assert_exists(project_path / "frontend" / item["to"], f"{stack_id} frontend output")

    _assert_frontend_required_content(stack_id, project_path)

    for service_id in selected_services:
        for item in _service_copy_files(service_id, services_by_id):
            _assert_exists(project_path / item["to"], f"{stack_id} service output {service_id}")


def _manifest_files(stack: dict[str, Any], key: str) -> list[dict[str, str]]:
    outputs = stack.get(key) or {}
    if not isinstance(outputs, dict):
        raise SystemExit(f"stacks.{_required_str(stack, 'id')}.{key} must be a mapping")
    files = outputs.get("files", [])
    if not isinstance(files, list):
        raise SystemExit(f"stacks.{_required_str(stack, 'id')}.{key}.files must be a list")
    return [_file_record(item, f"stacks.{_required_str(stack, 'id')}.{key}.files") for item in files]


def _service_copy_files(
    service_id: str,
    services_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    copy_files = services_by_id[service_id].get("copy_files", [])
    if not isinstance(copy_files, list):
        raise SystemExit(f"services.{service_id}.copy_files must be a list")
    return [_file_record(item, f"services.{service_id}.copy_files") for item in copy_files]


def _render_or_copy(source: str, context: dict[str, Any], target: Path) -> None:
    source_path = _source_path(source)
    if source_path.is_dir():
        _copy_path(source_path, target)
        return

    if source_path.suffix == ".j2":
        rendered = _render_template(source, context)
        _write_text(target, rendered)
        _assert_rendered(rendered, source)
        return

    _copy_path(source_path, target)


def _copy_path(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, ignore=_ignore_generated_artifacts)
    else:
        shutil.copy2(source, target)


def _render_template(source: str, context: dict[str, Any]) -> str:
    return _render_relative_template(ROOT, source, context)


def _render_relative_template(root: Path, source: str, context: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(root),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    return env.get_template(source).render(**context)


def _write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def _source_path(value: str) -> Path:
    path = ROOT / value
    if not path.exists():
        raise SystemExit(f"template source missing: {value}")
    return path


def _assert_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"{label} is missing: {path}")


def _assert_rendered(content: str, source: str) -> None:
    if "{{" in content or "{%" in content or "{#" in content:
        raise SystemExit(f"{source} rendered with unresolved Jinja syntax")


def _assert_frontend_required_content(stack_id: str, project_path: Path) -> None:
    for relative_path, expected_values in FRONTEND_REQUIRED_CONTENT.get(stack_id, {}).items():
        path = project_path / "frontend" / relative_path
        _assert_exists(path, f"{stack_id} frontend starter surface")
        content = path.read_text()
        for expected in expected_values:
            if expected not in content:
                raise SystemExit(f"{path} is missing expected starter content: {expected}")


def _file_record(value: Any, field: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise SystemExit(f"{field} entries must be mappings")
    return {"from": _required_str(value, "from"), "to": _required_str(value, "to")}


def _required_mapping(record: dict[str, Any], key: str) -> dict[str, Any]:
    value = record.get(key)
    if not isinstance(value, dict):
        raise SystemExit(f"{key} must be a mapping")
    return value


def _required_list(record: dict[str, Any], key: str) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list):
        raise SystemExit(f"{key} must be a list")
    return value


def _required_str(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"{key} must be a non-empty string")
    return value


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise SystemExit("expected a list")
    if not all(isinstance(item, str) and item for item in value):
        raise SystemExit("expected a list of non-empty strings")
    return value


def _ignore_generated_artifacts(_: str, names: list[str]) -> set[str]:
    return {name for name in names if _is_ignored_generated_artifact(name)}


def _is_ignored_generated_artifact(name: str) -> bool:
    return name in IGNORED_COPY_DIRS or name.endswith(".pyc")


if __name__ == "__main__":
    main()
