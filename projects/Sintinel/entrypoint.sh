#!/usr/bin/env bash
set -euo pipefail

: "${RESTSERVER_HOST:=${RESTSERVER_HOST:-}}"
: "${SSH_KEY_NAME:=id_ed25519}"

SSH_KEY_PATH="/home/sintinel/.ssh/${SSH_KEY_NAME}"
SINTINEL_USER="sintinel"
SINTINEL_HOME="/home/${SINTINEL_USER}"
APP_SCRIPT="/opt/scripts/sintinel.py"
LOG_DIR="/var/log/sintinel"
LOG_FILE="${LOG_DIR}/sintinel.log"

_log() {
  local ts
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "[$ts] $*" >> "${LOG_FILE}"
}

# Prepare runtime FS (best-effort)
mkdir -p "${LOG_DIR}" "${SINTINEL_HOME}/.ssh" 2>/dev/null || true
touch "${LOG_FILE}" 2>/dev/null || true
chown -R "${SINTINEL_USER}:${SINTINEL_USER}" "${LOG_DIR}" "${SINTINEL_HOME}" 2>/dev/null || true
chmod 700 "${SINTINEL_HOME}/.ssh" 2>/dev/null || true

# Only check SSH key presence here (clients file checked by Python)
if [ -f "${SSH_KEY_PATH}" ]; then
  chmod 600 "${SSH_KEY_PATH}" 2>/dev/null || true
  chown "${SINTINEL_USER}:${SINTINEL_USER}" "${SSH_KEY_PATH}" 2>/dev/null || true
  _log "INFO: SSH key present at ${SSH_KEY_PATH}"
else
  _log "WARN: SSH key not found at ${SSH_KEY_PATH}. Mount your private key via volume."
fi

# Verify application script exists
if [ ! -f "${APP_SCRIPT}" ]; then
  _log "ERROR: application script not found at ${APP_SCRIPT}."
  exit 2
fi
chmod +x "${APP_SCRIPT}" 2>/dev/null || true

# Require explicit command (no default 'help' behavior)
if [ $# -lt 1 ]; then
  _log "ERROR: No command provided. Usage: docker run <container_name> <backup|restore|remove|list> [args]"
  exit 2
fi

_log "INFO: executing: python3 ${APP_SCRIPT} $*"
#exec python3 "${APP_SCRIPT}" "$@"
exec su -s /bin/bash sintinel -c "python3 ${APP_SCRIPT} $*"

