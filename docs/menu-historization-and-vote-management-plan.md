# Menu Historization & Vote Management Plan

## Context

This plan covers three major features:
1. **Menu Historization** - Archive menus by week with date-based navigation
2. **Vote Deletion on Validation** - Clear votes when menu is finalized
3. **Thursday-to-Thursday Menu Cycle** - Automated weekly menu cycle with specific date ranges

### Current Architecture

- **Storage**: Single-table DynamoDB with in-memory state
- **Menu Model**: Abstract weekly menu (Monday-Sunday) with no calendar dates
- **Votes**: Stored with day-of-week (e.g., "monday") but no specific date
- **Finalization**: Single boolean flag (`_finalized`), no date tracking
- **Automation**: None - admin manually manages everything

### Architecture Improvement: Interface-Based Design

**Current Issue**: `store.py` is 634 lines mixing in-memory logic, DynamoDB operations, and conditional checks (`if _USE_DYNAMODB`) throughout.

**Proposed Solution**: Use Protocol-based interface with separate implementations:

```
backend/app/services/
├── store_interface.py      # Protocol defining Store interface
├── store_inmemory.py       # Pure in-memory implementation (~300 lines)
├── store_dynamodb.py       # DynamoDB implementation (~350 lines)
└── store.py                # Factory: creates correct implementation
```

**Benefits**:
- ✅ Each implementation is simpler and focused
- ✅ No conditional checks scattered in business logic
- ✅ Easier to test (can test each implementation independently)
- ✅ Easier to maintain and understand
- ✅ Follows Interface Segregation Principle

**Interface Definition** (`store_interface.py`):
```python
from abc import ABC, abstractmethod
from app.schemas.common import *

class StoreInterface(ABC):
    """Abstract interface for the meal planner store."""
    
    # Dish operations
    @abstractmethod
    def list_dishes(self) -> list[Dish]: ...
    
    @abstractmethod
    def create_dish(self, payload: CreateDishRequest) -> Dish: ...
    
    @abstractmethod
    def update_dish(self, dish_id: str, payload: CreateDishRequest) -> Dish: ...
    
    @abstractmethod
    def delete_dish(self, dish_id: str) -> None: ...
    
    # Member operations
    @abstractmethod
    def list_members(self) -> list[str]: ...
    
    @abstractmethod
    def add_member(self, name: str) -> str: ...
    
    @abstractmethod
    def update_member(self, current_name: str, new_name: str) -> str: ...
    
    @abstractmethod
    def delete_member(self, name: str) -> None: ...
    
    # Vote operations
    @abstractmethod
    def list_votes(self) -> list[Vote]: ...
    
    @abstractmethod
    def add_vote(self, payload: CreateVoteRequest) -> Vote: ...
    
    # Menu operations
    @abstractmethod
    def generate_weekly_menu(self) -> WeeklyMenuResponse: ...
    
    @abstractmethod
    def validate_menu(self) -> WeeklyMenuResponse: ...
    
    @abstractmethod
    def unvalidate_menu(self) -> WeeklyMenuResponse: ...
    
    # ... and other methods
```

**Factory Pattern** (`store.py`):
```python
import os
from .store_interface import StoreInterface
from .store_inmemory import InMemoryStore
from .store_dynamodb import DynamoDBStore

_store: StoreInterface | None = None

def get_store() -> StoreInterface:
    """Get the store singleton based on BACKEND_PERSISTENCE_MODE."""
    global _store
    if _store is None:
        mode = os.getenv("BACKEND_PERSISTENCE_MODE", "inmemory").lower()
        if mode == "dynamodb":
            _store = DynamoDBStore()
        else:
            _store = InMemoryStore()
    return _store

def reset_store() -> None:
    """Reset the store singleton (useful for testing)."""
    global _store
    _store = None

# Keep backward compatibility with existing imports
def __getattr__(name: str):
    """Delegate module-level function calls to store instance."""
    store = get_store()
    if hasattr(store, name):
        return getattr(store, name)
    raise AttributeError(f"'{name}' not found")
```

