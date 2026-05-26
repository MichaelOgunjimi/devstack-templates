# devstack-templates

Official project templates for
[devstack-cli](https://github.com/MichaelOgunjimi/devstack-cli).

This repository contains the template manifest, backend starter code, frontend
shared client libraries, Docker Compose templates, and generated project
baseline files used by `devstack new`, `devstack add`, and `devstack update`.

The FastAPI + Next.js and FastAPI + React/Vite stacks include a starter auth
baseline: register, login, refresh tokens, password reset, email verification,
protected dashboard, and a minimal admin page using generic `user` and `admin`
roles.

## Development

Point the CLI at this checkout while working on templates:

```bash
export DEVSTACK_TEMPLATES_PATH="/path/to/devstack-templates"
devstack templates list
```

Run checks locally:

```bash
uv run --with pyyaml python scripts/validate_manifest.py
uv run --with pyyaml --with jinja2 python scripts/smoke_generate_stacks.py
uv run --project backend ruff check .
uv run --project backend pytest -q
```

Generated projects should receive stack-specific files through
`project_outputs.files` in `devstack-template.yaml`, not through hardcoded CLI
paths.
