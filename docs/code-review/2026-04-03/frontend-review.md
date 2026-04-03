# Frontend Code Review — 2026-04-03

## Review Scope
- Scope: branch
- Files reviewed: 25
- Changed files:
  - `frontend/index.html`
  - `frontend/package.json`
  - `frontend/playwright.config.ts`
  - `frontend/src/App.tsx`
  - `frontend/src/api/client.ts`
  - `frontend/src/components/admin/AdminButton.tsx`
  - `frontend/src/components/admin/AdminCatalogSection.tsx`
  - `frontend/src/components/admin/AdminMembersSection.tsx`
  - `frontend/src/components/admin/AdminMenuSection.tsx`
  - `frontend/src/components/admin/AdminSection.tsx`
  - `frontend/src/components/admin/AdminSectionNav.tsx`
  - `frontend/src/components/admin/AdminVotesSection.tsx`
  - `frontend/src/constants/meals.ts`
  - `frontend/src/constants/weekdays.ts`
  - `frontend/src/pages/AdminLoginPage.tsx`
  - `frontend/src/pages/AdminPage.tsx`
  - `frontend/src/pages/CatalogPage.tsx`
  - `frontend/src/pages/VotingPage.tsx`
  - `frontend/src/pages/WeeklyMenuPage.tsx`
  - `frontend/src/styles/app.css`
  - `frontend/src/types/domain.ts`
  - `frontend/tests/admin.spec.ts`
  - `frontend/tests/voting.spec.ts`
  - `frontend/vite.config.d.ts`
  - `frontend/vite.config.js`

## Findings

### Critical

1. **Playwright admin tests use non-existent selectors — tests will fail**
   - `admin.spec.ts:56,63` — `page.locator('input[placeholder*="Nom du plat"]')` and `'input[placeholder*="Tags"]'` reference `placeholder` attributes that do not exist on the inputs in `AdminCatalogSection.tsx`. All inputs use `<label>...<input /></label>` without placeholders. The "add dish" and "delete dish" tests will fail at runtime.

2. **Admin tests assume wrong tab is active on load**
   - `admin.spec.ts:54–77` — After login, `AdminPage` defaults `selectedSection` to `"members"`, so the catalog form is hidden. The tests for adding/deleting dishes attempt to interact with catalog inputs that are in a non-rendered tab, causing test failures.

3. **Admin test button text mismatch for menu validation**
   - `admin.spec.ts:80` — Test clicks `'Valider menu hebdomadaire'` but `AdminMenuSection.tsx:81` renders `'Valider le menu'`. This test will always fail.

4. **Dead code: `votesBySlot` computed but never used**
   - `AdminPage.tsx:119–133` — `votesBySlot` is computed via `useMemo` and the `votes` state is fetched, but neither is passed to any child component or used in rendering. This is dead code that performs a network call (`getVotes`) with no visible effect and silently swallows errors.

5. **`signIn` helper duplicated across describe blocks**
   - `admin.spec.ts:4–9` and `admin.spec.ts:37–42` — The `signIn` function is duplicated verbatim. Should be extracted to a shared helper above both blocks for maintainability.

6. **Compiled artifacts committed: `vite.config.js` and `vite.config.d.ts`**
   - These are compiled outputs of `vite.config.ts` and should not be tracked in source control. Their presence can cause confusion about which config file is authoritative.

### Major

7. **`WeeklyMenuPage` day ordering not guaranteed**
   - `WeeklyMenuPage.tsx:12–21` — Uses `Object.keys(itemsByDay)` to iterate days in the table, but `Object.keys` does not guarantee meaningful ordering. Should iterate `WEEK_DAYS` from `constants/weekdays.ts` and look up each day in `itemsByDay` to ensure Monday-through-Sunday display order.

8. **`categoryLabel` function triplicated**
   - Identical category-to-French-label mapping exists in three places:
     - `AdminPage.tsx:56–65` (function `categoryLabel`)
     - `AdminCatalogSection.tsx:20–30` (function `categoryLabel`)
     - `CatalogPage.tsx:4–9` (constant `categoryLabels`)
   - Per project rules, French UI strings should be extracted into `constants/`. Create a shared `CATEGORY_LABELS_FR` constant.

9. **`initialAvailability` and `AvailabilityMap` type duplicated**
   - `VotingPage.tsx:13–23` and `AdminPage.tsx:40–54` — Both the type alias and the default object are copy-pasted. Extract to `types/domain.ts` and `constants/` respectively.

10. **`AdminSectionNav` ARIA roles incorrect**
    - `AdminSectionNav.tsx:19` — Uses `role="tablist"` on the container but `aria-pressed` on buttons. Per WAI-ARIA, tab patterns require `role="tab"` on each button and `aria-selected` instead of `aria-pressed`. Content panels should have `role="tabpanel"`.

