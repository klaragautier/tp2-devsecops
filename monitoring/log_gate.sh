#!/bin/bash
set -euo pipefail

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-compose.staging.yml}"
SERVICE="${SERVICE:-catalog}"
BASE_URL="${BASE_URL:-http://localhost:5001}"

# --- RECUPERATION ROBUSTE ---
# On prend la variable d'env, sinon 0
SUSPECT_MODE="${SUSPECT_MODE:-0}"
# ----------------------------

MAX_5XX="${MAX_5XX:-0}"
MAX_P95_MS="${MAX_P95_MS:-2000}"
MAX_TRAV="${MAX_TRAV:-0}"
MAX_CMD="${MAX_CMD:-0}"

# Auto-détection Python
if command -v python &> /dev/null; then
    PYTHON_CMD=python
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python.exe
fi

mkdir -p reports
START_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "[gate] Timestamp : $START_TS"
echo "[gate] Mode Suspect demande : $SUSPECT_MODE"

echo "[gate] 1. Sante..."
BASE_URL="$BASE_URL" bash monitoring/smoke.sh >/dev/null
BASE_URL="$BASE_URL" bash monitoring/supervision.sh >/dev/null

echo "[gate] 2. Generation de trafic..."
BASE_URL="$BASE_URL" bash monitoring/traffic.sh "$SUSPECT_MODE"

echo "[gate] 3. Logs..."
docker compose -f "$COMPOSE_FILE" logs --since "$START_TS" --no-log-prefix "$SERVICE" > "reports/${SERVICE}_logs.jsonl"

if [ ! -s "reports/${SERVICE}_logs.jsonl" ]; then
    echo "[gate] ERREUR: Aucun log."
    exit 1
fi

echo "[gate] 4. Analyse..."
$PYTHON_CMD monitoring/log_metrics.py "reports/${SERVICE}_logs.jsonl" "reports/log_report.json"

echo "[gate] 5. Verdict..."
TRAV=$($PYTHON_CMD -c 'import json; print(json.load(open("reports/log_report.json"))["patterns"]["path_traversal_hits"])')
CMD=$($PYTHON_CMD -c 'import json; print(json.load(open("reports/log_report.json"))["patterns"]["cmd_param_hits"])')

echo "--------------------------------"
echo " - Path Traversal : $TRAV"
echo " - Command Injection : $CMD"
echo "--------------------------------"

FAIL=0
if [ "$TRAV" -gt "$MAX_TRAV" ]; then FAIL=1; fi
if [ "$CMD" -gt "$MAX_CMD" ]; then FAIL=1; fi

if [ "$FAIL" -eq 1 ]; then
    echo "[gate] ❌ GATE FAILED"
    exit 1
else
    echo "[gate] ✅ GATE PASSED"
    exit 0
fi