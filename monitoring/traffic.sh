#!/bin/bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:5001}"

# On prend le 1er argument ($1) S'IL EXISTE, sinon on prend la variable, sinon 0
MODE="${1:-${SUSPECT_MODE:-0}}"
# --------------------------------

echo "[traffic] Sending normal traffic to $BASE_URL..."
echo "[traffic] DEBUG: Mode recu = $MODE"

# 1. Trafic de fond
for i in $(seq 1 30); do
    curl -fsS "$BASE_URL/health" >/dev/null
done

# 2. Trafic applicatif
curl -s "$BASE_URL/search?q=abc" >/dev/null || true
curl -s "$BASE_URL/search?q=test" >/dev/null || true

# 3. Mode "Suspect"
if [ "$MODE" = "1" ]; then
    echo "[traffic] !!! GENERATING SUSPECT TRAFFIC !!!"
    curl -s "$BASE_URL/report?file=../../etc/passwd" >/dev/null || true
    curl -s "$BASE_URL/debug/run?cmd=id" >/dev/null || true
else
    echo "[traffic] Mode normal (pas d'attaque)."
fi

echo "[traffic] Done."