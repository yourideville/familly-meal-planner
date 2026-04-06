---
name: testing-assistant
description: 'Automated test generation and coverage analysis for backend (pytest) and frontend (Playwright). Use for adding unit/integration tests, checking coverage, and maintaining test quality gates.'
argument-hint: 'Specify the component, file, or feature to test (e.g., "dishes router", "admin page", "voting service")'
---

# Testing Assistant

## When to Use
- Adding new tests for backend API endpoints or services
- Checking test coverage for modified code
- Generating test templates for common patterns
- Ensuring 80%+ coverage for backend changes
- Adding Playwright integration tests for frontend pages and workflows
- Testing end-to-end user interactions

## Procedure
1. **Identify test scope**: Determine if backend (pytest), frontend integration (Playwright), or both
2. **For backend tests**:
   - Generate pytest test functions covering success paths, validation errors, and edge cases
   - Use fixtures from conftest.py for isolation
   - Ensure deterministic behavior testing
   - Run `pytest --cov=app --cov-report=term-missing` to check coverage
3. **For frontend integration tests (Playwright)**:
   - Generate Playwright test specs for page interactions and API calls
   - Test user workflows: navigation, form submissions, data updates
   - Include assertions for UI state changes and API responses
   - Run `npm run test` to execute tests across multiple browsers
4. **Coverage analysis**:
   - Target 80% minimum for backend
   - Identify untested lines and suggest specific test cases
   - For frontend, focus on critical user paths and error scenarios
5. **Validation**: Run tests and verify coverage meets requirements

## Resources
- [Backend test template](./assets/backend_test_template.py)
- [Playwright test template](./assets/playwright_test_template.spec.ts)
- [Coverage script](./scripts/check_coverage.sh)