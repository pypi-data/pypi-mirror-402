# LogVictoriaLogs

Python client library for integrating with VictoriaLogs, a high-performance log database and search solution.

## Features

- Easy integration with VictoriaLogs
- Support for multiple logging protocols (HTTP, Syslog)
- Automatic caller information capture
- Python logging module integration
- Structured logging with rich context information

## Installation

```bash
pip install LogVictoriaLogs
```

## Usage

### Basic Usage

```python
# ----------------------------------------------------------------------
# 🎯 示例
# ----------------------------------------------------------------------
def demo_function():
    # 初始化主客户端，只包含基础配置
    base_client = VictoriaLogsClient("192.168.164.31", project="shortlink-system")
    # 创建服务特定的客户端
    service_client = base_client.CreateClient("shortlink-updater")
    service_client.info("从 demo_function 发出的日志")


if __name__ == "__main__":
    # 初始化主客户端，只包含基础配置
    base_client = VictoriaLogsClient("192.168.164.31", project="shortlink-system")
    
    # 为不同服务创建子客户端
    main_client = base_client.CreateClient("main")
    updater_client = base_client.CreateClient("shortlink-updater")

    # 模拟模块日志
    demo_function()
    main_client.info("主模块启动完成")
    updater_client.info("短链更新成功")
    updater_client.warning("短链更新成功")
    updater_client.error("短链更新失败")

    # 查询
    main_client.PrintLogs('project:"shortlink-system" service:"shortlink-updater"')

```

### Python Logging Integration

```python
import logging
from LogVictoriaLogs import VictoriaLogsClient

# Create client
client = VictoriaLogsClient("victorialogs-host", 9428, 514)

# Configure logging
logger = logging.getLogger("MyApp")
logger.setLevel(logging.INFO)

# Add VictoriaLogs handler
handler = client._setup_logging_handler(service="my-application")
logger.addHandler(handler)

# Use standard logging
logger.info("Application started")
logger.error("Something went wrong")
```

## License

MIT