**Implementation Differences**:

| Aspect | InMemoryStore | DynamoDBStore |
|--------|---------------|---------------|
| State | Python dicts/lists | DynamoDB single-table |
| Load | Instant | Query DynamoDB on init |
| Persist | No-op | Write to DynamoDB |
| Session | Not supported | Full session management |
| Complexity | ~300 lines | ~350 lines |

**Migration Strategy**:
- Keep existing `store.py` API intact for routers (no changes needed)
- Routers continue to call `store.list_dishes()`, `store.add_vote()`, etc.
- Factory pattern is transparent to callers
- Can swap implementations via environment variable

This refactoring should be done **BEFORE** implementing the historization features to keep the codebase clean and manageable.

---

## Feature 1: Menu Historization

### Goal
Allow users to view past menus by selecting a specific week's date range on the public weekly menu page.

### Technical Approach

#### 1.1 Backend: New Menu Period Model

**New Pydantic Schema** (`backend/app/schemas/common.py`):
```python
class MenuPeriod(BaseModel):
    id: str  # e.g., "2026-04-16" (Thursday start date as ISO format)
    start_date: str  # ISO date (Thursday)
    end_date: str  # ISO date (following Wednesday)
    display_label: str  # e.g., "16/04 - 23/04"
    created_at: str  # ISO timestamp
    finalized_at: str | None  # ISO timestamp when finalized
    menu: WeeklyMenuResponse  # The actual menu content
    vote_counts: dict[str, dict[str, int]]  # Optional: vote stats per slot
```

**New DynamoDB Table Pattern**:
| Entity | PK | SK | GSI1PK | GSI1SK |
|---|---|---|---|---|
| Menu Period | `PERIOD#<start_date>` | `METADATA` | `PERIODS` | `PERIOD#<start_date>` |

**Updated Store Service** (`backend/app/services/store.py`):
- Add `_menu_periods: dict[str, MenuPeriod] = {}` to in-memory state
- Add `_active_period_id: str | None` to track current period
- New functions:
  - `create_menu_period(start_date: str) -> MenuPeriod`
  - `get_menu_period(period_id: str) -> MenuPeriod | None`
  - `list_menu_periods(limit: int = 10) -> list[MenuPeriod]`
  - `get_active_period() -> MenuPeriod | None`
  - `set_active_period(period_id: str)`
  - `archive_current_period() -> MenuPeriod` (called during validation)

#### 1.2 Backend: Updated Menu Generation

**Updated `generate_weekly_menu()`**:
- Accept optional `period_id` parameter
- If `period_id` provided, return archived menu from that period
- If no `period_id`, return current active period's menu
- Keep existing logic intact

**New API Endpoint** (`backend/app/routers/menu.py`):
```
GET /weekly-menu?period=<period_id>  # Get specific historical menu
GET /menu-periods  # List available menu periods (for date picker)
```

#### 1.3 Frontend: Date Picker on Public Menu Page

**Updated `WeeklyMenuPage.tsx`**:
- Add week selector component (dropdown or date picker)
- Fetch available periods from `/menu-periods`
- When a period is selected, fetch `/weekly-menu?period=<period_id>`
- Display the period's `display_label` (e.g., "Menu du 16/04 au 23/04")
- Show "Menu de la semaine" by default (current active period)

**New Component** (`frontend/src/components/WeekSelector.tsx`):
```tsx
interface WeekSelectorProps {
  periods: MenuPeriod[];
  selectedPeriod: string | null;
  onSelect: (periodId: string | null) => void;
}
```
- Dropdown showing available periods with labels
- "Menu de la semaine" as default option
- Previous weeks listed below

#### 1.4 Frontend: Updated API Client

**New/Updated Functions** (`frontend/src/api/client.ts`):
```typescript
export function getMenuPeriods(): Promise<MenuPeriod[]>
export function getWeeklyMenu(periodId?: string): Promise<WeeklyMenuResponse>
```

