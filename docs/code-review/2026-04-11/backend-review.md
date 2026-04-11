# Backend Code Review — 2026-04-11

## Review Scope
- Scope: branch
- Files reviewed: 15
- Changed files:
  - `backend/app/main.py`
  - `backend/app/routers/menu.py`
  - `backend/app/routers/periods.py`
  - `backend/app/routers/votes.py`
  - `backend/app/schemas/common.py`
  - `backend/app/services/period_utils.py`
  - `backend/app/services/store.py`
  - `backend/app/services/store_dynamodb.py`
  - `backend/app/services/store_inmemory.py`
  - `backend/app/services/store_interface.py`
  - `backend/tests/test_store_module.py`
  - `backend/tests/test_auth.py`
  - `backend/tests/test_period_utils.py`
  - `backend/tests/test_periods.py`
  - `backend/tests/test_schemas.py`

## Findings

### Critical

1. **Coverage below 80% threshold — review gate FAIL** (all files)
   - Overall coverage: **72%** (target: ≥ 80%).
   - `store_dynamodb.py` at **36%** is the main drag — 277 of 430 lines untested. Every persistence helper (`_persist_*`, `_delete_*`, `_load_*`, pagination in `_query_pk`/`_query_gsi1`) lacks test coverage.
   - Per the testing-coverage-gate rule, this is a **hard failure**.

2. **`menu.py` — `period` query parameter is declared but never used** (`backend/app/routers/menu.py:11`)
   - `get_weekly_menu(period: str | None = None)` accepts a `period` parameter but always returns the current period via `store.generate_weekly_menu()`. Clients passing `?period=2026-04-09` will silently get the wrong result.
   - Either use the parameter to fetch a historical period, or remove it to avoid misleading API consumers.

3. **`main.py` — `invalidate_store_cache_middleware` defeats DynamoDB caching on every request** (`backend/app/main.py:30-33`)
   - The middleware calls `store.invalidate_store_cache()` at the **start** of every request, forcing a full DynamoDB reload on every single API call. This negates the in-memory cache purpose and will cause excessive read throughput costs.
   - Recommended: only invalidate on mutation endpoints (POST/PUT/DELETE), not on GET/HEAD.

4. **`period_utils.py` — `should_create_new_period()` returns `True` 6 of 7 days** (`backend/app/services/period_utils.py:85`)
   - Docstring says: "New periods are created on Tuesday after finalization."
   - Implementation: `return now.weekday() >= 1` — returns `True` for Tuesday through Sunday (6/7 days). Only Monday returns `False`.
   - Semantic mismatch between documentation and behavior. This could cause unwanted period creation on any non-Monday day.

### Major

5. **`store_dynamodb.py` / `store_inmemory.py` — uses `__import__()` instead of proper imports** (`backend/app/services/store_dynamodb.py:572`, `backend/app/services/store_inmemory.py:28`)
   - `logger = __import__("logging").getLogger(__name__)` and `__import__("datetime").datetime.now()` are code smells that bypass linters and static analyzers.
   - Use `import logging` / `from datetime import datetime` at module scope (or defer the `datetime` import inside the function if avoiding top-level cost).

6. **`period_utils.py` — `get_current_period()` returns 8 days but `end_date` only spans 7** (`backend/app/services/period_utils.py:36-43`)
   - `end_date = start_date + timedelta(days=7)` → Wednesday.
   - `period_days` loop runs 8 iterations → Thursday through following Thursday.
   - The `days` list includes a second Thursday that is *after* `end_date`. The label `"16/04 - 23/04"` (Thu–Wed) doesn't match the 8-day span (Thu–Thu). This is a subtle inconsistency that could confuse consumers.

7. **`periods.py` — dead `pass` block with TODO-style comment in production code** (`backend/app/routers/periods.py:38-41`)
   ```python
   if not period.menu:
       # For historical periods, we need to regenerate or retrieve stored menu
       # For now, return period without menu (can be enhanced later)
       pass
   ```
   - This `pass` is a no-op — the period is returned without menu regardless. Either implement the feature or remove the conditional entirely to reduce noise.

8. **`main.py` — `call_next` parameter lacks type hint** (`backend/app/main.py:30`)
   - `async def invalidate_store_cache_middleware(request: Request, call_next) -> Response:`
   - Should be typed as `Callable[[Request], Awaitable[Response]]` from `collections.abc`.

9. **`store_interface.py` — non-abstract defaults for `auto_finalize_if_needed` and `ensure_active_period`** (`backend/app/services/store_interface.py:205-224`)
   - These are concrete methods in an abstract base class. While intentional (shared default behavior), they could be extracted into a mixin to clarify intent and avoid the ABC carrying non-abstract methods.

