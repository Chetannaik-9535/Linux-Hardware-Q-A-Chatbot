#!/usr/bin/env bash
# ==============================================================================
# Script: setup_sudoers.sh
# Purpose: Configure narrowly-scoped passwordless sudo for dmidecode
# Security Principle: Principle of Least Privilege (PoLP)
#
# DO NOT GRANT UNRESTRICTED SUDO TO THE APPLICATION OR USER.
# This script creates /etc/sudoers.d/hw-assistant with read-only access to dmidecode.
# ==============================================================================

set -euo pipefail

TARGET_USER="${1:-${USER:-$(whoami)}}"
SUDOERS_FILE="/etc/sudoers.d/hw-assistant"
DMIDECODE_BIN="$(command -v dmidecode || echo "/usr/sbin/dmidecode")"

echo "=================================================================="
echo "Configuring Scoped Sudoers Rule for Linux Hardware Assistant"
echo "=================================================================="
echo "Target User: ${TARGET_USER}"
echo "Binary:      ${DMIDECODE_BIN}"
echo "Rule File:   ${SUDOERS_FILE}"
echo ""

if [[ $EUID -ne 0 ]]; then
    echo "This setup script requires root to create ${SUDOERS_FILE}."
    echo "Please run: sudo bash $0 ${TARGET_USER}"
    exit 1
fi

if [[ ! -x "${DMIDECODE_BIN}" ]]; then
    echo "Warning: '${DMIDECODE_BIN}' not found or not executable. Please install dmidecode first:"
    echo "  Debian/Ubuntu: apt-get install dmidecode"
    echo "  Fedora/RHEL:   dnf install dmidecode"
    echo "  Arch Linux:    pacman -S dmidecode"
    exit 1
fi

TMP_FILE="$(mktemp)"
cat <<EOF > "${TMP_FILE}"
# Scoped permission for Linux Hardware Q&A Assistant
# Allows non-root execution of dmidecode without password prompting.
# The application itself runs as an unprivileged user.
${TARGET_USER} ALL=(ALL) NOPASSWD: ${DMIDECODE_BIN}
EOF

# Validate syntax with visudo before installing to prevent bricking sudo
echo "Validating sudoers syntax with visudo..."
if visudo -cf "${TMP_FILE}"; then
    install -m 0440 "${TMP_FILE}" "${SUDOERS_FILE}"
    rm -f "${TMP_FILE}"
    echo "✓ Successfully installed ${SUDOERS_FILE}"
    echo ""
    echo "Test it as unprivileged user by running:"
    echo "  sudo -n ${DMIDECODE_BIN} -t memory"
    echo "If that succeeds without prompting for a password, setup is complete!"
else
    echo "Error: Syntax validation failed! Aborting installation."
    rm -f "${TMP_FILE}"
    exit 1
fi

