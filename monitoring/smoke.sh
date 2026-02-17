#!/bin/bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:5001}"

echo "Check health on $BASE_URL/health"
curl -fsS "$BASE_URL/health" > /dev/null
echo " OK"