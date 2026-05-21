"""Validate devstack-template.yaml for CI and contributors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "devstack-template.yaml"


def main() -> None:
    manifest = _load_manifest()
    services = _service_ids(manifest)
    _validate_stacks(manifest, services)
    _validate_services(manifest)


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST.exists():
        raise SystemExit("devstack-template.yaml is missing")

    data = yaml.safe_load(MANIFEST.read_text())
    if not isinstance(data, dict):
        raise SystemExit("manifest root must be a mapping")
    if data.get("manifest_version") != 1:
        raise SystemExit("manifest_version must be 1")
    return data


def _service_ids(manifest: dict[str, Any]) -> set[str]:
    services = manifest.get("services")
    if not isinstance(services, list):
        raise SystemExit("services must be a list")

    ids: set[str] = set()
    for index, service in enumerate(services):
        if not isinstance(service, dict):
            raise SystemExit(f"services[{index}] must be a mapping")
        service_id = service.get("id")
        if not isinstance(service_id, str) or not service_id:
            raise SystemExit(f"services[{index}].id must be a non-empty string")
        if service_id in ids:
            raise SystemExit(f"duplicate service id: {service_id}")
        ids.add(service_id)
    return ids


def _validate_stacks(manifest: dict[str, Any], service_ids: set[str]) -> None:
    stacks = manifest.get("stacks")
    if not isinstance(stacks, list):
        raise SystemExit("stacks must be a list")

    ids: set[str] = set()
    for index, stack in enumerate(stacks):
        if not isinstance(stack, dict):
            raise SystemExit(f"stacks[{index}] must be a mapping")

        stack_id = _required_str(stack, "id", f"stacks[{index}].id")
        if stack_id in ids:
            raise SystemExit(f"duplicate stack id: {stack_id}")
        ids.add(stack_id)

        for field in ("default_services", "optional_features"):
            values = stack.get(field, [])
            if not isinstance(values, list):
                raise SystemExit(f"stacks.{stack_id}.{field} must be a list")
            for service_id in values:
                if service_id not in service_ids:
                    raise SystemExit(
                        f"stacks.{stack_id}.{field} references unknown service {service_id}"
                    )

        templates = stack.get("templates")
        if not isinstance(templates, dict):
            raise SystemExit(f"stacks.{stack_id}.templates must be a mapping")
        for key, value in templates.items():
            if value is not None:
                _validate_existing_relative_path(value, f"stacks.{stack_id}.templates.{key}")

        project_outputs = stack.get("project_outputs", {})
        if project_outputs is None:
            project_outputs = {}
        if not isinstance(project_outputs, dict):
            raise SystemExit(f"stacks.{stack_id}.project_outputs must be a mapping")
        files = project_outputs.get("files", [])
        if not isinstance(files, list):
            raise SystemExit(f"stacks.{stack_id}.project_outputs.files must be a list")
        for file_index, file_record in enumerate(files):
            if not isinstance(file_record, dict):
                raise SystemExit(
                    f"stacks.{stack_id}.project_outputs.files[{file_index}] must be a mapping"
                )
            source = _required_str(
                file_record,
                "from",
                f"stacks.{stack_id}.project_outputs.files[{file_index}].from",
            )
            destination = _required_str(
                file_record,
                "to",
                f"stacks.{stack_id}.project_outputs.files[{file_index}].to",
            )
            _validate_existing_relative_path(
                source,
                f"stacks.{stack_id}.project_outputs.files[{file_index}].from",
            )
            _validate_relative_path(
                destination,
                f"stacks.{stack_id}.project_outputs.files[{file_index}].to",
            )


def _validate_services(manifest: dict[str, Any]) -> None:
    for service in manifest["services"]:
        service_id = service["id"]
        copy_files = service.get("copy_files", [])
        if not isinstance(copy_files, list):
            raise SystemExit(f"services.{service_id}.copy_files must be a list")
        for index, item in enumerate(copy_files):
            if not isinstance(item, dict):
                raise SystemExit(f"services.{service_id}.copy_files[{index}] must be a mapping")
            source = _required_str(item, "from", f"services.{service_id}.copy_files[{index}].from")
            destination = _required_str(item, "to", f"services.{service_id}.copy_files[{index}].to")
            _validate_existing_relative_path(
                source,
                f"services.{service_id}.copy_files[{index}].from",
            )
            _validate_relative_path(destination, f"services.{service_id}.copy_files[{index}].to")


def _required_str(record: dict[str, Any], key: str, field: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"{field} must be a non-empty string")
    return value


def _validate_existing_relative_path(value: str, field: str) -> None:
    _validate_relative_path(value, field)
    if not (ROOT / value).exists():
        raise SystemExit(f"{field} does not exist: {value}")


def _validate_relative_path(value: str, field: str) -> None:
    path = Path(value)
    if path.is_absolute():
        raise SystemExit(f"{field} must be relative")
    if ".." in path.parts:
        raise SystemExit(f"{field} must not contain '..'")


if __name__ == "__main__":
    main()
