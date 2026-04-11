# Frontend Code Review — 2026-04-11

## Review Scope
- **Scope**: branch
- **Files reviewed**: 11
- **Changed files**:
  - `frontend/src/api/client.ts`
  - `frontend/src/components/WeekSelector.tsx` (new)
  - `frontend/src/components/admin/AdminMenuSection.tsx`
  - `frontend/src/pages/WeeklyMenuPage.tsx`
  - `frontend/src/styles/app.css`
  - `frontend/src/types/domain.ts`
  - `frontend/package.json`
  - `frontend/package-lock.json`
  - `frontend/tests/WeekSelector.test.tsx` (new)
  - `frontend/tests/constants.test.ts` (new)
  - `frontend/tests/setup.ts` (new)
  - `frontend/vitest.config.ts` (new)

## Findings

### Critical

#### C1 — `getDateForDay` timezone bug in `WeeklyMenuPage.tsx` (line 14)
```ts
const start = new Date(periodStart);
const targetDate = new Date(start);
targetDate.setDate(start.getDate() + dayIndex);
```
`new Date("2026-04-16")` parses as **midnight UTC**. In timezones west of UTC (e.g., Americas), `getDate()` returns the previous day (15 instead of 16). In timezone-heavy apps, always force local or use explicit time: `new Date(periodStart + "T00:00:00")` or parse manually with `split("-")`. This will cause **every date label in the weekly menu to be off by one day** for many users.

#### C2 — French UI strings hardcoded inline (multiple files)
The project guidelines mandate extracting French UI strings into `constants/` modules. The following strings are hardcoded:

| File | String(s) |
|------|-----------|
| `WeeklyMenuPage.tsx` | "Pas encore de gagnant" (×3), "Menu hebdomadaire", "Visualisez les plats retenus pour chaque jour.", "Menu du", "Actualiser le menu", "Chargement..." |
| `WeekSelector.tsx` | "Semaine", "Menu de la semaine" |
| `AdminMenuSection.tsx` | "Remplacement manuel", "Forcer un plat spécifique…", "Jour", "Repas", "Plat manuel", "Utiliser les votes", "Enregistrer le remplacement", "Votes pour ce créneau", "Validation finale", "Valider le menu", "Dévalider le menu", "État finalisé", "oui", "non" |

**Fix**: Create `constants/weekly-menu.ts` and `constants/admin-menu.ts` (or extend existing modules) with typed label maps, following the pattern of `meals.ts` / `weekdays.ts`.

#### C3 — Global coverage at 2.12% far below 80% threshold
The `test:unit:coverage` run reports **2.12% statements** against the full `src/` tree. The changed source files are largely untested:

| File | Coverage |
|------|----------|
| `WeeklyMenuPage.tsx` | 0% |
| `AdminMenuSection.tsx` | 0% |
| `api/client.ts` | 0% |
| `WeekSelector.tsx` | 100% ✓ |
| constants/ | 100% ✓ |

Only `WeekSelector` and the four constant modules have tests. **`WeeklyMenuPage.tsx`** (the largest changed file) and **`AdminMenuSection.tsx`** (the most complex logic change) have zero unit-test coverage.

#### C4 — vitest coverage thresholds set to 70%, not 80%
`vitest.config.ts` sets all thresholds at **70%** while the project standard requires **80%**. This means the gate is weaker than intended.

#### C5 — Error silently swallowed in `loadPeriods()` (`WeeklyMenuPage.tsx` line 36)
```ts
} catch (error) {
  console.error("Failed to load periods:", error);
}
```
No user-facing error is shown. Per guidelines: *"Handle async failures with explicit user-facing messages and avoid silent catches."* Add an error state and render a message (e.g., `"Impossible de charger les périodes."`).

### Major

#### M1 — `day as any` cast in `WeeklyMenuPage.tsx` (line ~112)
```ts
const dayIndex = weekdayOrder.indexOf(day as any);
```
Both `day` (from `WEEK_DAYS: Weekday[]`) and `weekdayOrder: Weekday[]` are typed as `Weekday[]`. The `as any` cast should be unnecessary and masks a potential type mismatch. If it compiles without the cast, remove it; if not, the underlying types should be aligned.

#### M2 — `itemsByDay` uses loose `Record<string, Record<string, string>>`
```ts
const itemsByDay = menu?.items.reduce<Record<string, Record<string, string>>>(
```
This loses all type safety. Should be `Record<Weekday, Record<Meal, string>>` so that misspelled keys are caught at compile time.

#### M3 — Duplicate `thursday` entry in `weekdayOrder` array
```ts
const weekdayOrder: Weekday[] = [
  "thursday", "friday", "saturday", "sunday",
  "monday", "tuesday", "wednesday", "thursday"  // ← appears twice
];
```
`indexOf("thursday")` always returns **0** (the first occurrence), meaning Thursday's date label always shows the period start date. This is *probably* intentional (periods start on Thursday), but the duplication is confusing and fragile. Add a comment or refactor to use `dayIndex = day === "thursday" ? 0 : WEEK_DAYS.indexOf(day) + 1`.

