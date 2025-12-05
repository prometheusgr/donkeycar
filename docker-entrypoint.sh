#!/bin/bash
set -euo pipefail

JUPYTER_CONFIG_DIR="${HOME}/.jupyter"
mkdir -p "$JUPYTER_CONFIG_DIR"

# Ensure the notebooks folder exists in the project (mounted at /app/notebooks)
# This prevents Jupyter from failing if the host hasn't created the folder yet.
if [ ! -d "/app/notebooks" ]; then
  mkdir -p /app/notebooks || true
  echo "Created /app/notebooks"
fi

# If user opts into insecure mode, disable token/password in config
if [ "${JUPYTER_ALLOW_INSECURE:-0}" = "1" ]; then
  cat > "${JUPYTER_CONFIG_DIR}/jupyter_notebook_config.py" <<'PYCFG'
# WARNING: This disables authentication. Only enable in trusted networks.
c.NotebookApp.token = ''
c.NotebookApp.password = ''
PYCFG
  echo "Jupyter: running WITHOUT token/password (INSECURE)."
else
  if [ -n "${JUPYTER_TOKEN:-}" ]; then
    echo "Jupyter: using token from JUPYTER_TOKEN env var."
  fi
fi

# If JUPYTER_TOKEN is set and insecure mode not enabled, append token CLI arg
if [ -n "${JUPYTER_TOKEN:-}" ] && [ "${JUPYTER_ALLOW_INSECURE:-0}" != "1" ]; then
  set -- "$@" "--NotebookApp.token=${JUPYTER_TOKEN}"
fi

# Exec the requested command (e.g., jupyter lab ...)
exec "$@"
