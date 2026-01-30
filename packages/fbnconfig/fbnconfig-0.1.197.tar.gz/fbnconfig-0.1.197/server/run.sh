#!/bin/bash
set -euo pipefail
THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
uv run uvicorn \
    --app-dir "$THISDIR" \
     --reload --reload-dir "$THISDIR" --reload-dir "$THISDIR/../fbnconfig" \
    app:app --host 127.0.0.1 --port 4290
