#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT/backend"
echo "==> [HarvestFlow] Backend ruff check..."
uv run ruff check .
echo "==> [HarvestFlow] Backend pytest..."
uv run pytest -q

cd "$PROJECT_ROOT/frontend"
echo "==> [HarvestFlow] Frontend lint & test..."
npm run lint
npm test

echo "✓ 全部检查通过 (HarvestFlow)"
