"""Definitions of HTML parsers for Mercury switches."""

from __future__ import annotations

import logging
import re
from typing import Any

from .const import LINK_STATUS_TO_SPEED, SPEED_MAPPING
from .fetcher import BaseResponse

_LOGGER = logging.getLogger(__name__)


class MercurySwitchPageParserError(Exception):
    """Error parsing page."""


def create_page_parser(switch_model: str | None = None) -> PageParser:
    """Return the parser for the switch model."""
    # For now, we only have one parser. In the future, we can add model-specific parsers.
    return PageParser()


class PageParser:
    """Parser for Mercury Switch HTML pages."""

    def parse_js_object(self, html_content: str, var_name: str) -> dict[str, Any]:
        """Parse a JavaScript object variable from HTML."""
        # Pattern to match: var var_name = { ... };
        pattern = rf"var\s+{var_name}\s*=\s*(\{{[^}}]*\}});"
        match = re.search(pattern, html_content, re.DOTALL)
        if not match:
            # Try without semicolon
            pattern = rf"var\s+{var_name}\s*=\s*(\{{[^}}]*\}})"
            match = re.search(pattern, html_content, re.DOTALL)

        if not match:
            raise MercurySwitchPageParserError(
                f"Could not find JavaScript variable: {var_name}"
            )

        js_obj_str = match.group(1)
        result: dict[str, Any] = {}

        # Parse key-value pairs
        # Match patterns like: key: value or key: [value1, value2]
        # Handle both strings and arrays
        for key_match in re.finditer(r"(\w+):\s*(\[[^\]]*\]|[^,}]+)", js_obj_str):
            key = key_match.group(1)
            value_str = key_match.group(2).strip()

            # Check if it's an array
            if value_str.startswith("[") and value_str.endswith("]"):
                # Parse array
                array_content = value_str[1:-1]
                values: list[str | int] = []
                # Handle array elements (strings, numbers, hex)
                for elem in re.finditer(
                    r"(['\"][^'\"]*['\"]|\d+|0x[0-9A-Fa-f]+)", array_content
                ):
                    elem_str = elem.group(1)
                    # Remove quotes if string
                    if elem_str.startswith("'") or elem_str.startswith('"'):
                        values.append(elem_str[1:-1])
                    elif elem_str.startswith("0x"):
                        values.append(int(elem_str, 16))
                    else:
                        try:
                            values.append(int(elem_str))
                        except ValueError:
                            values.append(elem_str)
                result[key] = values
            else:
                # Single value
                value_str = value_str.strip()
                # Remove trailing comma or semicolon
                value_str = value_str.rstrip(",;")
                # Try to parse as number
                if value_str.isdigit():
                    result[key] = int(value_str)
                elif value_str.startswith("0x"):
                    result[key] = int(value_str, 16)
                elif value_str in ["true", "false"]:
                    result[key] = value_str == "true"
                elif value_str.startswith("'") or value_str.startswith('"'):
                    result[key] = value_str[1:-1]
                else:
                    result[key] = value_str

        return result

    def parse_js_variable(self, html_content: str, var_name: str) -> Any:
        """Parse a simple JavaScript variable from HTML."""
        # Pattern to match: var var_name = value;
        pattern = rf"var\s+{var_name}\s*=\s*([^;]+);"
        match = re.search(pattern, html_content)
        if not match:
            raise MercurySwitchPageParserError(
                f"Could not find JavaScript variable: {var_name}"
            )

        value_str = match.group(1).strip()
        # Try to parse as number
        if value_str.isdigit():
            return int(value_str)
        elif value_str.startswith("0x"):
            return int(value_str, 16)
        return value_str

    def check_system_info_model(self, response: BaseResponse) -> str:
        """Check the model from system info page."""
        try:
            info_ds = self.parse_js_object(response.text, "info_ds")
            if "descriStr" in info_ds and len(info_ds["descriStr"]) > 0:
                model_name: str = info_ds["descriStr"][0]
                return model_name
        except Exception as e:
            _LOGGER.debug("Error parsing system info model: %s", e)
        return ""

    def parse_system_info(self, response: BaseResponse) -> dict[str, Any]:
        """Parse system information from SystemInfoRpm.htm."""
        result: dict[str, Any] = {}
        try:
            info_ds = self.parse_js_object(response.text, "info_ds")
            if "descriStr" in info_ds and len(info_ds["descriStr"]) > 0:
                result["switch_model"] = info_ds["descriStr"][0]
            if "macStr" in info_ds and len(info_ds["macStr"]) > 0:
                result["switch_mac"] = info_ds["macStr"][0]
            if "ipStr" in info_ds and len(info_ds["ipStr"]) > 0:
                result["switch_ip"] = info_ds["ipStr"][0]
            if "firmwareStr" in info_ds and len(info_ds["firmwareStr"]) > 0:
                result["switch_firmware"] = info_ds["firmwareStr"][0]
            if "hardwareStr" in info_ds and len(info_ds["hardwareStr"]) > 0:
                result["switch_hardware"] = info_ds["hardwareStr"][0]
        except Exception as e:
            _LOGGER.error("Error parsing system info: %s", e)
        return result

    def parse_port_setting(self, response: BaseResponse, ports: int) -> dict[str, Any]:
        """Parse port settings from PortSettingRpm.htm."""
        result: dict[str, Any] = {}
        try:
            max_port_num = self.parse_js_variable(response.text, "max_port_num")
            result["switch_ports"] = max_port_num
            all_info = self.parse_js_object(response.text, "all_info")

            if "state" in all_info and "spd_act" in all_info:
                state = all_info["state"]
                spd_act = all_info["spd_act"]

                for port_num in range(1, min(ports + 1, len(state) + 1)):
                    port_idx = port_num - 1
                    if port_idx < len(state):
                        result[f"port_{port_num}_state"] = (
                            "on" if state[port_idx] == 1 else "off"
                        )
                    if port_idx < len(spd_act):
                        speed_val = spd_act[port_idx]
                        result[f"port_{port_num}_speed"] = SPEED_MAPPING.get(
                            speed_val, f"Unknown({speed_val})"
                        )
        except Exception as e:
            _LOGGER.error("Error parsing port setting: %s", e)
        return result

    def parse_port_statistics(
        self, response: BaseResponse, ports: int
    ) -> dict[str, Any]:
        """Parse port statistics from PortStatisticsRpm.htm."""
        result: dict[str, Any] = {}
        try:
            max_port_num = self.parse_js_variable(response.text, "max_port_num")
            result["switch_ports"] = max_port_num
            all_info = self.parse_js_object(response.text, "all_info")

            if "state" in all_info and "link_status" in all_info and "pkts" in all_info:
                state = all_info["state"]
                link_status = all_info["link_status"]
                pkts = all_info["pkts"]

                for port_num in range(1, min(ports + 1, len(state) + 1)):
                    port_idx = port_num - 1
                    # Use link_status to determine connectivity
                    # (0 = disconnected, >0 = connected)
                    if port_idx < len(link_status):
                        link_val = link_status[port_idx]
                        result[f"port_{port_num}_status"] = (
                            "on" if link_val > 0 else "off"
                        )
                        result[f"port_{port_num}_connection_speed"] = (
                            LINK_STATUS_TO_SPEED.get(link_val, f"Unknown({link_val})")
                        )
                    # Packets: 4 values per port [tx_good, tx_bad, rx_good, rx_bad]
                    if port_idx * 4 + 3 < len(pkts):
                        result[f"port_{port_num}_tx_good"] = pkts[port_idx * 4]
                        result[f"port_{port_num}_tx_bad"] = pkts[port_idx * 4 + 1]
                        result[f"port_{port_num}_rx_good"] = pkts[port_idx * 4 + 2]
                        result[f"port_{port_num}_rx_bad"] = pkts[port_idx * 4 + 3]
        except Exception as e:
            _LOGGER.error("Error parsing port statistics: %s", e)
        return result

    def parse_vlan_info(self, response: BaseResponse) -> dict[str, Any]:
        """Parse VLAN information from Vlan8021QRpm.htm."""
        result: dict[str, Any] = {}
        try:
            qvlan_ds = self.parse_js_object(response.text, "qvlan_ds")

            # VLAN enabled state
            if "state" in qvlan_ds:
                result["vlan_enabled"] = qvlan_ds["state"] == 1

            # VLAN type - for now assume 802.1Q if enabled, otherwise check other types
            if result.get("vlan_enabled"):
                result["vlan_type"] = "802.1Q"
            else:
                # Could be Port-based, MTU, or None - for now default to None
                result["vlan_type"] = "None"

            # VLAN count
            if "count" in qvlan_ds:
                result["vlan_count"] = qvlan_ds["count"]

            # VLAN details
            if "vids" in qvlan_ds and "names" in qvlan_ds:
                vids = qvlan_ds["vids"]
                names = qvlan_ds["names"]
                tag_mbrs = qvlan_ds.get("tagMbrs", [])
                untag_mbrs = qvlan_ds.get("untagMbrs", [])

                for idx, vid in enumerate(vids):
                    if idx < len(names):
                        result[f"vlan_{vid}_name"] = names[idx]

                    # Convert bitmasks to port lists
                    if idx < len(tag_mbrs):
                        tagged_ports = self._bitmask_to_ports(
                            tag_mbrs[idx], qvlan_ds.get("portNum", 8)
                        )
                        result[f"vlan_{vid}_tagged_ports"] = (
                            ", ".join(str(p) for p in tagged_ports)
                            if tagged_ports
                            else ""
                        )

                    if idx < len(untag_mbrs):
                        untagged_ports = self._bitmask_to_ports(
                            untag_mbrs[idx], qvlan_ds.get("portNum", 8)
                        )
                        result[f"vlan_{vid}_untagged_ports"] = (
                            ", ".join(str(p) for p in untagged_ports)
                            if untagged_ports
                            else ""
                        )

        except Exception as e:
            _LOGGER.error("Error parsing VLAN info: %s", e)
        return result

    def parse_logon_info(self, response: BaseResponse) -> int | None:
        """Parse logonInfo array from login response.

        Returns the error type (errType) from logonInfo[0]:
        - 0: Login successful
        - 1: Username or password incorrect
        - 2: User not allowed to login
        - 3: Maximum login users reached
        - 4: Maximum login users reached (16 users)
        - 5: Session timeout

        Returns None if logonInfo not found.
        """
        try:
            # Pattern to match: var logonInfo = new Array(1, 0, 0);
            pattern = (
                r"var\s+logonInfo\s*=\s*new\s+Array\s*\("
                r"\s*(\d+)\s*,\s*\d+\s*,\s*\d+\s*\)"
            )
            match = re.search(pattern, response.text)
            if match:
                err_type = int(match.group(1))
                return err_type
        except Exception as e:
            _LOGGER.debug("Error parsing logonInfo: %s", e)
        return None

    def _bitmask_to_ports(self, bitmask: int, max_ports: int) -> list[int]:
        """Convert a bitmask to a list of port numbers (1-indexed)."""
        ports: list[int] = []
        for i in range(max_ports):
            if bitmask & (1 << i):
                ports.append(i + 1)  # Ports are 1-indexed
        return ports
