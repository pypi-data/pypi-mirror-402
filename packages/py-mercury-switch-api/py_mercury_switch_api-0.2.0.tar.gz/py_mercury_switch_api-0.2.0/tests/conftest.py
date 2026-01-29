"""Pytest fixtures for py-mercury-switch-api tests."""

import json
from pathlib import Path

import pytest

PAGES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sg108pro_pages_0():
    """Load SG108Pro snapshot 0 pages."""
    return _load_pages("SG108Pro", "0")


@pytest.fixture
def sg108pro_expected_0():
    """Load expected switch_infos.json for snapshot 0."""
    return _load_json("SG108Pro", "0", "switch_infos.json")


def _load_pages(model: str, snapshot: str) -> dict[str, str]:
    """Load all HTML pages for a model snapshot."""
    pages = {}
    path = PAGES_DIR / model / snapshot
    for file in path.glob("*.htm"):
        pages[file.name] = file.read_text(encoding="utf-8")
    return pages


def _load_json(model: str, snapshot: str, filename: str) -> dict:
    """Load JSON file."""
    path = PAGES_DIR / model / snapshot / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}
