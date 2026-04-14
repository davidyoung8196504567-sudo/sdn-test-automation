#!/usr/bin/env bash
# =============================================================================
# Teardown self-hosted runner
# =============================================================================
#
# Stops the service, unregisters the runner, and cleans up.
#
# Usage:
#   ./teardown-runner.sh --token <REMOVAL_TOKEN>
# =============================================================================

set -euo pipefail

RUNNER_DIR="/opt/actions-runner"
TOKEN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --token) TOKEN="$2"; shift 2 ;;
        *)       echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$TOKEN" ]]; then
    echo "ERROR: --token is required (runner removal token from GitHub)."
    exit 1
fi

cd "$RUNNER_DIR"

echo "Stopping runner service..."
sudo ./svc.sh stop || true
sudo ./svc.sh uninstall || true

echo "Removing runner registration..."
./config.sh remove --token "$TOKEN"

echo "Runner unregistered and service removed."
