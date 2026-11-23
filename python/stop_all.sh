#!/usr/bin/env bash
# Para os servidores Python iniciados por run_all.sh.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .pids ]; then
  echo "Nenhum pid encontrado."
  exit 0
fi

for pidfile in .pids/*.pid; do
  [ -e "$pidfile" ] || continue
  name="$(basename "$pidfile" .pid)"
  pid="$(cat "$pidfile")"
  if kill "$pid" 2>/dev/null; then
    echo "  $name (pid $pid) parado"
  fi
  rm -f "$pidfile"
done