---

## Feature 2: Vote Deletion on Menu Validation

### Goal
When admin validates/finalizes the menu, all votes for the current period are permanently deleted.

### Technical Approach

#### 2.1 Backend: Vote Deletion Logic

**Architecture Note**: Following the existing pattern in `store.py`, all operations work **in-memory first**, with DynamoDB as a persistence layer. We do NOT create separate `_delete_all_votes_from_dynamodb()` functions. Instead:
- Modify in-memory state (`_votes.clear()`)
- Call helper to persist to DynamoDB (`_delete_all_votes()`)
- The helper checks `_USE_DYNAMODB` flag and only acts if needed

This ensures the application works identically in both `inmemory` and `dynamodb` modes.

**Updated Store Service** (`backend/app/services/store.py`):

**Updated `validate_menu()` function**:
```python
def validate_menu():
    _ensure_store_loaded()
    global _finalized, _final_weekly_menu

    if _finalized and _final_weekly_menu is not None:
        return _final_weekly_menu

    # 1. Archive current period with menu content
    archive_current_period()

    # 2. Delete all votes (in-memory + DynamoDB persistence)
    _delete_all_votes()
    _votes.clear()

    # 3. Set finalized flag and generate menu
    _final_weekly_menu = generate_weekly_menu(allow_generate_final=True)
    _finalized = True
    _final_weekly_menu = WeeklyMenuResponse(
        items=_final_weekly_menu.items,
        finalized=True,
        shortlists=_final_weekly_menu.shortlists,
    )
    _persist_config_finalized(True)
    
    return _final_weekly_menu
```

**New Function**: `_delete_all_votes()`
- Follows existing pattern: checks `_USE_DYNAMODB` flag
- If DynamoDB: batch delete all votes from table
- In-memory state is cleared separately with `_votes.clear()`
- Reuses existing `_delete_vote_from_db()` helper for each vote

#### 2.2 Frontend: Updated Validation UI

**Updated `AdminMenuSection.tsx`**:
- Add warning message near "Valider le menu" button:
  > "⚠️ La validation du menu supprimera définitivement tous les votes de la période en cours."
- Add confirmation dialog before validation (using `window.confirm` or custom modal)
- Keep manual "Valider le menu" button for admin override before auto-finalization
- Add info message: "Le menu sera automatiquement validé lundi à 23h59 si non validé manuellement"

---

## Feature 3: Thursday-to-Thursday Menu Cycle (Automated)

### Goal
Automate the menu lifecycle with a Thursday-to-Thursday cycle:
- **Thursday → Wednesday**: Menu covers 8 days (Thu, Fri, Sat, Sun, Mon, Tue, Wed, Thu)
- **Friday → Sunday**: Voting period opens
- **Monday 11:59 PM**: Menu auto-finalizes (with manual override available)
- **Tuesday**: New period is created, votes open Friday

### Technical Approach

#### 3.1 Backend: Date-Based Period Management

**New Utility Module** (`backend/app/services/period_utils.py`):
```python
from datetime import datetime, timedelta

def get_current_period() -> dict:
    """
    Calculate the current menu period based on today's date.
    Returns dict with:
    - start_date: Thursday (ISO string)
    - end_date: Next Wednesday (ISO string)
    - period_id: start_date string
    - display_label: "DD/MM - DD/MM"
    """
    today = datetime.now()
    # Find most recent Thursday
    days_since_thursday = (today.weekday() - 3) % 7
    thursday = today - timedelta(days=days_since_thursday)
    
    start_date = thursday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=7)  # Next Wednesday
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "period_id": start_date.strftime("%Y-%m-%d"),
        "display_label": f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"
    }

def is_voting_open() -> bool:
    """
    Voting is open from Friday 00:00 to Sunday 23:59.
    """
    today = datetime.now()
    weekday = today.weekday()  # 0=Monday, 4=Friday, 6=Sunday
    return weekday in (4, 5, 6)  # Friday, Saturday, Sunday

def is_finalization_time() -> bool:
    """
    Check if it's Monday evening (after 23:59 - end of day).
    """
    now = datetime.now()
    return now.weekday() == 0 and now.hour >= 23 and now.minute >= 59  # Monday 11:59 PM

def should_create_new_period() -> bool:
    """
    Check if we should create a new period (Tuesday after finalization).
    """
    now = datetime.now()
    return now.weekday() == 1 and now.hour >= 0  # Tuesday 12:00 AM
```

