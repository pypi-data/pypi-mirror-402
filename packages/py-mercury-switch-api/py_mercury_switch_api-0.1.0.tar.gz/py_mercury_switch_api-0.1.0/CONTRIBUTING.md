# Contributing to py-mercury-switch-api

Thank you for your interest in contributing to py-mercury-switch-api! This document provides guidelines and instructions for contributing.

## Ways to Contribute

- 🐛 Reporting bugs
- 💡 Suggesting features
- 📖 Improving documentation
- 🔧 Submitting code changes
- ➕ Adding support for new switch models

## Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/daxingplay/py-mercury-switch-api.git
cd py-mercury-switch-api
```

2. Install development dependencies:

```bash
pip install -e .
pip install pytest pytest-cov ruff mypy types-requests
```

3. Run tests to verify setup:

```bash
pytest
```

## Code Style

We use [ruff](https://github.com/astral-sh/ruff) for code formatting and linting.

```bash
# Format code
ruff format .

# Check for issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes (`pytest`)
4. Make sure your code lints (`ruff check .`)
5. Update documentation if needed
6. Submit your pull request

## Adding Support for New Switch Models

This is the most common type of contribution. Follow these steps to add a new Mercury switch model:

### Step 1: Gather Information

Connect to your switch's web interface and save the HTML pages:

1. `SystemInfoRpm.htm` - System information page
2. `PortSettingRpm.htm` - Port settings page
3. `PortStatisticsRpm.htm` - Port statistics page
4. `Vlan8021QRpm.htm` - VLAN configuration page (if available)
5. `logon.cgi` response - Login response (save as `LoginFailed.htm` for failed login)

Save these files in `tests/fixtures/MODEL_NAME/0/`.

### Step 2: Create the Model Class

Add a new class in `src/py_mercury_switch_api/models.py`:

```python
class SG116E(AutodetectedMercuryModel):
    """Mercury SG116E 16-port switch."""
    
    MODEL_NAME = "SG116E"
    PORTS = 16
    
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_system_info_model", ["SG116E"]),
    ]
    
    # Override templates if needed (most Mercury switches use the same URLs)
    # SYSTEM_INFO_TEMPLATES: ClassVar = [
    #     {"method": "get", "url": "http://{host}/CustomPage.htm"},
    # ]
```

### Step 3: Verify Model Detection

The `CHECKS_AND_RESULTS` attribute defines how the library identifies your switch model. The parser function `check_system_info_model` extracts the model name from the `info_ds` JavaScript object in `SystemInfoRpm.htm`.

If your switch uses a different format, you may need to:

1. Add a new parser function in `parsers.py`
2. Reference it in `CHECKS_AND_RESULTS`

### Step 4: Handle Model-Specific Parsing

If your switch's HTML pages have a different structure, create a model-specific parser:

```python
# In parsers.py
class SG116EParser(PageParser):
    """Parser for SG116E-specific pages."""
    
    def parse_system_info(self, response: BaseResponse) -> dict[str, Any]:
        # Custom parsing logic
        ...
```

Then update `create_page_parser()` to return the correct parser.

### Step 5: Add Test Fixtures

Create the fixture directory structure:

```
tests/fixtures/
└── SG116E/
    └── 0/
        ├── SystemInfoRpm.htm
        ├── PortSettingRpm.htm
        ├── PortStatisticsRpm.htm
        ├── Vlan8021QRpm.htm
        └── LoginFailed.htm
```

### Step 6: Run Tests

```bash
pytest -v
```

### Step 7: Submit a Pull Request

Include in your PR description:

- Switch model name and port count
- Any special features or limitations
- Screenshots of the switch web interface (optional but helpful)

## Reporting Bugs

When reporting bugs, please include:

- Python version
- Library version
- Switch model and firmware version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (with `logging.DEBUG` enabled)

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Feature Requests

Feature requests are welcome! Please include:

- Clear description of the feature
- Use case / why it would be useful
- Any implementation ideas

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
