#!/usr/bin/env bash
# =============================================================================
# Self-Hosted GitHub Actions Runner Setup for SDN Lab
# =============================================================================
#
# This script installs and configures a GitHub Actions self-hosted runner
# on a machine that has network access to your SDN lab (controller + devices).
#
# Prerequisites:
#   - Ubuntu 22.04+ or RHEL 9.x
#   - Network access to SDN controller and fabric management interfaces
#   - A GitHub personal access token with repo scope
#
# Usage:
#   chmod +x setup-runner.sh
#   ./setup-runner.sh \
#     --repo "https://github.com/YOUR_ORG/sdn-test-automation" \
#     --token "ABCDEF123456" \
#     --labels "sdn-lab" \
#     --controller-host "10.0.0.100" \
#     --controller-type "odl"
#
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

RUNNER_VERSION="2.323.0"
RUNNER_DIR="/opt/actions-runner"
RUNNER_USER="runner"
RUNNER_GROUP="runner"

# Parse arguments
REPO_URL=""
TOKEN=""
LABELS="sdn-lab"
CONTROLLER_HOST=""
CONTROLLER_TYPE="odl"
CONTROLLER_USER="admin"
CONTROLLER_PASS="admin"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)           REPO_URL="$2"; shift 2 ;;
        --token)          TOKEN="$2"; shift 2 ;;
        --labels)         LABELS="$2"; shift 2 ;;
        --controller-host) CONTROLLER_HOST="$2"; shift 2 ;;
        --controller-type) CONTROLLER_TYPE="$2"; shift 2 ;;
        --controller-user) CONTROLLER_USER="$2"; shift 2 ;;
        --controller-pass) CONTROLLER_PASS="$2"; shift 2 ;;
        *)                echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$REPO_URL" || -z "$TOKEN" ]]; then
    echo "ERROR: --repo and --token are required."
    echo "Usage: $0 --repo <REPO_URL> --token <TOKEN> [options]"
    exit 1
fi

echo "========================================"
echo " SDN Lab Runner Setup"
echo "========================================"
echo "  Repo:       $REPO_URL"
echo "  Labels:     $LABELS"
echo "  Controller: $CONTROLLER_HOST ($CONTROLLER_TYPE)"
echo "========================================"

# ---------------------------------------------------------------------------
# 1. System dependencies
# ---------------------------------------------------------------------------

echo "[1/6] Installing system dependencies..."

if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        curl jq git software-properties-common \
        libffi-dev libssl-dev build-essential \
        iputils-ping net-tools traceroute nmap
    # Install Python 3.13 from deadsnakes PPA (Ubuntu)
    if ! python3.13 --version &>/dev/null; then
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update -qq
        sudo apt-get install -y -qq python3.13 python3.13-venv python3.13-dev
    fi
    # Set python3.13 as the default python3
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 || true
elif command -v dnf &>/dev/null; then
    sudo dnf install -y -q \
        curl jq git \
        libffi-devel openssl-devel gcc \
        iputils net-tools traceroute nmap
    # Install Python 3.13 on RHEL/Fedora
    if ! python3.13 --version &>/dev/null; then
        sudo dnf install -y -q python3.13 python3.13-devel python3.13-pip || {
            echo "Python 3.13 not in default repos. Install from source or enable EPEL."
            exit 1
        }
    fi
else
    echo "ERROR: Unsupported package manager. Need apt-get or dnf."
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Create runner user
# ---------------------------------------------------------------------------

echo "[2/6] Creating runner user..."

if ! id "$RUNNER_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash "$RUNNER_USER"
fi

# ---------------------------------------------------------------------------
# 3. Install GitHub Actions runner
# ---------------------------------------------------------------------------

echo "[3/6] Installing GitHub Actions runner v${RUNNER_VERSION}..."

sudo mkdir -p "$RUNNER_DIR"
sudo chown "$RUNNER_USER:$RUNNER_GROUP" "$RUNNER_DIR"

cd "$RUNNER_DIR"

ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  RUNNER_ARCH="x64" ;;
    aarch64) RUNNER_ARCH="arm64" ;;
    *)       echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

RUNNER_TAR="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_TAR}"

if [[ ! -f "$RUNNER_TAR" ]]; then
    sudo -u "$RUNNER_USER" curl -sL "$RUNNER_URL" -o "$RUNNER_TAR"
fi

sudo -u "$RUNNER_USER" tar xzf "$RUNNER_TAR"

# ---------------------------------------------------------------------------
# 4. Configure the runner
# ---------------------------------------------------------------------------

echo "[4/6] Configuring runner..."

sudo -u "$RUNNER_USER" ./config.sh \
    --url "$REPO_URL" \
    --token "$TOKEN" \
    --labels "$LABELS" \
    --name "sdn-lab-$(hostname)" \
    --work "_work" \
    --unattended \
    --replace

# ---------------------------------------------------------------------------
# 5. Set environment variables for SDN access
# ---------------------------------------------------------------------------

echo "[5/6] Configuring SDN environment variables..."

ENV_FILE="$RUNNER_DIR/.env"
cat > "$ENV_FILE" << EOF
# SDN Controller Configuration
SDN_CONTROLLER_HOST=$CONTROLLER_HOST
SDN_CONTROLLER_TYPE=$CONTROLLER_TYPE
SDN_CONTROLLER_USER=$CONTROLLER_USER
SDN_CONTROLLER_PASS=$CONTROLLER_PASS
SDN_CONTROLLER_PORT=8181

# Lab environment flag
SDN_LAB_DEVICES=true

# Python settings
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
EOF

sudo chown "$RUNNER_USER:$RUNNER_GROUP" "$ENV_FILE"
echo "  Environment written to $ENV_FILE"

# ---------------------------------------------------------------------------
# 6. Install as systemd service
# ---------------------------------------------------------------------------

echo "[6/6] Installing systemd service..."

sudo ./svc.sh install "$RUNNER_USER"
sudo ./svc.sh start

echo ""
echo "========================================"
echo " Runner setup complete"
echo "========================================"
echo ""
echo "  Service: actions.runner.$(basename "$REPO_URL").sdn-lab-$(hostname)"
echo "  Status:  sudo ./svc.sh status"
echo "  Logs:    journalctl -u actions.runner.* -f"
echo ""
echo "  Verify with: sudo -u $RUNNER_USER ./run.sh --check"
echo ""

# ---------------------------------------------------------------------------
# Verify controller connectivity from runner
# ---------------------------------------------------------------------------

if [[ -n "$CONTROLLER_HOST" ]]; then
    echo "Testing controller connectivity..."
    if curl -sf -o /dev/null "http://${CONTROLLER_HOST}:8181/" -u "${CONTROLLER_USER}:${CONTROLLER_PASS}" --connect-timeout 5; then
        echo "  ✓ Controller reachable at ${CONTROLLER_HOST}:8181"
    else
        echo "  ✗ WARNING: Cannot reach controller at ${CONTROLLER_HOST}:8181"
        echo "    Ensure the runner host has network access to the SDN lab."
    fi
fi
