# Backend Code Review — 2026-04-03

## Review Scope
- Scope: branch
- Files reviewed: 18
- Changed files:
  - `backend/Dockerfile`
  - `backend/app/__init__.py`
  - `backend/app/core/auth.py`
  - `backend/app/core/ssm.py`
  - `backend/app/lambda_handler.py`
  - `backend/app/main.py`
  - `backend/app/routers/admin.py`
  - `backend/app/routers/members.py`
  - `backend/app/routers/votes.py`
  - `backend/app/schemas/common.py`
  - `backend/app/services/store.py`
  - `backend/pytest.ini`
  - `backend/requirements.txt`
  - `backend/tests/conftest.py`
  - `backend/tests/test_admin_members.py`
  - `backend/tests/test_health_and_dishes.py`
  - `backend/tests/test_ssm.py`
  - `backend/tests/test_store_module.py`
  - `backend/tests/test_votes_and_menu.py`

## Findings

### Critical

1. **[BUG] SSM SecureString not decrypted** — `app/core/ssm.py:15`
   `get_admin_password()` calls `ssm.get_parameter(Name=parameter_name)` without `WithDecryption=True`. For SecureString parameters, this returns the encrypted ciphertext, not the actual password. This is also the root cause of the failing test `test_get_admin_password_from_ssm`.
   **Fix**: Add `WithDecryption=True` to the `get_parameter` call.

2. **[TEST FAILURE] `test_get_admin_password_from_ssm` fails** — `tests/test_ssm.py:9`
   The `DummySSMClient.get_parameter` asserts `WithDecryption is True`, but the production code never passes that argument. **1 test fails out of 25.**

3. **[SECURITY] Static session token — trivially forgeable** — `app/core/auth.py:11`
   `ADMIN_SESSION_TOKEN = "authenticated"` is a hardcoded string value set as the cookie. Any client can set the cookie `family_meal_planner_admin_session=authenticated` to gain admin access without authenticating. This is a session fixation / cookie forging vulnerability.
   **Fix**: Generate a cryptographically random token on login and validate it server-side against a stored session map.

4. **[SECURITY] Cookie missing `secure` flag** — `app/core/auth.py:39-42`
   `response.set_cookie(…, httponly=True, samesite="lax")` does not set `secure=True`. In production (HTTPS), the cookie could be sent over unencrypted connections.
   **Fix**: Set `secure=True` when running behind HTTPS (e.g. conditioned on an environment variable).

5. **[ARCHITECTURE] Business logic in `votes.py` router** — `app/routers/votes.py:17-18`
   The router pre-validates `payload.dish_id` against `store.list_dishes()` before calling `store.add_vote()`. This duplicates validation already performed inside `store.add_vote()` and puts business logic in the HTTP layer, violating the thin-router rule.
   **Fix**: Remove the duplicate dish-ID check from the router; let the service raise `KeyError` and map it in the `except` block.

6. **[COVERAGE] `app/routers/admin.py` at 62%** — well below the 80% per-file threshold.
   Missing coverage for: admin dish CRUD error paths, shortlist legacy endpoint, menu item legacy endpoint, menu validate/unvalidate error paths, and several 4xx branches.
   **Fix**: Add tests for admin dish update/delete errors (404, 409), shortlist 404/400 errors, manual menu item errors, and validate/unvalidate flows.

### Major

7. **[BUG] Typo in error message** — `app/core/ssm.py:11`
   `"ADMIN_PASSWORD_PARAMETER_name must be provided"` — lowercase `name` should be `NAME` to match the env var `ADMIN_PASSWORD_PARAMETER_NAME`.

8. **[ARCHITECTURE] Data transformation in router** — `app/routers/admin.py:130`
   `store.set_shortlists([slot.model_dump() for slot in payload])` converts Pydantic models to dicts in the router. The service should accept the typed schema objects directly.
   **Fix**: Change `store.set_shortlists()` to accept `list[SetShortlistRequest]` instead of `list[dict]`.

9. **[ARCHITECTURE] Side effect at import time** — `app/routers/dishes.py:7`
   `store.seed_data()` is called at module level when `dishes.py` is imported. This means seed data runs on every import (including tests, Lambda cold starts, etc.). It's a hidden coupling.
   **Fix**: Move `seed_data()` to an explicit startup hook (e.g., FastAPI `@app.on_event("startup")` or a lifespan handler), or guard it behind an environment variable.