11. **`Dispatch<SetStateAction<...>>` in component props**
    - `AdminMenuSection.tsx:13–15`, `AdminVotesSection.tsx:13–14` — Prop types use `Dispatch<SetStateAction<Weekday>>` which tightly couples the component API to React's internal state setter type. Use simpler callback types like `(value: Weekday) => void` for better encapsulation and testability.

12. **No loading states for async operations**
    - `App.tsx`, `VotingPage.tsx`, `AdminPage.tsx` — No loading indicators are shown while API calls are in progress. Users get no visual feedback between clicking and the result appearing. At minimum, a loading boolean should disable submit buttons during requests.

13. **No unit test framework configured — coverage not measurable**
    - `package.json` includes only Playwright for E2E tests. There is no vitest/jest setup for unit testing components, hooks, or utility functions. Per the testing-coverage-gate instructions, when coverage cannot be measured, it is treated as failing.

### Minor

14. **Unused `MouseEvent` type annotation in `AdminSectionNav`**
    - `AdminSectionNav.tsx:25` — The `(event: MouseEvent<HTMLButtonElement>)` type annotation is unnecessary since TypeScript infers the event type from the `onClick` handler. Can be simplified to `(event) => { ... }` or just `() => { ... }` since `event.preventDefault()` isn't needed for `type="button"`.

15. **`tsconfig.json` has redundant `allowImportingTsExtensions: false`**
    - This is the default value and adds noise without providing clarity.

16. **Inline ad-hoc interfaces in `api/client.ts`**
    - `client.ts:79–86` — `AdminLoginPayload` and `AdminSessionResponse` are defined inline rather than in `types/domain.ts`. Per project rules, domain types should live in `types/`.

17. **`availableDishes` fallback in `VotingPage` may confuse users**
    - `VotingPage.tsx:113–116` — When no dishes match the slot category, the fallback shows ALL dishes. This silently degrades instead of showing an empty state with a message, which could lead to miscategorized votes.

18. **Missing `<title>` update per route**
    - Only the static HTML `<title>` is set. Consider using `useEffect` or a helmet-like approach to update the document title per page for better browser tab identification.

19. **`admin.spec.ts` test for shortlist uses overly broad selector**
    - `admin.spec.ts:73` — `page.locator('select').selectOption('monday')` matches the first `<select>` on the page, which is fragile when multiple selects exist across tabs.

## Coverage Summary
- Test command: `npx playwright test`
- Result: **Expected to fail** (broken selectors and tab navigation issues in admin tests)
- Coverage: **Not measurable** (no unit test framework; Playwright does not report code coverage by default)
- Target: >= 80%
- Untested critical paths:
  - `CatalogPage` — no tests at all (category filtering, empty state)
  - `WeeklyMenuPage` — no tests (rendering, refresh)
  - Admin member CRUD — no tests (add, rename, delete member)
  - Admin manual menu override — no tests
  - Error states across all pages — no tests
  - `api/client.ts` — no unit tests for request helper, error handling, 204 handling
  - `AdminLoginPage` — no tests for invalid credentials error display

## Score Breakdown
| Category                  | Score (/10) |
|---------------------------|-------------|
| Coding style              | 7           |
| Architecture              | 7           |
| Performance & readability | 7           |
| Tests & coverage          | 3           |

## Global Note: 6/10

## Review Status
**CHANGES REQUIRED**

## Recommended Next Actions

1. **Fix broken Playwright tests** — Update selectors in `admin.spec.ts` to use `page.getByLabel()` or `page.getByRole()` instead of placeholder-based selectors. Add tab navigation steps (click "Catalogue" tab before interacting with catalog inputs). Fix the "Valider le menu" button text in assertions.

2. **Add a unit test framework** — Install vitest and configure it for component/utility testing to enable code coverage measurement. Add unit tests for `api/client.ts`, the category label constants, and the availability map utilities.

3. **Extract duplicated constants** — Create `constants/categories.ts` with `CATEGORY_LABELS_FR` and a shared `initialAvailability` default. Remove the three copies of `categoryLabel`.

4. **Extract `AvailabilityMap` type** — Move to `types/domain.ts` and reuse across `VotingPage` and `AdminPage`.

5. **Remove dead code** — Delete `votesBySlot`, `votes` state, and the `getVotes()` call in `AdminPage` (or implement the votes display feature if intended).

6. **Delete compiled artifacts** — Remove `vite.config.js` and `vite.config.d.ts` from version control and add them to `.gitignore`.

7. **Fix `WeeklyMenuPage` day ordering** — Iterate `WEEK_DAYS` constant instead of `Object.keys(itemsByDay)`.

8. **Fix ARIA roles in `AdminSectionNav`** — Use `role="tab"` + `aria-selected` on buttons, add `role="tabpanel"` on content sections.

9. **Add loading states** — Introduce a loading boolean to disable buttons and show feedback during API calls.

10. **Move inline types from `api/client.ts` to `types/domain.ts`** — `AdminLoginPayload` and `AdminSessionResponse`.
