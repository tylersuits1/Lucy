#!/bin/bash
# Dev-server launcher — cds into backend/ so uvicorn's relative paths
# (.env, ./data/chroma) and the `app` package import resolve correctly
# regardless of the caller's working directory.
cd "$(dirname "$0")"
exec venv/bin/uvicorn app.main:app --reload --port 8000
