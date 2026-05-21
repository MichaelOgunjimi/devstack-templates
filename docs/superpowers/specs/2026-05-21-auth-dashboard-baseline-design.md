# Auth Dashboard Baseline Design

## Goal

Generated DevStack projects should be usable immediately as starter products: a developer can create an app, run it, register, log in, land on a dashboard, and protect admin-only screens without designing auth from scratch.

## Scope

This baseline is generic. It uses `user` and `admin` roles only. Domain-specific roles such as customer, vendor, musician, creator, tenant, or staff belong in later optional template modules.

The baseline includes:

- Backend email/password auth with refresh tokens.
- Current-user profile endpoints.
- Password reset and email verification flows.
- A small admin authorization dependency.
- Next.js auth pages and starter dashboard/admin pages.
- Local email behavior that works without SMTP credentials.

OAuth, billing, deep RBAC, organization membership, invitations, and domain dashboards stay outside this slice.

## Backend Design

The backend keeps the existing FastAPI structure and extends it rather than replacing it.

- `models/user.py` stores `role`, `is_active`, and `is_verified`.
- `schemas/auth.py` owns request/response contracts for register, login, refresh, email verification, password reset, and change password.
- `services/auth.py` owns user creation, token creation/revocation, reset/verification token creation, and email dispatch.
- `api/v1/auth.py` remains a thin route layer.
- `api/deps.py` exposes `AdminDep`, implemented as `get_current_admin_user`.

Verification and reset tokens are signed JWTs with dedicated `type` claims. They are stateless for the first baseline so projects do not need extra token tables before they can run. Refresh tokens remain persisted in the database and cached in Redis so logout and revocation keep working.

## Email Design

The baseline must not require real email credentials in development.

`services/integrations/email` should provide a `send_email` interface that:

- Sends via SMTP when `SMTP_HOST` and sender settings are configured.
- Logs the email subject and important action link when SMTP is not configured.

This lets password reset and verification work in local development by copying the logged link.

## Frontend Design

The CLI needs to copy stack-declared frontend app files after Next.js scaffolding. The template repo will provide simple Next.js App Router pages:

- `/login`
- `/register`
- `/forgot-password`
- `/reset-password`
- `/verify-email`
- `/dashboard`
- `/admin`

The pages should use the generated auth client and plain Tailwind classes. They should avoid shadcn-specific components so the baseline works whether the user opted into shadcn or not.

`/dashboard` requires any authenticated user. `/admin` requires `user.role === "admin"` and shows an access-denied state otherwise.

## Testing

Backend tests cover the first hard guarantees:

- Registration returns tokens and creates a `user` role by default.
- Duplicate registration returns 409.
- Login returns tokens for valid credentials.
- `/auth/me` returns the current user.
- Forgot password returns a generic success message.
- Reset password changes the password when given a valid reset token.
- Email verification marks the user as verified.
- Admin dependency rejects normal users and accepts admins.

Frontend files are template assets. The first automated check should be manifest validation plus a template smoke check that every declared frontend source path exists. A later CLI PR should add an end-to-end generated-project smoke test.

## Rollout

Ship this in two dependent PRs:

1. `devstack-cli`: add frontend output file support to the manifest and new-project scaffolder.
2. `devstack-templates`: add the backend auth baseline, frontend app files, and manifest entries.

The backend template changes can be reviewed independently, but the frontend pages only become active for generated projects after the CLI support lands.
