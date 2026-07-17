#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${ROOT}/.agent_env"

python -m venv "${ENVIRONMENT}"
"${ENVIRONMENT}/bin/python" -m pip install --upgrade pip
"${ENVIRONMENT}/bin/python" -m pip install -r "${ROOT}/requirements-agent.txt"
echo "Agent SDK runtime installed at ${ENVIRONMENT}"
