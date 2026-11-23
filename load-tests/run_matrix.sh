#!/usr/bin/env bash
# Roda o benchmark em vários níveis de concorrência (diferentes cargas de trabalho).
# Uso: ./run_matrix.sh <label> [requests] ["1 10 50 100"]
#   ./run_matrix.sh python 500 "1 10 50"
set -euo pipefail
cd "$(dirname "$0")"

LABEL="${1:-python}"
REQUESTS="${2:-500}"
CONCURRENCIES="${3:-1 10 50}"
PY="${BENCH_PYTHON:-../python/.venv/bin/python}"

for concurrency in $CONCURRENCIES; do
  echo "==================================================="
  echo "== $LABEL | $REQUESTS reqs | concorrência $concurrency"
  echo "==================================================="
  "$PY" bench.py --tech all --requests "$REQUESTS" --concurrency "$concurrency" --label "$LABEL"
  echo
done

echo "Dica: gere os gráficos com: $PY plot.py"