#### M4 — `WeekSelector` emits checkmark character "✓" inline
The "✓" for finalized periods is concatenated directly in the option text. This is a UI constant that should live in a constants module (e.g., `FINALIZED_INDICATOR = " ✓"`) for consistency and i18n readiness.

#### M5 — `handlePeriodSelect` has dead code path for non-null `periodId`
When a specific period is selected, the handler calls `onRefresh()` which fetches the *current* menu — not the selected period's menu. The comment acknowledges this ("would need backend endpoint for this"), but the UX is misleading: selecting a past week shows the current week's menu. Either disable non-current options or wire up the actual period-fetch endpoint.

#### M6 — `AdminMenuSection` `useMemo` uses string literals for category filtering
```ts
if (selectedDay === "saturday") {
  if (selectedMeal === "lunch") return dish.category === "weekends_lunch";
  return selectedMeal === "dinner" && dish.category === "saturday_dinner";
}
```
String literals `"saturday"`, `"lunch"`, `"weekends_lunch"`, etc. are used instead of the typed constants from `constants/weekdays.ts`, `constants/meals.ts`. This creates a maintenance risk — if the type values change, these strings won't update. Use `Meal.LUNCH` or typed guards instead.

#### M7 — No Playwright/E2E test for `WeeklyMenuPage` with new `WeekSelector`
Existing Playwright tests (`admin.spec.ts`) cover the admin tab navigation but do not test:
- WeekSelector rendering or interaction on the WeeklyMenuPage
- Period label display
- Date calculation in table rows

### Minor

#### m1 — `getDateForDay` can be a pure utility, not a page-local function
This function is generic date math that could live in `src/utils/date.ts` for reusability. Not urgent, but would improve separation of concerns.

#### m2 — `week-select-input` class naming inconsistency
The CSS class `week-select-input` mixes two naming conventions seen elsewhere (`week-selector-label` vs `week-select-input`). Consider `week-selector-select` for consistency.

#### m3 — Missing `aria-busy` on loading refresh button
The refresh button gets `disabled={loadingPeriod}` and changes text to "Chargement…", which is good. Adding `aria-busy={loadingPeriod}` would improve accessibility for screen readers.

#### m4 — `AdminMenuSection` renders inline `type="button"` on AdminButton children
All `AdminButton` elements receive `type="button"` — this is correct (prevents form submission), but it would be cleaner to set `type="button"` as the default inside `AdminButton` itself.

#### m5 — CSS media query for `.section-head-row` duplicated
There are two `@media (max-width: 700px)` blocks both setting `.section-head-row { flex-direction: column; }`. Merge them.

## Coverage Summary
- **Test command**: `npm run test:unit:coverage`
- **Result**: pass (all 15 tests green)
- **Coverage**: **2.12%** global (target: >= 80%)
  - WeekSelector: 100%
  - constants/: 100%
  - WeeklyMenuPage: 0%
  - AdminMenuSection: 0%
  - api/client.ts: 0%
- **Untested critical paths**:
  - `WeeklyMenuPage` date calculation (`getDateForDay`)
  - `WeeklyMenuPage` period loading and error handling
  - `AdminMenuSection` `filteredDishes` memo with weekend/weekday logic
  - `AdminMenuSection` `votesForSlot` memo and `voteCounts` aggregation
  - `api/client.ts` — none of the new endpoints (`getMenuPeriods`, `getCurrentPeriod`)

## Score Breakdown
| Category               | Score (/10) |
|------------------------|-------------|
| Coding style           | 6           |
| Architecture           | 6           |
| Performance & readability | 7        |
| Tests & coverage       | 3           |

## Global Note: 5/10

The changes add genuinely useful features (historical week selection, dish filtering, admin menu validation) with good component decomposition. `WeekSelector` is well-structured with full test coverage. However, the widespread hardcoding of French strings, the timezone-sensitive date parsing bug, the near-zero coverage on the two most complex changed files, and the dead UX path for non-current period selection are significant issues that should be addressed before merging.

## Review Status
**CHANGES REQUIRED**

## Recommended Next Actions

1. **[Critical] Fix `getDateForDay` timezone bug** — Parse ISO dates without timezone shift (e.g., `new Date(periodStart + "T00:00:00")`).
2. **[Critical] Extract all French UI strings** into `constants/` modules following the established `meals.ts` / `weekdays.ts` pattern.
3. **[Critical] Add unit tests** for `WeeklyMenuPage` (date calculation, period loading, error state) and `AdminMenuSection` (dish filtering logic for weekends vs weekdays).
4. **[Critical] Raise vitest coverage thresholds** to 80% in `vitest.config.ts` to match project standard.
5. **[Major] Add user-facing error state** in `loadPeriods()` catch block instead of silent `console.error`.
6. **[Major] Remove `as any` cast** in `WeeklyMenuPage` — fix the underlying type or document why it's needed.
7. **[Major] Clarify or fix** the `weekdayOrder` duplicate-Thursday issue.
8. **[Major] Decide on non-current period UX** — either disable those options or wire up the backend endpoint to fetch historical menus.
9. **[Minor] Add Playwright E2E test** covering the WeekSelector interaction on WeeklyMenuPage.
10. **[Minor] Merge duplicate media query** rules in `app.css`.
