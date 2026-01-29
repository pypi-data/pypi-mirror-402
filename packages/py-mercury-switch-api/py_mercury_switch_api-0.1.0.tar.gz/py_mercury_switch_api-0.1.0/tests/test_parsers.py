"""Tests for parsers."""

from py_mercury_switch_api.fetcher import BaseResponse
from py_mercury_switch_api.parsers import PageParser


class TestPageParser:
    """Test PageParser class."""

    def test_parse_js_object_info_ds(self, sg108pro_pages_0):
        """Test parsing info_ds JavaScript object."""
        parser = PageParser()
        html = sg108pro_pages_0["SystemInfoRpm.htm"]
        result = parser.parse_js_object(html, "info_ds")

        assert result["descriStr"] == ["SG108-Pro"]
        assert result["macStr"] == ["00:AA:BB:CC:DD:EE"]
        assert result["firmwareStr"] == ["1.0.0 Build 20180515 Rel.60767"]

    def test_parse_system_info(self, sg108pro_pages_0):
        """Test parsing system info."""
        parser = PageParser()

        class MockResponse:
            text = sg108pro_pages_0["SystemInfoRpm.htm"]

        response = BaseResponse()
        response.text = MockResponse.text
        result = parser.parse_system_info(response)

        assert result["switch_model"] == "SG108-Pro"
        assert result["switch_mac"] == "00:AA:BB:CC:DD:EE"
        assert result["switch_ip"] == "192.168.1.100"

    def test_parse_port_statistics(self, sg108pro_pages_0):
        """Test parsing port statistics."""
        parser = PageParser()

        class MockResponse:
            text = sg108pro_pages_0["PortStatisticsRpm.htm"]

        response = BaseResponse()
        response.text = MockResponse.text
        result = parser.parse_port_statistics(response, ports=8)

        assert result["port_1_tx_good"] == 426028519
        assert result["port_1_status"] == "on"  # link_status[0] = 6
        assert result["port_2_status"] == "off"  # link_status[1] = 0

    def test_parse_vlan_info(self, sg108pro_pages_0):
        """Test parsing VLAN info."""
        parser = PageParser()

        class MockResponse:
            text = sg108pro_pages_0["Vlan8021QRpm.htm"]

        response = BaseResponse()
        response.text = MockResponse.text
        result = parser.parse_vlan_info(response)

        assert result["vlan_enabled"] is True
        assert result["vlan_count"] == 7
        assert result["vlan_10_name"] == "VLAN10"
        assert result["vlan_20_name"] == "VLAN20"

    def test_bitmask_to_ports(self):
        """Test bitmask to ports conversion."""
        parser = PageParser()

        assert parser._bitmask_to_ports(0xFF, 8) == [1, 2, 3, 4, 5, 6, 7, 8]
        assert parser._bitmask_to_ports(0x41, 8) == [1, 7]
        assert parser._bitmask_to_ports(0x02, 8) == [2]
        assert parser._bitmask_to_ports(0x00, 8) == []

    def test_parse_logon_info_failed(self):
        """Test parsing logonInfo from failed login response."""
        parser = PageParser()

        # Load the LoginFailed.htm fixture
        from pathlib import Path

        fixture_path = (
            Path(__file__).parent / "fixtures" / "SG108Pro" / "0" / "LoginFailed.htm"
        )
        html_content = fixture_path.read_text(encoding="utf-8")

        response = BaseResponse()
        response.text = html_content

        err_type = parser.parse_logon_info(response)

        # Should return 1 (username or password incorrect)
        assert err_type == 1

    def test_parse_logon_info_success(self):
        """Test parsing logonInfo from successful login response."""
        parser = PageParser()

        # Create a mock successful login response
        html_content = "<script>var logonInfo = new Array(0, 0, 0);</script>"

        response = BaseResponse()
        response.text = html_content

        err_type = parser.parse_logon_info(response)

        # Should return 0 (login successful)
        assert err_type == 0