#### 3.2 Backend: Automated Period Creation & Finalization

**Updated Store Service** - Add auto-management functions:

```python
async def ensure_active_period():
    """
    Check if active period exists and is current.
    If not, create new period or activate existing one.
    Called on every API request (lightweight check).
    """
    active = await get_active_period()
    current = period_utils.get_current_period()
    
    if not active or active.id != current["period_id"]:
        # Create new period
        await create_menu_period(current["start_date"])
        await set_active_period(current["period_id"])
        
        # Reset votes and availability for new period
        await _reset_period_state()

async def auto_finalize_if_needed():
    """
    Check if it's Monday 11:59 PM and auto-finalize.
    Called periodically or on API requests.
    Admin can still manually finalize before this time.
    """
    if not _finalized and period_utils.is_finalization_time():
        await validate_menu()  # This will archive and clear votes
```

**Updated API Middleware/Router** (`backend/app/routers/menu.py` and `backend/app/routers/admin.py`):
- Add dependency that calls `ensure_active_period()` on relevant endpoints
- Ensures current period is always active before processing requests

#### 3.3 Backend: Updated Vote Validation

**Updated `add_vote()` function**:
```python
async def add_vote(payload: VotePayload):
    # Check if voting period is open (Friday-Sunday)
    if not period_utils.is_voting_open():
        raise ValueError("Voting is only open from Friday to Sunday")
    
    # Rest of existing validation...
```

#### 3.4 Backend: Updated Menu Display with Dates

**Updated `WeeklyMenuResponse`**:
```python
class WeeklyMenuResponse(BaseModel):
    period_id: str  # e.g., "2026-04-16"
    period_label: str  # e.g., "16/04 - 23/04"
    start_date: str  # ISO date
    end_date: str  # ISO date
    items: list[MenuItem]
    finalized: bool = False
    shortlists: dict[Weekday, dict[Meal, list[str]]] = Field(default_factory=dict)
```

**Updated `generate_weekly_menu()`**:
- Include period metadata in response
- Map abstract weekdays to actual dates based on period start date

#### 3.5 Frontend: Updated Weekly Menu Display

**Updated `WeeklyMenuPage.tsx`**:
- Display period label at top: "Menu du {start_date} au {end_date}"
- Show actual dates for each day in the table:
  ```
  Jeudi 16/04 | Plats midi | Plats soir
  Vendredi 17/04 | ... | ...
  ```

**New Helper Function**:
```typescript
function getDayDate(periodStart: string, weekday: Weekday): string {
  // Calculate actual date for a weekday within the period
  // Returns formatted date like "16/04"
}
```

**Updated Table Headers**:
```tsx
<thead>
  <tr>
    <th>Jour</th>
    <th>Déjeuner</th>
    <th>Dîner</th>
  </tr>
</thead>
<tbody>
  {WEEK_DAYS_ORDERED.map((day) => (
    <tr key={day}>
      <td>
        {WEEK_DAY_LABELS_FR[day]} {getDayDate(menu.start_date, day)}
      </td>
      <td>{/* lunch content */}</td>
      <td>{/* dinner content */}</td>
    </tr>
  ))}
</tbody>
```

#### 3.6 Frontend: Updated Admin Page

**Updated `AdminPage.tsx`**:
- Display current period dates at top
- Show voting status (open/closed based on day)
- Auto-finalization status indicator

