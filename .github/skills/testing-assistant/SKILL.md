---
name: testing-assistant
description: 'Automated test generation and coverage analysis for backend (pytest) and frontend. Use for adding unit/integration tests, checking coverage, and maintaining test quality gates.'
argument-hint: 'Specify the component, file, or feature to test (e.g., "dishes router", "voting service")'
---

# Testing Assistant

## When to Use
- Adding new tests for backend API endpoints or services
- Checking test coverage for modified code
- Generating test templates for common patterns
- Ensuring 80%+ coverage for backend changes
- Planning frontend test implementation (currently no tests)

## Procedure
1. **Identify test scope**: Determine if backend (pytest) or frontend (future vitest/jest)
2. **For backend tests**:
   - Generate pytest test functions covering success paths, validation errors, and edge cases
   - Use fixtures from conftest.py for isolation
   - Ensure deterministic behavior testing
   - Run `pytest --cov=app --cov-report=term-missing` to check coverage
3. **For frontend tests** (future):
   - Suggest component tests with React Testing Library
   - Include API mocking for integration tests
   - Propose test setup with vitest
4. **Coverage analysis**:
   - Target 80% minimum for backend
   - Identify untested lines and suggest specific test cases
5. **Validation**: Run tests and verify coverage meets requirements

## Resources
- [Backend test template](./assets/backend_test_template.py)
- [Frontend test template](./assets/frontend_test_template.tsx) (placeholder)
- [Coverage script](./scripts/check_coverage.sh)