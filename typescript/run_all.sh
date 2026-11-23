#!/usr/bin/env bash
# Sobe os 4 servidores TypeScript em background (portas 8000-8003).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .logs .pids

TSX="./node_modules/.bin/tsx"

start() {
  local name="$1"
  shift
  setsid "$@" > ".logs/$name.log" 2>&1 < /dev/null &
  echo $! > ".pids/$name.pid"
  echo "  $name -> pid $(cat ".pids/$name.pid")"
}

if [ ! -d node_modules ]; then
  echo "Instalando dependências..." && npm install --no-fund --no-audit
fi

echo "Subindo servidores TypeScript:"
start rest "$TSX" src/rest/server.ts
start soap "$TSX" src/soap/server.ts
start graphql "$TSX" src/graphql/server.ts
start grpc "$TSX" src/grpc/server.ts

echo "Aguardando 6s..." && sleep 6
echo "Portas:"
ss -ltn 2>/dev/null | grep -E ':(8000|8001|8002|8003)' || true