**Updated `AdminMenuSection.tsx`**:
- Remove manual "Valider le menu" button OR keep it for manual override
- Add info message: "Le menu sera automatiquement validé lundi soir à 20h"
- Show countdown or status: "Finalisation dans X heures"

---

## Implementation Phases

### Phase 0: Store Refactoring (NEW - Do This First!)
**Estimated scope**: Split store.py into interface + 2 implementations

**Goal**: Refactor the monolithic `store.py` (634 lines) into a clean interface-based architecture before adding historization features.

**Why First?**:
- Reduces complexity before adding new features
- Makes future implementations cleaner (separate concerns)
- Easier to test each implementation independently
- Prevents store.py from becoming 1000+ lines with period management

**Steps**:

1. **Create `store_interface.py`** - Abstract Protocol/ABC
   - Define all public methods as abstract methods
   - Document each method with docstrings
   - Include type hints for all parameters and returns

2. **Create `store_inmemory.py`** - Pure in-memory implementation
   - Extract all in-memory logic from current `store.py`
   - Remove all `_USE_DYNAMODB` checks (always no-op for persistence)
   - Remove all `_persist_*` and `_delete_*_from_db` helpers
   - Keep `_ensure_store_loaded()` as no-op
   - Expected: ~300 lines of clean, focused code

3. **Create `store_dynamodb.py`** - DynamoDB implementation
   - Extract all DynamoDB logic from current `store.py`
   - Keep all `_persist_*` and `_delete_*_from_db` helpers
   - Keep all `_load_*_from_db()` methods
   - Keep `_query_pk()`, `_query_gsi1()`, `_put_item()`, `_delete_item()`
   - Initialize DynamoDB connection in `__init__()`
   - Expected: ~350 lines with all DynamoDB-specific logic

4. **Update `store.py`** - Factory pattern
   - Implement `get_store()` factory function
   - Add `__getattr__()` for backward compatibility
   - Keep `reset_store()` for testing
   - Very small file (~40 lines)

5. **Update imports in routers**
   - Change `from app.services import store` to work with factory
   - OR keep existing imports working via `__getattr__()` (recommended)
   - No changes to router logic needed

6. **Test both implementations**
   - Run existing test suite with `BACKEND_PERSISTENCE_MODE=inmemory`
   - Run with `BACKEND_PERSISTENCE_MODE=dynamodb`
   - Verify identical behavior

**Files Created**:
- `backend/app/services/store_interface.py` (~100 lines)
- `backend/app/services/store_inmemory.py` (~300 lines)
- `backend/app/services/store_dynamodb.py` (~350 lines)

**Files Modified**:
- `backend/app/services/store.py` - Becomes factory (~40 lines, was 634)

**Estimated Time**: 2-3 hours of refactoring

**Success Criteria**:
- ✅ All existing tests pass with both modes
- ✅ No changes needed to any router files
- ✅ Each implementation file is < 400 lines
- ✅ No `if _USE_DYNAMODB` checks in business logic
- ✅ Clear separation of concerns

---

### Phase 1: Foundation (Backend Core)
**Estimated scope**: Database schema changes, new models, period utilities

1. **Create `period_utils.py`** - Date calculation utilities
2. **Update Pydantic schemas** - Add `MenuPeriod`, update `WeeklyMenuResponse`
3. **Update DynamoDB schema** - Add period table pattern
4. **Implement period management in store.py**:
   - `create_menu_period()`
   - `get_active_period()`
   - `set_active_period()`
   - `archive_current_period()`
   - `ensure_active_period()`

### Phase 2: Vote Deletion & Menu Validation
**Estimated scope**: Vote cleanup, validation flow updates

5. **Implement vote deletion in `validate_menu()`**
   - DynamoDB batch delete
   - In-memory state cleanup
6. **Add confirmation dialog in frontend** (`AdminMenuSection.tsx`)
7. **Add warning message about vote deletion**

