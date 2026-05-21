# Auth Dashboard Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated FastAPI + Next.js projects immediately usable with auth, dashboard, and admin starter flows.

**Architecture:** Extend the existing FastAPI auth template with generic `user`/`admin` roles, verification/reset token flows, and an admin dependency. Add CLI support for stack-declared frontend output files, then add Next.js App Router pages from the template repo.

**Tech Stack:** FastAPI, SQLModel, Redis refresh-token cache, python-jose JWTs, Next.js App Router, React, Tailwind, uv, pytest, ruff.

---

### Task 1: Backend Auth Baseline In `devstack-templates`

**Files:**
- Modify: `backend/models/user.py`
- Modify: `backend/schemas/auth.py`
- Modify: `backend/schemas/user.py`
- Modify: `backend/core/security.py`
- Modify: `backend/api/deps.py`
- Modify: `backend/api/v1/auth.py`
- Modify: `backend/services/auth.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing backend auth tests**

Add tests for registration role defaults, login, `/auth/me`, password reset, verification, and admin dependency.

Run:

```bash
uv run --project backend pytest backend/tests/test_auth.py -q
```

Expected: failures for missing schemas, routes, or role/admin behavior.

- [ ] **Step 2: Implement roles and auth schemas**

Add `role: str = "user"` to the `User` model, expose it in `UserRead`, validate register roles as `user|admin`, and add request schemas for reset, verification, and password change.

- [ ] **Step 3: Implement token helpers and service functions**

Add `create_verification_token`, `create_password_reset_token`, and service functions for registration, password reset, email verification, password changes, and user updates.

- [ ] **Step 4: Keep routes thin**

Move business logic out of `api/v1/auth.py` and call the service functions from route handlers.

- [ ] **Step 5: Add admin dependency**

Add `get_current_admin_user` and `AdminDep` in `api/deps.py`.

- [ ] **Step 6: Verify backend**

Run:

```bash
uv run --project backend ruff check .
uv run --project backend pytest -q
```

Expected: both commands pass.

### Task 2: CLI Frontend Output Support In `devstack-cli`

**Files:**
- Modify: `devstack/template_manifest.py`
- Modify: `devstack/commands/project/new/__init__.py`
- Modify: `devstack/commands/project/new/scaffolder.py`
- Modify: `tests/test_template_manifest.py`
- Modify: `tests/test_new_stack.py`

- [ ] **Step 1: Write failing manifest/scaffolder tests**

Add tests that a stack can declare frontend output files and that `devstack new` copies them after frontend scaffolding.

- [ ] **Step 2: Extend stack manifest parsing**

Add a `frontend_outputs.files` collection to `StackDefinition`.

- [ ] **Step 3: Copy frontend files after scaffold**

After `_copy_frontend_lib`, render/copy declared frontend files into the generated frontend root.

- [ ] **Step 4: Verify CLI**

Run:

```bash
uv run pytest tests/test_template_manifest.py tests/test_new_stack.py -q
uv run ruff check .
```

Expected: all selected tests and lint pass.

### Task 3: Next.js Starter Pages In `devstack-templates`

**Files:**
- Create: `frontend/app/layout.tsx.j2`
- Create: `frontend/app/page.tsx.j2`
- Create: `frontend/app/login/page.tsx`
- Create: `frontend/app/register/page.tsx`
- Create: `frontend/app/forgot-password/page.tsx`
- Create: `frontend/app/reset-password/page.tsx`
- Create: `frontend/app/verify-email/page.tsx`
- Create: `frontend/app/dashboard/page.tsx`
- Create: `frontend/app/admin/page.tsx`
- Modify: `frontend/lib/auth/client.ts.j2`
- Modify: `frontend/lib/auth/provider.tsx.j2`
- Modify: `frontend/lib/auth/types.ts`
- Modify: `devstack-template.yaml`

- [ ] **Step 1: Add auth client methods**

Expose `forgotPassword`, `resetPassword`, `verifyEmail`, `resendVerification`, and `changePassword` in the generated auth client and provider.

- [ ] **Step 2: Add generic pages**

Create simple Tailwind pages that use the auth provider. Keep them domain-neutral.

- [ ] **Step 3: Declare frontend outputs**

Add the page files to `frontend_outputs.files` for the `fastapi-next` stack.

- [ ] **Step 4: Verify templates**

Run:

```bash
uv run --with pyyaml python scripts/validate_manifest.py
```

Expected: manifest validation passes and all declared frontend files exist.

### Task 4: Documentation

**Files:**
- Modify: `README.md`
- Modify: `project/README.md.j2`
- Modify: `project/docs/DEVELOPMENT.md.j2`

- [ ] **Step 1: Document starter auth**

Explain generated auth routes, first-run behavior, local email logging, and admin role basics.

- [ ] **Step 2: Verify docs render**

Run:

```bash
uv run --with pyyaml python scripts/validate_manifest.py
```

Expected: manifest validation still passes.

### Self-Review

- The spec is covered by the four tasks: backend auth, CLI frontend-copy support, frontend pages, and docs.
- No task depends on a later task to remain runnable; the CLI task must merge before frontend page copying is active.
- Domain-specific Ensomble concepts were intentionally excluded from the baseline.
