#!/bin/bash
set -euo pipefail
# Par défaut localhost:5000, mais surchargeable par la CI
BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "Check health on $BASE_URL/health"
curl -fsS "$BASE_URL/health"