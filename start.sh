#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

venv/bin/python -m streamlit run streamlit_app/app.py "$@"
