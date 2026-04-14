# Contributing

## Development Setup

```bash
# Create virtual environment with Python 3.13
python3.13 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify pytest version
pytest --version  # Should show pytest 9.0.x
```

## Running Tests Locally

```bash
# All unit tests
pytest tests/unit/ -m unit -v

# Specific test file
pytest tests/unit/test_config/test_validators.py -v

# Integration tests (mocked — no lab needed)
pytest tests/integration/ -m integration -v

# Smoke tests only
pytest -m smoke -v

# With parallel execution
pytest tests/unit/ -m unit -n auto
```

## Writing Tests

### Test Markers

Every test function or class must have at least one marker:

```python
@pytest.mark.unit
def test_something():
    ...

@pytest.mark.integration
@pytest.mark.smoke
class TestControllerHealth:
    ...

@pytest.mark.e2e
@pytest.mark.topology("spine_leaf")
class TestFabricReachability:
    ...
```

### pytest 9.x Rules

These patterns are enforced by pytest 9.0+ (previously warnings, now errors):

1. **No marks on fixtures.** Place marks on the test functions/classes that use the fixture, not on the fixture itself.

   ```python
   # WRONG — will error in pytest 9
   @pytest.mark.integration
   @pytest.fixture
   def my_device():
       ...

   # CORRECT — mark the test, not the fixture
   @pytest.fixture
   def my_device():
       ...

   @pytest.mark.integration
   def test_device_command(my_device):
       ...
   ```

2. **No returning values from tests.** Test functions must return `None`.

   ```python
   # WRONG — will error in pytest 9
   def test_something():
       result = compute()
       return result  # Don't do this

   # CORRECT
   def test_something():
       result = compute()
       assert result == expected
   ```

3. **Use `pathlib.Path`, not `py.path.local`.** All path handling uses `pathlib.Path`. The `tmp_path` fixture (not `tmpdir`) is the standard.

4. **Use `from __future__ import annotations`** in every Python file for forward-reference type hints and `X | Y` union syntax.

### Test Naming

- Files: `test_<module>.py`
- Classes: `Test<Feature>`
- Functions: `test_<behavior_under_test>`

### Using Fixtures

Key fixtures from `conftest.py`:

| Fixture               | Scope    | Description                              |
|-----------------------|----------|------------------------------------------|
| `controller`          | session  | Active SDN controller client (ODL/ONOS)  |
| `controller_config`   | session  | Controller connection parameters         |
| `active_topology`     | session  | Loaded topology from `--topology`        |
| `topology_spine_leaf` | function | Pre-loaded spine-leaf topology           |
| `sample_device`       | function | Dict for a mock device                   |
| `sample_flow`         | function | Dict for a mock flow rule                |

### Mocking Network Calls

For integration tests, use `responses` (HTTP) or `unittest.mock` (SSH):

```python
import responses
from unittest.mock import patch, MagicMock

@responses.activate
def test_controller_api():
    responses.add(responses.GET, "http://127.0.0.1:8181/...", json={...})
    # test code

@patch("sdn_testkit.devices.netmiko_helpers.ConnectHandler")
def test_device_command(mock_handler):
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "output"
    mock_handler.return_value = mock_conn
    # test code
```

## Adding a Topology Bundle

1. Create `topologies/<name>/topology.yaml`
2. Follow the schema defined in `src/sdn_testkit/topology/models.py`
3. Validate it: `python -c "from sdn_testkit.topology.loader import load_topology; load_topology('topologies/<name>/topology.yaml')"`
4. Bind tests with `@pytest.mark.topology("<name>")`

### Topology YAML Schema

```yaml
name: string            # Unique topology identifier
description: string     # Human-readable description
controller:
  type: odl|onos
  host: string
  port: int

nodes:                  # List of network devices and hosts
  - name: string
    role: spine|leaf|border|host|controller|firewall|load_balancer
    mgmt_ip: string
    device_type: string  # Netmiko device_type
    interfaces: [string]
    metadata: {}

links:                  # Connections between nodes
  - src_node: string
    src_interface: string
    dst_node: string
    dst_interface: string
    bandwidth: string

segments:               # Network segments (VLAN/VRF)
  - name: string
    vlan_id: int
    vrf: string
    nodes: [string]     # Must reference existing node names
    description: string

metadata: {}            # Arbitrary topology metadata
```

## Code Quality

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/ --ignore-missing-imports
```

## Branch Strategy

- `main` — Protected. All three CI stages must pass.
- `develop` — Integration branch. Lint + unit tests required.
- Feature branches — Lint + unit tests on push.