10. **[TYPE SAFETY] Loose type on `set_shortlist` parameter** — `app/services/store.py:351`
    `def set_shortlist(day: str, meal: Meal, ...)` — `day` is typed as `str` instead of `Weekday`. Same issue on `set_menu_item` (line 376) and `get_slot_category` (line 404).
    **Fix**: Use the `Weekday` literal type for consistency and static analysis.

11. **[TYPE SAFETY] Missing return type on `_scan_table`** — `app/services/store.py:67`
    `def _scan_table(table)` has no type hints on parameter or return value.

12. **[UNUSED IMPORT]** — `app/services/store.py:5`
    `from boto3.dynamodb.conditions import Attr` is imported but never used.

13. **[RETURN TYPE MISMATCH] `list_dish_categories`** — `app/services/store.py:320`
    Returns `list[str]` but the router at `admin.py:93` declares `response_model=list[DishCategory]`. While compatible at runtime (DishCategory is a `Literal[str]`), the function signature should return `list[DishCategory]` for correctness.

### Minor

14. **[STYLE] `login_admin` helper duplicated across test files** — `tests/test_admin_members.py:4` and `tests/test_votes_and_menu.py:4`
    The same `login_admin(client)` helper is defined in two test files. Consider moving it to `conftest.py` as a shared fixture or utility.

15. **[STYLE] Legacy endpoints carry tech debt** — `app/routers/admin.py:142,163`
    `put_shortlist_legacy` and `put_menu_item_legacy` suggest the old API shape is still in use. If the frontend has migrated, these should be deprecated and removed. If still needed, add deprecation warnings.

16. **[STYLE] `requirements.txt` unpinned** — `backend/requirements.txt`
    All dependencies are unpinned (`fastapi`, `boto3`, etc.). This can lead to non-reproducible builds and unexpected breakage on version bumps.
    **Suggestion**: Pin major versions at minimum (e.g., `fastapi>=0.100,<1.0`).

17. **[STYLE] Dockerfile uses Python 3.11 but venv is Python 3.13** — `backend/Dockerfile:1`
    The Dockerfile uses `python:3.11-slim` while the local venv is Python 3.13. This mismatch could cause subtle compatibility issues.

18. **[STYLE] `conftest.py` sets env var and inserts sys.path at import time** — `tests/conftest.py:8-9`
    `os.environ["BACKEND_PERSISTENCE_MODE"] = "inmemory"` and `sys.path.insert(…)` are run at import time. The sys.path manipulation is fragile; prefer configuring `pythonpath` in `pytest.ini` instead.

## Coverage Summary
- Test command: `pytest --cov=app --cov-report=term-missing`
- Result: **FAIL** (1 test failure: `test_get_admin_password_from_ssm`)
- Coverage: **83.22%** (target: >= 80%) — threshold met overall
- Per-file coverage below 80%:
  | File | Coverage |
  |------|----------|
  | `app/routers/admin.py` | 62% |
- Untested critical paths:
  - Admin dish CRUD error branches (404, 409 on update/delete)
  - Admin shortlist legacy endpoint
  - Admin menu item legacy endpoint
  - Admin menu validate conflict path
  - Admin menu unvalidate conflict path
  - Votes router dead code branch (line 22, unreachable due to pre-check)

## Score Breakdown
| Category                  | Score (/10) |
|---------------------------|-------------|
| Coding style              | 7           |
| Architecture              | 6           |
| Performance & readability | 7           |
| Tests & coverage          | 6           |

## Global Note: 6/10

## Review Status
**CHANGES REQUIRED**

## Recommended Next Actions
1. **Fix SSM `WithDecryption=True`** in `app/core/ssm.py` and fix the corresponding test — this is a production bug.
2. **Replace the static session token** with a proper random token + server-side session map to close the cookie forging vulnerability.
3. **Remove duplicate dish-ID validation** from `votes.py` router — let the service handle it.
4. **Add tests for `admin.py`** to bring per-file coverage above 80% (currently 62%).
5. **Accept typed schemas in `store.set_shortlists()`** instead of `list[dict]`.
6. **Move `seed_data()`** out of module-level execution in `dishes.py`.
7. **Fix the typo** in `ssm.py` error message (`PARAMETER_name` → `PARAMETER_NAME`).
8. **Remove unused import** `Attr` from `store.py`.
9. **Pin dependency versions** in `requirements.txt`.
10. **Add `secure=True`** to the admin session cookie for production deployments.
