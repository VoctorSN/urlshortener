# Security Audit Report

Date: 2026-03-13
Scope: Full repository static review (application code + local config files in workspace)

## Executive Summary

The codebase has no authentication/authorization layer and exposes all operational endpoints publicly, including write operations (create/update/delete) and analytics access. In addition, there are real API keys present in local configuration files. Input validation is good for core URL creation fields, and SQL queries are ORM-parameterized (no direct SQL injection patterns found), but some request-derived fields are trusted/stored without normalization or limits.

## Findings

## Update 2026-03-13 (Token Security Implemented)

Status update after remediation work:

- Token-based authentication was added globally using Bearer tokens.
- Protected routes are now configurable from settings via `AUTH_PROTECTED_ROUTE_PATTERNS`.
- Exempt/public routes are configurable via `AUTH_EXEMPT_ROUTE_PATTERNS`.
- Default policy now protects `/api/urls/*` and keeps `/health`, `/favicon.ico`, and `/{short_code}` public.
- Auth accepts either:
  - a static API token from `API_TOKENS`, or
  - a valid JWT HS256 signed with `JWT_SECRET`.

Residual risk:

- Resource-level authorization (ownership/tenant checks) is still pending. Authentication now exists, but any valid principal can access protected resources unless ownership rules are added in a later phase.

### 1) Exposed API Keys in Workspace Files

Severity: Critical (if shared), High (local compromise)

Evidence:

- `.env`: `TESTSPRITE_API_KEY=...` (real `sk-user-...` token)
- `.vscode/mcp.json`: `API_KEY=...`
- `.claude/settings.json`: `API_KEY=...`

Notes:

- `git ls-files` shows these files are not currently tracked, which reduces repo leak risk.
- Risk remains high if files are shared, backed up, screen-shared, copied, or accidentally committed later.

Recommended fixes:

1. Rotate all exposed tokens immediately.
2. Replace plaintext secrets with environment-only injection from a secret manager or CI/CD secrets.
3. Add hard fail checks in CI to block secrets (e.g., gitleaks/trufflehog/pre-commit hooks).
4. Keep `.env`, `.vscode/`, `.claude/` ignored and avoid storing live keys in editor config.

### 2) Missing Authentication and Authorization on All API Routes

Severity: Critical

Evidence:

- No auth dependencies in routers (`Depends(get_db)` only).
- No usage of FastAPI security components (`fastapi.security`, bearer/API key/OAuth2 not present).
- Public access includes:
  - `POST /api/urls` (create)
  - `PATCH /api/urls/{short_code}` (update)
  - `DELETE /api/urls/{short_code}` (deactivate)
  - `GET /api/urls` (enumerate all records)
  - `GET /api/urls/{short_code}/analytics` and `/clicks` (analytics data exposure)

Impact:

- Anyone can modify or deactivate links.
- Anyone can enumerate stored URLs and metadata.
- Analytics and click event data can be accessed without identity checks.

Recommended fixes:

1. Add authentication (API key/JWT/OAuth2).
2. Introduce ownership/tenant model for URL records.
3. Enforce authorization per resource on read/update/delete/analytics endpoints.
4. Restrict list endpoints to owner/admin scopes.

### 3) Untrusted Header Trust: Spoofable Client IP

Severity: Medium

Evidence:

- `extract_client_ip()` trusts `X-Forwarded-For` directly and takes first value.

Impact:

- Attackers can spoof IP-based analytics and potentially weaken IP rate-limit assumptions in downstream logic.

Recommended fixes:

1. Trust forwarding headers only behind known reverse proxies.
2. Use trusted proxy middleware/config and strip untrusted forwarding headers at edge.
3. Consider logging both transport IP and trusted forwarded IP for auditability.

### 4) Unsanitized/Unbounded Header-Derived Input Stored and Re-Exposed

Severity: Medium

Evidence:

- `record_click()` stores raw `user-agent` and `referer` from request headers.
- Click data is returned via `/api/urls/{short_code}/clicks`.

Impact:

- Potential log/data poisoning and downstream stored-XSS risk if a frontend later renders these fields unsafely.
- Potential storage abuse from oversized header values.

Recommended fixes:

1. Add length limits and normalization for `user_agent` and `referrer` before persisting.
2. Optionally drop/control characters and invalid Unicode sequences.
3. Ensure any UI layer escapes output by default.

### 5) Lack of Path Parameter Constraints for `short_code` on Read/Write Routes

Severity: Low

Evidence:

- `short_code` path params are plain `str` in multiple routes without regex/min/max constraints.

Impact:

- Not SQL-injectable in current ORM usage, but allows oversized/invalid values, unnecessary DB load, and inconsistent behavior vs. create-time alias rules.

Recommended fixes:

1. Constrain route params with regex and length (same policy as `custom_alias`: 3-30, `[a-zA-Z0-9_-]+`).
2. Reject invalid short codes early at request validation layer.

## Positive Security Notes

- Core URL creation input uses Pydantic `HttpUrl` and alias regex constraints.
- SQL access uses SQLAlchemy ORM expressions; no raw SQL string interpolation patterns were found.
- Rate limiting is enabled via `slowapi` on all main routes.

## Priority Remediation Plan

1. Rotate leaked secrets and remove plaintext keys from local config files.
2. Implement authentication + per-resource authorization immediately.
3. Add input constraints for `short_code` path params.
4. Normalize and cap header-derived fields (`User-Agent`, `Referer`, forwarded IP).
5. Add automated secret scanning and security checks to CI.