### Minor

10. **`store.py` factory — `__getattr__` delegation breaks IDE autocomplete and static type checking** (`backend/app/services/store.py:64-75`)
    - Clever pattern for backward compatibility, but type checkers (mypy, pyright) cannot resolve attributes through `__getattr__`. Consider adding a `TYPE_CHECKING` block with a stub or using `typing.TYPE_CHECKING` for IDE support.

11. **`test_store_module.py` — tests bypass `__init__` via `object.__new__()`** (multiple lines)
    - `DynamoDBStore` instances are created with `object.__new__(DynamoDBStore)` and attributes set manually. This works for isolated unit tests but is fragile — any new `__init__` field must be manually added to every test. Consider a factory helper or `@pytest.fixture` that centralizes this setup.

12. **`schemas/common.py` — `MenuPeriod.menu` uses string forward reference** (`backend/app/schemas/common.py:78`)
    - `menu: "WeeklyMenuResponse | None" = None` works because `WeeklyMenuResponse` is defined later in the file, but `from __future__ import annotations` at the top would allow native syntax and is the modern Pydantic v2 approach.

13. **`votes.py` — `post_vote` catches generic `ValueError` and re-raises 409** (`backend/app/routers/votes.py:24-25`)
    - The `if detail == "Member not found"` check relies on exact string matching. If the error message in the service changes, the mapping silently breaks. Consider using a custom exception type (e.g., `MemberNotFoundError`) instead.

14. **`test_periods.py` — tests mutate shared store singleton without isolation** (`backend/tests/test_periods.py:18-21`)
    - Tests call `store.create_period(...)` directly. While the `reset_store` fixture runs autouse, tests that create periods may interfere with each other if the fixture ordering changes. Explicit isolation via a dedicated store fixture per test class would be safer.

## Coverage Summary
- Test command: `pytest --cov=app --cov-report=term-missing`
- Result: **FAIL** (exit code 1 — coverage gate not met)
- Coverage: **72%** (target: >= 80%)
- Untested critical paths:
  - `store_dynamodb.py` (36%): all `_persist_*`, `_delete_*`, `_load_*` helpers, pagination in `_query_pk`/`_query_gsi1`, `archive_period`, `auto_finalize_if_needed`, `get_active_period`, `list_periods`, session CRUD methods.
  - `store_inmemory.py` (89%): edge cases in `update_member`, `delete_member`, `archive_period`.
  - `app/main.py` (92%): lifespan function lines 13-14.
  - `store.py` factory (92%): `reset_store()` path lines 55-56.
  - `app/core/ssm.py` (80%): error-handling branch lines 18-25.

## Score Breakdown
| Category               | Score (/10) |
|------------------------|-------------|
| Coding style           | 7           |
| Architecture           | 7           |
| Performance & readability | 6        |
| Tests & coverage       | 5           |

## Global Note: 6/10

The codebase shows a clean layered architecture (thin routers → services → schemas), a well-designed store abstraction with both in-memory and DynamoDB implementations, and comprehensive test suites for `period_utils`, `auth`, `schemas`, and the periods router. However, the review fails the coverage gate at 72% (target 80%), driven almost entirely by `store_dynamodb.py` at 36%. There are also a few semantic mismatches (unused `period` parameter, `should_create_new_period` docstring vs. implementation) and a middleware that undermines caching. These issues are fixable without structural changes.

## Review Status
**CHANGES REQUIRED**

## Recommended Next Actions

1. **Bring `store_dynamodb.py` coverage above 80%** — add tests for all `_persist_*`, `_delete_*`, `_load_*` helpers using the existing `FakeTable` pattern already present in `test_store_module.py`. Centralize the FakeTable setup into a reusable `@pytest.fixture` to reduce duplication.

2. **Fix `menu.py` — use or remove the `period` query parameter** — either implement historical period lookup when `period` is provided, or drop the parameter and add a deprecation note.

3. **Fix `main.py` middleware** — change `invalidate_store_cache_middleware` to only invalidate on mutation methods (POST/PUT/DELETE/PATCH), or move cache invalidation into the relevant service methods.

4. **Fix `should_create_new_period()` logic** — align the implementation with the docstring (should return `True` only on Tuesday after finalization), or update the docstring to reflect the current 6/7-day behavior.

5. **Replace `__import__()` calls** with proper module-level imports in `store_dynamodb.py` and `store_inmemory.py`.

6. **Remove or implement the dead `pass` block** in `periods.py:38-41`.
