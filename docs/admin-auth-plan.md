# Plan: Admin Authentication

## TL;DR
Add a simple session-based admin login to protect all `/admin` routes, keep the rest of the site public, and expose a top-right login/logout action in the UI.

## Steps
1. Add backend admin auth helpers and session guard.
   - Create `backend/app/core/auth.py` with one admin username and env-configurable password.
   - Add login (`POST /admin/login`), logout (`POST /admin/logout`), and session check (`GET /admin/session`) endpoints.
   - Protect all existing admin endpoints with a FastAPI dependency like `Depends(get_current_admin)`.
   - Keep admin account hard-coded as `admin`; configure password via `ADMIN_PASSWORD` env var with a safe default.

2. Add auth request handling in the frontend API client.
   - Update `frontend/src/api/client.ts` to include `credentials: "include"` on fetch requests.
   - Add `loginAdmin`, `logoutAdmin`, and `checkAdminSession` helper functions.

3. Add frontend admin login UX and route guard.
   - Add a login link/button in the top-right of `frontend/src/App.tsx`.
   - Add admin auth state in `App` and a route guard for `/admin`.
   - Add a login page component at `frontend/src/pages/AdminLoginPage.tsx` with username and password fields.
   - Redirect unauthenticated users from `/admin` to the login page.
   - After login, allow access to `/admin` and switch the top-right link to logout.

4. Add support endpoints and auth schema.
   - Add `AdminLoginRequest` schema to `backend/app/schemas/common.py`.
   - Add any needed response model for session status.

5. Update tests for auth behavior.
   - Update backend tests to authenticate before calling protected admin routes.
   - Add backend coverage for login, session check, unauthorized access, and logout.
   - Update frontend Playwright tests to verify the login link, login flow, protected `/admin` access, and logout.

## Relevant files
- `backend/app/main.py`
- `backend/app/routers/admin.py`
- `backend/app/core/auth.py`
- `backend/app/schemas/common.py`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/pages/AdminLoginPage.tsx`
- `frontend/src/styles/app.css`
- `frontend/tests/admin.spec.ts`
- `backend/tests/test_admin_members.py`

## Verification
1. `POST /admin/login` with correct admin credentials returns success and sets a session cookie.
2. `GET /admin/members` returns 401 when not authenticated and 200 after login.
3. `POST /admin/logout` ends the session so admin routes fail until login again.
4. The UI shows `Se connecter` in the top right when logged out and `Se déconnecter` when logged in.
5. Visiting `/admin` redirects to login when not authenticated and shows the admin UI after login.
6. Frontend tests cover login link visibility, login success, protected route redirect, and logout.

## Decisions
- Use a single hard-coded admin user named `admin`.
- Use an env-configurable password with a default fallback.
- Protect admin routes at the API layer and in the frontend routing.
- Keep voting, catalog, and weekly menu pages public.

## Further considerations
1. Later, add localStorage session refresh or a refresh endpoint if reload persistence is needed.
2. For stronger security later, consider switching to JWT or HTTP Basic auth instead of cookie sessions.
