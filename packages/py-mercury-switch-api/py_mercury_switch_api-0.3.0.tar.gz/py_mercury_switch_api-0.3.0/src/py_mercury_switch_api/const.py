"""Constants for Mercury Switch API."""

# Speed mappings from switch values to human-readable strings
SPEED_MAPPING = {
    0: "Disconnected",  # 断开
    1: "Auto",  # 自动
    2: "10M Half Duplex",  # 10M半双工
    3: "10M Full Duplex",  # 10M全双工
    4: "100M Half Duplex",  # 100M半双工
    5: "100M Full Duplex",  # 100M全双工
    6: "1000M Full Duplex",  # 1000M全双工
}

# Link status to speed mapping (from PortStatistics)
LINK_STATUS_TO_SPEED = {
    0: "Disconnected",  # 断开
    1: "Auto",  # 自动
    2: "10M Half Duplex",  # 10M半双工
    3: "10M Full Duplex",  # 10M全双工
    4: "100M Half Duplex",  # 100M半双工
    5: "100M Full Duplex",  # 100M全双工
    6: "1000M Full Duplex",  # 1000M全双工
}

# URL paths
LOGIN_URL = "/logon.cgi"
SYSTEM_INFO_URL = "/SystemInfoRpm.htm"
PORT_SETTING_URL = "/PortSettingRpm.htm"
PORT_STATISTICS_URL = "/PortStatisticsRpm.htm"
VLAN_8021Q_URL = "/Vlan8021QRpm.htm"

# Request timeout
URL_REQUEST_TIMEOUT = 15
