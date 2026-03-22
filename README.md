# Family Meal Planner MVP

Very simple local MVP:
- Backend: FastAPI with in-memory data (no persistence).
- Frontend: React + Vite.

## Run with Docker Compose

From repo root:

```bash
docker compose up -d --build
```

Then open:
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

Stop:

```bash
docker compose down
```

## Testing

### Backend Tests

```bash
cd backend
activate-python  # Activate virtual environment
pytest --cov=app --cov-report=term-missing
```

Current status: ✅ 8 tests passing, 85.24% coverage (exceeds 80% requirement)

### Frontend Integration Tests (Playwright)

```bash
cd frontend
npm install
npx playwright install
npm run test
```

Current status: ⚠️ Tests configured but browser launch fails in Docker container due to missing dependencies. Run locally with Node.js 20+ for full testing.

### Recent Fixes
- Fixed admin menu validation bug (finalized status not updating)
- Added Playwright integration tests for admin page
- Updated testing-assistant skill with Playwright support

Or with UI:

```bash
npm run test:ui
```
