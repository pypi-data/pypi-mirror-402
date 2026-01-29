"""Constants for Mercury Switch API."""

# Speed mappings from switch values to human-readable strings
SPEED_MAPPING = {
    0: "断开",  # Disconnected
    1: "自动",  # Auto
    2: "10M半双工",  # 10M Half Duplex
    3: "10M全双工",  # 10M Full Duplex
    4: "100M半双工",  # 100M Half Duplex
    5: "100M全双工",  # 100M Full Duplex
    6: "1000M全双工",  # 1000M Full Duplex
}

# Link status to speed mapping (from PortStatistics)
LINK_STATUS_TO_SPEED = {
    0: "断开",  # Disconnected
    1: "自动",  # Auto
    2: "10M半双工",  # 10M Half Duplex
    3: "10M全双工",  # 10M Full Duplex
    4: "100M半双工",  # 100M Half Duplex
    5: "100M全双工",  # 100M Full Duplex
    6: "1000M全双工",  # 1000M Full Duplex
}

# URL paths
LOGIN_URL = "/logon.cgi"
SYSTEM_INFO_URL = "/SystemInfoRpm.htm"
PORT_SETTING_URL = "/PortSettingRpm.htm"
PORT_STATISTICS_URL = "/PortStatisticsRpm.htm"
VLAN_8021Q_URL = "/Vlan8021QRpm.htm"

# Request timeout
URL_REQUEST_TIMEOUT = 15
