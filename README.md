# SDN Test Automation

A pytest-based test automation framework for Software-Defined Networks. Provides a layered test pyramid (unit → integration → E2E), topology-bound test bundles, and GitHub Actions CI/CD with self-hosted runner support for lab environments.

**Requires Python 3.10+ and pytest 9.0+.**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                     │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐ │
│  │ Lint + Unit  │→ │  Integration   │→ │  Topology Gate   │ │
│  │(ubuntu-latest│  │ (ubuntu-latest)│  │ (self-hosted,    │ │
│  │ Python 3.10- │  │ mocked APIs    │  │  sdn-lab)        │ │
│  │ 3.13)        │  │                │  │                  │ │
│  └──────────────┘  └────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │  tests/ │         │  tests/ │         │  tests/ │
    │  unit/  │         │integra- │         │  e2e/   │
    │         │         │  tion/  │         │         │
    └─────────┘         └─────────┘         └─────────┘
         │                    │                    │
    ┌────▼────────────────────▼────────────────────▼────┐
    │              src/sdn_testkit/                      │
    │  controllers/  devices/  topology/  utils/         │
    └───────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │ ODL /   │         │ Netmiko │         │Topology │
    │ ONOS    │         │ Nornir  │         │ YAML    │
    │ REST API│         │ SSH     │         │ Bundles │
    └─────────┘         └─────────┘         └─────────┘
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/davidyoung8196504567-sudo/sdn-test-automation.git
cd sdn-test-automation
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run unit tests (no network needed)
pytest tests/unit/ -m unit -v

# Run integration tests (mocked by default)
pytest tests/integration/ -m integration -v

# Run E2E tests against a lab (requires controller + devices)
pytest tests/e2e/ -m e2e \
  --topology=spine_leaf \
  --controller-host=10.0.0.100 \
  --controller-type=odl \
  -v
```

## Repository Structure

```
sdn-test-automation/
├── .github/workflows/
│   ├── ci-lint-unit.yml        # Ruff lint + mypy + unit tests (every push/PR)
│   ├── ci-integration.yml      # Integration tests with mocked transport
│   └── topology-gate.yml       # E2E tests on self-hosted runner
├── runners/
│   ├── setup-runner.sh         # Self-hosted runner installation (Python 3.13)
│   ├── teardown-runner.sh      # Runner removal script
│   ├── Dockerfile.runner       # Containerized runner (Ubuntu 24.04 + Python 3.13)
│   └── docker-entrypoint.sh    # Container entrypoint
├── src/sdn_testkit/
│   ├── controllers/            # SDN controller clients (ODL, ONOS)
│   │   ├── base.py             # Abstract base with HTTP helpers
│   │   ├── odl.py              # OpenDaylight RESTCONF client
│   │   └── onos.py             # ONOS REST client
│   ├── devices/                # Network device interaction
│   │   ├── netmiko_helpers.py  # Netmiko wrappers (SSH commands)
│   │   └── nornir_helpers.py   # Nornir task orchestration
│   ├── topology/               # Topology models and loaders
│   │   ├── models.py           # Pydantic models (Node, Link, Segment, Topology)
│   │   └── loader.py           # YAML loader + discovery
│   └── utils/                  # Shared utilities
│       ├── config.py           # YAML config loading with env var interpolation
│       ├── validators.py       # IP, CIDR, MAC, VLAN validators
│       └── templates.py        # Jinja2 flow/ACL template rendering
├── tests/
│   ├── unit/                   # @pytest.mark.unit — pure logic, no I/O
│   │   ├── test_config/        # Config loading, validators
│   │   ├── test_topology/      # Topology model validation, YAML parsing
│   │   └── test_policy/        # Flow rule and ACL template rendering
│   ├── integration/            # @pytest.mark.integration — mocked or live APIs
│   │   ├── test_controller/    # ODL/ONOS API interactions
│   │   ├── test_netmiko/       # Device command execution
│   │   └── test_nornir/        # Nornir task orchestration
│   └── e2e/                    # @pytest.mark.e2e — requires lab fabric
│       ├── test_reachability/  # Host-to-host ping matrix
│       ├── test_segmentation/  # VLAN/VRF isolation verification
│       └── test_failover/      # Spine/border failover resilience
├── topologies/                 # Topology bundle definitions
│   ├── spine_leaf/             # 2-spine / 4-leaf Clos fabric
│   ├── campus/                 # Three-tier campus network
│   └── dc_fabric/              # Production-like 4-spine / 8-leaf + borders
├── inventory/                  # Nornir SimpleInventory files
├── templates/                  # Jinja2 templates for flow rules and ACLs
├── conftest.py                 # Root fixtures, CLI options, topology filtering
└── pyproject.toml              # Project config, pytest markers, ruff, mypy
```

## Version Compatibility

| Component          | Version                  |
|--------------------|--------------------------|
| Python             | 3.10, 3.11, 3.12, 3.13  |
| pytest             | >=9.0, <10               |
| pytest-xdist       | >=3.5                    |
| pytest-rerunfailures | >=15                   |
| netmiko            | >=4.3, <5                |
| nornir             | >=3.4, <4                |
| pydantic           | >=2.5, <3                |

### pytest 9.x Migration Notes

This repo is built for pytest 9.0+. Key differences from pytest 8.x:

- **`PytestRemovedIn9Warning` items are now errors.** No marks on fixtures, no `py.path.local` hook arguments, no `fspath` constructor args.
- **Python 3.9 dropped.** Minimum is Python 3.10 (pytest 9.0 requirement).
- **`--import-mode=importlib`** is enabled by default in `pyproject.toml` for reliable test discovery.
- **Native TOML config** is supported (though this repo uses `pyproject.toml` INI-compat mode for broader tooling support).
- **Subtests** are now a core feature — `pytest.raises()` with `ExceptionGroup` is natively supported.
- **No test functions return values** — pytest 9 (via 8.4) errors on non-None returns.

## Test Pyramid

| Layer         | Marker          | Runner           | What It Tests                                    |
|---------------|-----------------|------------------|--------------------------------------------------|
| Unit          | `@pytest.mark.unit` | `ubuntu-latest`  | Validators, models, template rendering, config parsing |
| Integration   | `@pytest.mark.integration` | `ubuntu-latest` | Controller API calls, netmiko/nornir task execution (mocked) |
| E2E           | `@pytest.mark.e2e` | `self-hosted, sdn-lab` | Reachability, segmentation, failover across live fabric |

Additional markers:
- `@pytest.mark.smoke` — Quick sanity checks (subset of integration)
- `@pytest.mark.slow` — Tests taking >30s
- `@pytest.mark.topology("name")` — Binds test to a specific topology bundle

## Topology Bundles

Topologies are defined in YAML and validated by Pydantic models. Each bundle defines nodes, links, segments, and controller configuration.

```yaml
# topologies/spine_leaf/topology.yaml
name: spine_leaf
nodes:
  - name: spine-1
    role: spine
    mgmt_ip: "10.255.0.1"
    device_type: arista_eos