### Phase 3: Automated Period Lifecycle
**Estimated scope**: Automation, scheduling, validation rules

8. **Implement `auto_finalize_if_needed()`**
9. **Update `add_vote()` to check voting window** (Friday-Sunday)
10. **Add period creation trigger** (`should_create_new_period()`)
11. **Update API endpoints to call `ensure_active_period()`**
12. **Update `generate_weekly_menu()` to include period metadata**

### Phase 4: Frontend Date Display
**Estimated scope**: UI updates for dates, week selector

13. **Create `WeekSelector.tsx` component**
14. **Update `WeeklyMenuPage.tsx`**:
    - Add week selector
    - Display period dates
    - Show actual dates for each day
15. **Update API client with period support**
16. **Update `AdminPage.tsx` to show current period info**

### Phase 5: Testing & Polish
**Estimated scope**: Tests, edge cases, UX improvements

17. **Add backend tests** for period calculations, auto-finalization, vote deletion
18. **Add frontend tests** for date formatting, week selector
19. **Test edge cases**:
    - Timezone handling
    - Menu period transitions
    - Vote window boundaries
    - Concurrent finalization attempts
20. **Add loading states and error handling**

---

## File Changes Summary

### Phase 0: Store Refactoring Files

#### Backend Files to Create
- `backend/app/services/store_interface.py` - Abstract interface (ABC/Protocol) for store
- `backend/app/services/store_inmemory.py` - Pure in-memory implementation (~300 lines)
- `backend/app/services/store_dynamodb.py` - DynamoDB implementation (~350 lines)

#### Backend Files to Modify
- `backend/app/services/store.py` - Becomes factory function (~40 lines, was 634 lines)

#### Backend Files to Review (no changes expected)
- All router files in `backend/app/routers/` - Should work via `__getattr__()` delegation

---

### Phase 1-5 Files (Original Plan)

### Backend Files to Create
- `backend/app/services/period_utils.py` - Date and period utilities
- `backend/app/schemas/period.py` - MenuPeriod schema (optional, can add to common.py)

### Backend Files to Modify
- `backend/app/schemas/common.py` - Update `WeeklyMenuResponse`, add `MenuPeriod`
- `backend/app/services/store.py` - Period management, vote deletion, auto-finalization
- `backend/app/services/store_inmemory.py` - Add period methods to in-memory store
- `backend/app/services/store_dynamodb.py` - Add period methods to DynamoDB store
- `backend/app/routers/menu.py` - Add `/menu-periods` endpoint, update `/weekly-menu`
- `backend/app/routers/admin.py` - Update validation endpoints
- `backend/app/routers/votes.py` - Add voting window validation

### Frontend Files to Create
- `frontend/src/components/WeekSelector.tsx` - Week period selector
- `frontend/src/types/period.ts` - MenuPeriod TypeScript type (optional)

### Frontend Files to Modify
- `frontend/src/types/domain.ts` - Update `WeeklyMenuResponse` with period fields
- `frontend/src/api/client.ts` - Add `getMenuPeriods()`, update `getWeeklyMenu()`
- `frontend/src/pages/WeeklyMenuPage.tsx` - Add week selector, display dates
- `frontend/src/pages/AdminPage.tsx` - Show period info, voting status
- `frontend/src/components/admin/AdminMenuSection.tsx` - Add warning, confirmation dialog
- `frontend/src/components/admin/AdminVotesSection.tsx` - Show voting window status

### Frontend Files to Review (no changes expected)
- `frontend/src/constants/weekdays.ts` - May need reorder for Thu-Wed cycle
- `frontend/src/constants/meals.ts` - No changes needed
- `frontend/src/components/admin/AdminSectionNav.tsx` - No changes needed

---

## Key Considerations & Edge Cases

### Timezone Handling
- All dates should be in UTC or Europe/Paris timezone
- Be consistent across backend and frontend
- Consider DST transitions

