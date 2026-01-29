"""Tests for connector."""

from py_mercury_switch_api import MercurySwitchConnector
from py_mercury_switch_api.models import SG108Pro


class TestConnectorOfflineMode:
    """Test connector using offline mode with fixtures."""

    def test_get_switch_infos_sg108pro(self, sg108pro_pages_0):
        """Test getting switch infos for SG108Pro."""
        connector = MercurySwitchConnector(
            host="192.168.1.100", username="admin", password="test"
        )
        # Enable offline mode - reads from fixtures/ directory
        import os

        pages_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "SG108Pro", "0"
        )
        connector.turn_on_offline_mode(pages_path)
        connector.switch_model = SG108Pro()
        connector.ports = 8

        result = connector.get_switch_infos()

        assert result["switch_model"] == "SG108-Pro"
        assert result["switch_mac"] == "00:AA:BB:CC:DD:EE"
        assert result["vlan_count"] == 7

    def test_autodetect_model(self, sg108pro_pages_0):
        """Test model auto-detection."""
        connector = MercurySwitchConnector(
            host="192.168.1.100", username="admin", password="test"
        )
        import os

        pages_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "SG108Pro", "0"
        )
        connector.turn_on_offline_mode(pages_path)

        model = connector.autodetect_model()

        assert model.MODEL_NAME == "SG108Pro"
        assert connector.ports == 8
