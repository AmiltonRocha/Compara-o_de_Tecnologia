#!/usr/bin/env bash
# Gera music_pb2.py e music_pb2_grpc.py a partir de specs/music.proto.
set -euo pipefail
cd "$(dirname "$0")"

if [ -x "../.venv/bin/python" ]; then
  PYTHON="../.venv/bin/python"
else
  PYTHON="python3"
fi

"$PYTHON" -m grpc_tools.protoc \
  -I../../specs \
  --python_out=. \
  --grpc_python_out=. \
  ../../specs/music.proto
echo "Gerado: music_pb2.py, music_pb2_grpc.py"
