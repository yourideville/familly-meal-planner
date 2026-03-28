# Plan: Admin Voting and Catalog Extensions

## TL;DR
Extend backend and frontend to support:
- Admin-managed vote availability by day + meal (lunch/dinner)
- Family member management
- One vote per member per slot (new vote updates existing vote)
- Weekly menu with lunch + dinner slots
- Catalog categories: `lunch`, `dinner`, `weekends_lunch`, `saturday_dinner`

Preserve existing architecture (FastAPI + in-memory store + React UI), add schema/store updates, and ensure full test coverage (pytest + Playwright).

---

## Phase 1: Domain Model

### Backend models/schemas
- `FamilyMember`: `name`
- `VoteSlot`: `day`, `meal`, `available`
- `DishCategory` enum: `lunch`, `dinner`, `weekends_lunch`, `saturday_dinner`
- `Vote` uniqueness: `member` + `day` + `meal`

### Frontend types
- `frontend/src/types/domain.ts` updates
- new `frontend/src/constants/meals.ts`
- existing `frontend/src/constants/weekdays.ts` stays

### In-memory store
- `backend/app/services/store.py` holds:
  - `members: List[str]`
  - `vote_availability` per day/meal
  - dish category metadata
  - single-vote-update behavior

---

## Phase 2: Backend Router/Service

### Admin endpoints
- `GET /admin/members`
- `POST /admin/members`
- `PUT /admin/members/{name}`
- `DELETE /admin/members/{name}`
- `GET /admin/vote-availability`
- `PUT /admin/vote-availability` (payload: slot list)
- `GET /admin/dishes/categories`
- `PUT /admin/dishes/{id}/category` or include category in existing dish payload

### Voting endpoint
- `POST /votes`:
  - validate member exists
  - validate slot (`day`, `meal`) available
  - update existing vote for same member/day/meal
  - frontend selectors only expose open day/meal combinations based on admin settings

### Weekly menu engine
- slot-based selection by `day` + `meal` (lunch/dinner)
- category constraints:
  - Mon-Fri lunch → `lunch`
  - Mon-Fri dinner → `dinner`
  - Sat/Sun lunch → `weekends_lunch`
  - Sat dinner → `saturday_dinner`
- optional fallback to generic categories
- preserve shortlist/manual override with meal dimension

---

## Phase 3: Frontend Behavior

### Admin page (`frontend/src/pages/AdminPage.tsx`)
- member CRUD controls
- vote availability table (days × meals)
- category in dish catalog items
- show shortlists and overrides with meal context

### Voting page (`frontend/src/pages/VotingPage.tsx`)
- member selector
- day + meal selector filtered dynamically from admin vote availability
- closed vote slots are not selectable
- dish filtering by slot category + shortlist
- submit vote with member/day/meal/dish

### Weekly menu page (`frontend/src/pages/WeeklyMenuPage.tsx`)
- 7-day grid with lunch/dinner cells
- unavailable slots marked clearly
- chosen dish or placeholder text

### Catalog page (`frontend/src/pages/CatalogPage.tsx`)
- category filters and labels
- dish creation includes category

---

## Phase 4: Testing & Quality Gate

### Backend tests
- new `backend/tests/test_admin_members.py`
- update `backend/tests/test_votes_and_menu.py` with:
  - member CRUD + validation
  - availability enforcement
  - one vote per member per slot behavior
  - category-based menu selection

### Frontend tests
- `test-results/tests/admin.spec.ts`: admin config available slots and member management
- `test-results/tests/voting.spec.ts`: vote + update flows, menu coverage

### Coverage
- `pytest --cov=app --cov-report=term-missing` (target ≥ 80%)
- `npm run test`

---

## Phase 5: Docs
1. This file: `docs/feature-admin-voting-categories-plan.md`
2. Update `docs/mvp.md` user stories
3. Add endpoint summary and acceptance criteria

---

## Relevant files
- `backend/app/services/store.py`
- `backend/app/routers/votes.py`
- `backend/app/routers/admin.py`
- `backend/app/schemas/common.py`
- `backend/tests/test_votes_and_menu.py`
- `backend/tests/conftest.py`
- `frontend/src/pages/AdminPage.tsx`
- `frontend/src/pages/VotingPage.tsx`
- `frontend/src/pages/WeeklyMenuPage.tsx`
- `frontend/src/pages/CatalogPage.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/types/domain.ts`
- `frontend/src/constants/weekdays.ts`
- `frontend/src/constants/meals.ts`

---

## Verification checklist
- [ ] `GET/POST/PUT/DELETE /admin/members`
- [ ] `GET/PUT /admin/vote-availability`
- [ ] `POST /votes` with member/day/meal validation
- [ ] voting UI only allows open day/meal combinations from admin availability
- [ ] `GET /weekly-menu` includes lunch/dinner slots
- [ ] `pytest` + `npm run test` pass
- [ ] manual scenario: admin -> vote -> menu works

---

## Key design decisions
- members are unique by name
- one vote per member per day+meal
- weekend categories are explicit as requested
- same shortlist/override semantics, extended to meal

---

## Further considerations
1. Persist to DynamoDB tables: Members, Availability, Votes, Dishes
2. Add role-based admin auth (future)
3. Add vote history by member (future)