links:
  - src_node: spine-1
    src_interface: Ethernet1
    dst_node: leaf-1
    dst_interface: Ethernet1
    bandwidth: "40G"
segments:
  - name: tenant-a
    vlan_id: 10
    vrf: "VRF-A"
    nodes: [host-1, host-2, leaf-1, leaf-2]
```

### Binding Tests to Topologies

```python
@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
class TestSpineLeafReachability:
    def test_ping_hosts(self, topology_spine_leaf):
        # Only runs when --topology=spine_leaf
        ...
```

Run with topology filtering:
```bash
pytest tests/e2e/ --topology=spine_leaf
```

## Self-Hosted Runner Setup

The self-hosted runner connects GitHub Actions to your SDN lab network. Both the setup script and Dockerfile install Python 3.13.

### Bare Metal / VM

```bash
chmod +x runners/setup-runner.sh
./runners/setup-runner.sh \
  --repo "https://github.com/diavidyoung8196504567-sudo/sdn-test-automation" \
  --token "YOUR_RUNNER_TOKEN" \
  --labels "sdn-lab" \
  --controller-host "10.0.0.100" \
  --controller-type "odl"
```

### Docker Container

```bash
docker build -t sdn-runner -f runners/Dockerfile.runner .
docker run -d --name sdn-runner \
  -e REPO_URL="https://github.com/davidyoung8196504567-sudo/sdn-test-automation" \
  -e TOKEN="YOUR_RUNNER_TOKEN" \
  -e SDN_CONTROLLER_HOST="10.0.0.100" \
  --network=host \
  sdn-runner
```

### Required GitHub Secrets

| Secret                | Description                         |
|-----------------------|-------------------------------------|
| `SDN_CONTROLLER_HOST` | Controller IP / hostname            |
| `SDN_CONTROLLER_USER` | Controller API username             |
| `SDN_CONTROLLER_PASS` | Controller API password             |

## CLI Options

```bash
pytest tests/ \
  --controller-host=10.0.0.100 \    # SDN controller address
  --controller-port=8181 \           # Controller API port
  --controller-type=odl \            # odl or onos
  --controller-user=admin \          # API username
  --controller-pass=admin \          # API password
  --topology=spine_leaf \            # Topology bundle filter
  --inventory-dir=./inventory        # Nornir inventory path
```

All options can also be set via environment variables prefixed with `SDN_`:
```bash
export SDN_CONTROLLER_HOST=10.0.0.100
export SDN_CONTROLLER_TYPE=odl
export SDN_TOPOLOGY=spine_leaf
```

## GitHub Actions Workflows

1. **CI: Lint + Unit Tests** (`ci-lint-unit.yml`) — Every push/PR. Ruff lint, mypy, unit tests across Python 3.10–3.13.
2. **CI: Integration Tests** (`ci-integration.yml`) — After PR to main. Mocked controller and device tests.
3. **Gate: Topology E2E Tests** (`topology-gate.yml`) — Manual dispatch or push to main. Runs on self-hosted runner with lab access.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, test conventions, and topology bundle authoring.

## Change History
2026-04-14 davidyoung8196504567@gmail.com - Initial upload to github account
- updated pyproject.toml: changed setuptools.backends._legacy to setuptools.build_meta to build clean with python 3.13 and pytest 9
- UNIT test results: 1 failed, 70 passed in 0.22s
  FAILED tests/unit/test_config/test_validators.py::TestValidateCIDR::test_invalid_cidrs[10.0.0.0] - AssertionError: assert True is False
  +  where True = validate_cidr('10.0.0.0')
- INT test results: 18 passed, 2 skipped in 0.25s 
- E2E test results: 11 passed, 4 skipped in 0.34s 


