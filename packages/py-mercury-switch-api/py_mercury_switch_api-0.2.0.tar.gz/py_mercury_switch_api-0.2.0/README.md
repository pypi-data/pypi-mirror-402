# py-mercury-switch-api

[![CI](https://github.com/daxingplay/py-mercury-switch-api/actions/workflows/ci.yml/badge.svg)](https://github.com/daxingplay/py-mercury-switch-api/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/py-mercury-switch-api.svg)](https://badge.fury.io/py/py-mercury-switch-api)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[中文文档](README_zh.md)

A Python library for interacting with Mercury (水星) network switches via their web interface.

## Features

- 🔍 **Auto-detection** - Automatically detects switch model
- 📊 **System Info** - Retrieve switch model, MAC address, IP, firmware version
- 🔌 **Port Status** - Monitor port states, connection speeds, and link status
- 📈 **Traffic Statistics** - Get TX/RX packet counts per port
- 🏷️ **VLAN Support** - Read 802.1Q VLAN configuration
- 🧪 **Offline Mode** - Test with saved HTML pages for development

## Installation

```bash
pip install py-mercury-switch-api
```

## Quick Start

```python
from py_mercury_switch_api import MercurySwitchConnector

# Create connector
connector = MercurySwitchConnector(
    host="192.168.1.1",
    username="admin",
    password="password"
)

# Login and get switch information
if connector.get_login_cookie():
    # Auto-detect switch model
    connector.autodetect_model()
    print(f"Detected: {connector.switch_model.MODEL_NAME}")
    
    # Get all switch information
    info = connector.get_switch_infos()
    print(info)
```

## API Reference

### MercurySwitchConnector

The main class for interacting with Mercury switches.

#### Constructor

```python
MercurySwitchConnector(host: str, username: str, password: str)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `host` | `str` | IP address or hostname of the switch |
| `username` | `str` | Login username (usually `admin`) |
| `password` | `str` | Login password |

#### Methods

| Method | Description |
|--------|-------------|
| `get_login_cookie()` | Authenticate and obtain session cookie. Returns `True` on success. |
| `autodetect_model()` | Detect and configure the switch model automatically. |
| `get_switch_infos()` | Retrieve all available switch information as a dictionary. |
| `get_unique_id()` | Get a unique identifier for the switch (model + IP). |

### Return Data Structure

The `get_switch_infos()` method returns a dictionary containing:

```python
{
    # System Information
    "switch_model": "SG108-Pro",
    "switch_mac": "AA:BB:CC:DD:EE:FF",
    "switch_ip": "192.168.1.1",
    "switch_firmware": "1.0.0",
    "switch_hardware": "V1.0",
    
    # Port Status (for each port 1-N)
    "port_1_state": "on",           # Port enabled state
    "port_1_status": "on",          # Link status (connected/disconnected)
    "port_1_speed": "1000M Full",   # Configured speed
    "port_1_connection_speed": "1000M Full",  # Actual connection speed
    
    # Traffic Statistics (for each port)
    "port_1_tx_good": 123456,       # TX good packets
    "port_1_tx_bad": 0,             # TX bad packets
    "port_1_rx_good": 654321,       # RX good packets
    "port_1_rx_bad": 0,             # RX bad packets
    
    # VLAN Information
    "vlan_enabled": True,
    "vlan_type": "802.1Q",
    "vlan_count": 2,
    "vlan_1_name": "default",
    "vlan_1_tagged_ports": "1, 2",
    "vlan_1_untagged_ports": "3, 4, 5, 6, 7, 8",
}
```

## Supported Models

| Model | Ports | Status |
|-------|-------|--------|
| SG108Pro | 8 | ✅ Supported |
| SG105E | 5 | 🚧 Planned |

## Home Assistant Integration

This library is designed to be used with Home Assistant. A custom integration is available at:

> *Coming soon*

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/daxingplay/py-mercury-switch-api.git
cd py-mercury-switch-api

# Install in development mode
pip install -e ".[dev]"
# Or install dependencies manually
pip install -e .
pip install pytest pytest-cov ruff mypy
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy src/py_mercury_switch_api
```

## Adding New Model Support

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions on how to add support for new Mercury switch models.

### Quick Overview

1. **Create a model class** in `models.py`:

```python
class SG116E(AutodetectedMercuryModel):
    """Mercury SG116E 16-port switch."""
    
    MODEL_NAME = "SG116E"
    PORTS = 16
    
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_system_info_model", ["SG116E"]),
    ]
```

2. **Add test fixtures** in `tests/fixtures/MODEL_NAME/0/`

3. **Run tests** to verify the model works correctly

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-model`)
3. Commit your changes (`git commit -am 'Add support for SG116E'`)
4. Push to the branch (`git push origin feature/new-model`)
5. Open a Pull Request

## License

This project is licensed under the Apache Software License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [py-netgear-plus](https://github.com/ckarrie/py-netgear-plus)
