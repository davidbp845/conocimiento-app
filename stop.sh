#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PID=$(pgrep -f "streamlit run streamlit_app/app.py" || true)

if [ -z "$PID" ]; then
  echo "La aplicación no está en ejecución."
else
  kill $PID
  echo "Aplicación detenida (PID $PID)."
fi
