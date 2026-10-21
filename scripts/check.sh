#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m ruff check backend/apps backend/bcms_backend backend/tests
(
  cd backend
  python manage.py check
  python manage.py makemigrations --check --dry-run
  python -m pytest
)
(
  cd frontend
  npm run lint
  npm run typecheck
  npm test
  npm run build
)
