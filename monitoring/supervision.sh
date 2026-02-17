#!/bin/bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "Starting supervision loop..."
for i in $(seq 1 5); do
    # Récupère le code HTTP (doit être 200)
    code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
    if [ "$code" = "200" ]; then
        echo "Attempt $i: OK"
    else
        echo "Attempt $i: KO (Code $code)"
        exit 1
    fi
    sleep 1
done
echo "Supervision OK"