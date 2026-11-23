#!/usr/bin/env bash
# Sobe os 4 servidores Python em background (portas 8000-8003).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .logs .pids

PY=".venv/bin/python"
UV=".venv/bin/uvicorn"

start() {
  local name="$1"
  shift
  setsid "$@" > ".logs/$name.log" 2>&1 < /dev/null &
  echo $! > ".pids/$name.pid"
  echo "  $name -> pid $(cat ".pids/$name.pid")"
}

./grpc_api/generate.sh > /dev/null

echo "Subindo servidores Python:"
start rest "$UV" rest.app:app --host 0.0.0.0 --port 8000
start soap "$UV" soap.app:app --host 0.0.0.0 --port 8001
start graphql "$UV" graphql_api.app:app --host 0.0.0.0 --port 8002
start grpc "$PY" grpc_api/server.py

echo "Aguardando 4s..." && sleep 4
echo "Portas:"
ss -ltn 2>/dev/null | grep -E ':(8000|8001|8002|8003)' || true
