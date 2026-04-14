#!/usr/bin/env bash
# Entrypoint for containerized runner.
# Registers, runs, and deregisters on shutdown.

set -euo pipefail

REPO_URL="${REPO_URL:?REPO_URL is required}"
TOKEN="${TOKEN:?TOKEN is required}"
LABELS="${LABELS:-sdn-lab}"
RUNNER_NAME="${RUNNER_NAME:-sdn-runner-$(hostname)}"

cd /home/runner/actions-runner

# Register
./config.sh \
    --url "$REPO_URL" \
    --token "$TOKEN" \
    --labels "$LABELS" \
    --name "$RUNNER_NAME" \
    --work "_work" \
    --unattended \
    --replace \
    --ephemeral

# Deregister on exit
cleanup() {
    echo "Removing runner..."
    ./config.sh remove --token "$TOKEN" || true
}
trap cleanup EXIT

# Run
./run.sh
