#!/bin/bash
# Check coverage script for backend

cd backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
echo "Coverage check complete. Ensure 80% minimum is met."