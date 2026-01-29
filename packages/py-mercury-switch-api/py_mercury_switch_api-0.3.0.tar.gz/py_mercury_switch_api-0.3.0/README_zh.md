# py-mercury-switch-api

[![CI](https://github.com/daxingplay/py-mercury-switch-api/actions/workflows/ci.yml/badge.svg)](https://github.com/daxingplay/py-mercury-switch-api/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/py-mercury-switch-api.svg)](https://badge.fury.io/py/py-mercury-switch-api)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[English](README.md)

一个用于通过 Web 界面与水星（Mercury）网络交换机交互的 Python 库。

## 功能特性

- 🔍 **自动检测** - 自动识别交换机型号
- 📊 **系统信息** - 获取交换机型号、MAC 地址、IP、固件版本
- 🔌 **端口状态** - 监控端口状态、连接速度、链路状态
- 📈 **流量统计** - 获取每个端口的发送/接收数据包数量
- 🏷️ **VLAN 支持** - 读取 802.1Q VLAN 配置
- 🧪 **离线模式** - 使用保存的 HTML 页面进行开发测试

## 安装

```bash
pip install py-mercury-switch-api
```

## 快速开始

```python
from py_mercury_switch_api import MercurySwitchConnector

# 创建连接器
connector = MercurySwitchConnector(
    host="192.168.1.1",
    username="admin",
    password="password"
)

# 登录并获取交换机信息
if connector.get_login_cookie():
    # 自动检测交换机型号
    connector.autodetect_model()
    print(f"检测到: {connector.switch_model.MODEL_NAME}")
    
    # 获取所有交换机信息
    info = connector.get_switch_infos()
    print(info)
```

## API 参考

### MercurySwitchConnector

用于与水星交换机交互的主类。

#### 构造函数

```python
MercurySwitchConnector(host: str, username: str, password: str)
```

| 参数 | 类型 | 描述 |
|------|------|------|
| `host` | `str` | 交换机的 IP 地址或主机名 |
| `username` | `str` | 登录用户名（通常是 `admin`） |
| `password` | `str` | 登录密码 |

#### 方法

| 方法 | 描述 |
|------|------|
| `get_login_cookie()` | 认证并获取会话 cookie。成功返回 `True`。 |
| `autodetect_model()` | 自动检测并配置交换机型号。 |
| `get_switch_infos()` | 以字典形式返回所有可用的交换机信息。 |
| `get_unique_id()` | 获取交换机的唯一标识符（型号 + IP）。 |

### 返回数据结构

`get_switch_infos()` 方法返回的字典包含：

```python
{
    # 系统信息
    "switch_model": "SG108-Pro",
    "switch_mac": "AA:BB:CC:DD:EE:FF",
    "switch_ip": "192.168.1.1",
    "switch_firmware": "1.0.0",
    "switch_hardware": "V1.0",
    
    # 端口状态（每个端口 1-N）
    "port_1_state": "on",           # 端口启用状态
    "port_1_status": "on",          # 链路状态（已连接/未连接）
    "port_1_speed": "1000M Full",   # 配置的速度
    "port_1_connection_speed": "1000M Full",  # 实际连接速度
    
    # 流量统计（每个端口）
    "port_1_tx_good": 123456,       # 发送正常数据包
    "port_1_tx_bad": 0,             # 发送错误数据包
    "port_1_rx_good": 654321,       # 接收正常数据包
    "port_1_rx_bad": 0,             # 接收错误数据包
    
    # VLAN 信息
    "vlan_enabled": True,
    "vlan_type": "802.1Q",
    "vlan_count": 2,
    "vlan_1_name": "default",
    "vlan_1_tagged_ports": "1, 2",
    "vlan_1_untagged_ports": "3, 4, 5, 6, 7, 8",
}
```

## 支持的型号

| 型号 | 端口数 | 状态 |
|------|--------|------|
| SG108Pro | 8 | ✅ 已支持 |
| SG105E | 5 | 🚧 计划中 |

## Home Assistant 集成

本库设计用于 Home Assistant 智能家居平台。自定义集成组件：

> *即将推出*

## 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/daxingplay/py-mercury-switch-api.git
cd py-mercury-switch-api

# 以开发模式安装
pip install -e ".[dev]"
# 或手动安装依赖
pip install -e .
pip install pytest pytest-cov ruff mypy
```

### 运行测试

```bash
pytest
```

### 代码质量检查

```bash
# 格式化代码
ruff format .

# 代码检查
ruff check .

# 类型检查
mypy src/py_mercury_switch_api
```

## 添加新型号支持

详细说明请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 简要步骤

1. **在 `models.py` 中创建型号类**：

```python
class SG116E(AutodetectedMercuryModel):
    """水星 SG116E 16口交换机。"""
    
    MODEL_NAME = "SG116E"
    PORTS = 16
    
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_system_info_model", ["SG116E"]),
    ]
```

2. **在 `tests/fixtures/型号名/0/` 目录添加测试数据**

3. **运行测试** 验证型号是否正常工作

## 贡献指南

欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细指南。

### 如何贡献

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/new-model`)
3. 提交更改 (`git commit -am '添加 SG116E 支持'`)
4. 推送到分支 (`git push origin feature/new-model`)
5. 提交 Pull Request

## 许可证

本项目采用 Apache 2.0 软件许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- 灵感来源于 [py-netgear-plus](https://github.com/ckarrie/py-netgear-plus)