### Voting Window Edge Cases
- What if admin validates manually before Monday? → Votes still deleted
- What if period creation fails? → Fallback to manual creation
- What happens to votes cast outside the window? → Rejected with clear error message

### Period Transitions
- Ensure no gap between periods (old ends Wednesday, new starts Thursday)
- Handle late menu finalization gracefully
- Allow admin to view/modify archived periods (read-only)

### DynamoDB Batch Operations
- Vote deletion may need pagination if many votes
- Use batch write operations for efficiency
- Handle throttling and retries

### Backward Compatibility
- Existing menus have no period data → migrate or handle gracefully
- API clients may not expect period fields → make optional with defaults
- Frontend should work with old backend responses during transition

---

## Testing Strategy

### Backend Tests
```python
# test_period_utils.py
def test_get_current_period_on_thursday()
def test_get_current_period_on_monday()
def test_is_voting_open_friday()
def test_is_voting_open_monday()
def test_is_finalization_time_monday_1159pm()

# test_store.py
def test_create_menu_period()
def test_archive_current_period()
def test_validate_menu_deletes_votes()
def test_ensure_active_period_creates_new()
def test_auto_finalize_on_monday_night()
def test_manual_finalize_before_auto()

# test_votes.py
def test_vote_outside_window_rejected()
def test_vote_inside_window_accepted()
```

### Frontend Tests
```typescript
// test WeekSelector.tsx
it('displays current week by default')
it('calls onSelect when period changes')

// test WeeklyMenuPage.tsx
it('displays period label')
it('shows correct dates for each day')

// test date utilities
it('calculates correct date for Thursday in period')
it('handles week boundary correctly')
```

### Integration Tests
- Full cycle: Create period → Vote → Finalize → Archive → Create new period
- View historical menu from public page
- Vote deletion verified after finalization

---

## Migration Plan

### Database Migration
1. Deploy new DynamoDB schema (add period table pattern)
2. Create initial period for current week manually or via script
3. Migrate existing menu to new period structure
4. Keep backward compatibility for existing votes

### Frontend Migration
1. Deploy updated API client (handles both old and new responses)
2. Deploy updated components with period support
3. Monitor for errors during transition

### Rollback Plan
- Keep old API endpoints functional during transition
- Feature flag for new period functionality
- Can disable auto-finalization if issues arise

---

## Open Questions (Resolved)

✅ **1. Manual Finalization Override** - DECIDED: Yes, allow it
   - Admin can manually finalize menu anytime before Monday 11:59 PM
   - Auto-finalization serves as a safety net

✅ **2. Historical Menu Retention** - DECIDED: 12 weeks (3 months)
   - Keep last 12 weeks of menus in DynamoDB
   - Automatic cleanup of periods older than 12 weeks

✅ **3. Auto-Finalization Time** - DECIDED: Monday 11:59 PM
   - Finalizes at end of Monday (23:59)
   - Gives admin full Monday to make last-minute changes

✅ **4. No Votes in a Slot** - UNCHANGED: Keep current behavior
   - Display "Pas encore de gagnant" or empty slot
   - No fallback mechanism needed

✅ **5. Admin View of Past Periods** - DECIDED: Public page only
   - Historical menus only accessible via public weekly menu page
   - Admin page focuses on current week management only

---

## Success Metrics

- ✅ Users can view any past menu by selecting a week
- ✅ Votes are automatically deleted when menu is finalized
- ✅ Menu cycle runs automatically from Thursday to Thursday
- ✅ Voting only opens Friday-Sunday
- ✅ Auto-finalization happens Monday evening
- ✅ Public menu page shows actual dates for each day
- ✅ No manual intervention required for weekly cycle
- ✅ All tests pass (backend + frontend)
- ✅ Zero downtime deployment

---

## Next Steps

1. Review and approve this plan
2. Answer open questions
3. Begin Phase 1 implementation
4. Schedule deployment timeline
5. Set up monitoring and alerts for auto-finalization
