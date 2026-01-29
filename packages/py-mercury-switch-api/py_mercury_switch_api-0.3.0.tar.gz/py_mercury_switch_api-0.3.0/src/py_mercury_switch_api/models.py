"""Definitions of auto-detectable Mercury Switch models."""

from __future__ import annotations

from typing import Any, ClassVar

from .utils import get_all_child_classes_list


class MultipleModelsDetectedError(Exception):
    """Detection of switch model was not unique."""


class MercurySwitchModelNotDetectedError(Exception):
    """None of the models passed the tests."""


class AutodetectedMercuryModel:
    """Base class definition for Mercury Switch Models."""

    SUPPORTED = True
    MODEL_NAME = ""
    PORTS = 0
    CHECKS_AND_RESULTS: ClassVar[list[tuple[str, list[str]]]] = []

    AUTODETECT_TEMPLATES: ClassVar[list[dict[str, Any]]] = [
        {"method": "get", "url": "http://{host}/SystemInfoRpm.htm"},
    ]

    LOGIN_TEMPLATE: ClassVar[dict[str, Any]] = {
        "method": "post",
        "url": "http://{host}/logon.cgi",
        "params": {"username": "_username", "password": "_password", "logon": "登录"},
    }

    SYSTEM_INFO_TEMPLATES: ClassVar[list[dict[str, Any]]] = [
        {"method": "get", "url": "http://{host}/SystemInfoRpm.htm"},
    ]

    PORT_SETTING_TEMPLATES: ClassVar[list[dict[str, Any]]] = [
        {"method": "get", "url": "http://{host}/PortSettingRpm.htm"},
    ]

    PORT_STATISTICS_TEMPLATES: ClassVar[list[dict[str, Any]]] = [
        {"method": "get", "url": "http://{host}/PortStatisticsRpm.htm"},
    ]

    VLAN_8021Q_TEMPLATES: ClassVar[list[dict[str, Any]]] = [
        {"method": "get", "url": "http://{host}/Vlan8021QRpm.htm"},
    ]

    def __init__(self) -> None:
        """Empty constructor."""

    def get_autodetect_funcs(self) -> list[tuple[str, list[str]]]:
        """Return list with detection functions."""
        return self.CHECKS_AND_RESULTS


class SG108Pro(AutodetectedMercuryModel):
    """Mercury SG108-Pro 8-port switch."""

    MODEL_NAME = "SG108Pro"
    PORTS = 8

    CHECKS_AND_RESULTS: ClassVar[list[tuple[str, list[str]]]] = [
        ("check_system_info_model", ["SG108-Pro"]),
    ]


class SG105E(AutodetectedMercuryModel):
    """Mercury SG105E 5-port switch (placeholder for future support)."""

    MODEL_NAME = "SG105E"
    PORTS = 5
    SUPPORTED = False  # Not yet implemented

    CHECKS_AND_RESULTS: ClassVar[list[tuple[str, list[str]]]] = [
        ("check_system_info_model", ["SG105E"]),
    ]


# Get all registered models
MODELS: list[type] = get_all_child_classes_list(AutodetectedMercuryModel)
