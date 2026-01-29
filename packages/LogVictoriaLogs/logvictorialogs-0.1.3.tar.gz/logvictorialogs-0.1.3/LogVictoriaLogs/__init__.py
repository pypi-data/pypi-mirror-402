import socket
import requests
import json
import logging
import inspect
from typing import List, Dict, Any, Union


class VictoriaLogsClient:
    """
    VictoriaLogs 客户端
    提供 HTTP / Syslog 日志发送与查询功能
    支持多层 stream：project + service
    """

    def __init__(
        self,
        host: str,
        http_port: int = 9428,
        syslog_udp_port: int = 514,
        timeout: int = 5,
        project: str | None = None,
    ):
        """
        :param host: VictoriaLogs 主机
        :param http_port: HTTP 插入端口（默认 9428）
        :param syslog_udp_port: Syslog UDP 端口
        :param timeout: 请求超时
        :param project: 项目名，用于日志分层（可选）
        """
        self.host = host
        self.http_port = http_port
        self.syslog_udp_port = syslog_udp_port
        self.timeout = timeout
        self.project = project

        self.http_insert_url = f"http://{host}:{http_port}/insert/jsonline"
        self.query_url = f"http://{host}:{http_port}/select/logsql/query"
    
    def CreateClient(self, name: str = "logging-demo") -> 'VictoriaLogsServiceClient':
        """
        创建一个服务级别的子客户端
        
        :param name: 服务/模块名
        :return: 服务级别的日志客户端
        """
        return VictoriaLogsServiceClient(self, name)


class VictoriaLogsServiceClient:
    """
    服务级别的 VictoriaLogs 客户端
    继承主客户端的配置，并添加服务名称
    """
    
    def __init__(self, parent_client: VictoriaLogsClient, name: str):
        """
        :param parent_client: 父级 VictoriaLogsClient 实例
        :param name: 服务/模块名
        """
        # 继承父级客户端的属性
        self.host = parent_client.host
        self.http_port = parent_client.http_port
        self.syslog_udp_port = parent_client.syslog_udp_port
        self.timeout = parent_client.timeout
        self.project = parent_client.project
        self.http_insert_url = parent_client.http_insert_url
        self.query_url = parent_client.query_url
        
        # 服务名称
        self.name = name
        
        # 内部 logger
        self.logger = logging.getLogger(f"{self.name}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # ----------------------------------------------------------------------
    # 🌐 日志发送
    # ----------------------------------------------------------------------
    def _send_logs(
        self,
        logs: Union[Dict[str, Any], List[Dict[str, Any]]],
        protocol: str = "http",
        stream_fields: str = None,
        time_field: str = "timestamp",
        msg_field: str = "message"
    ) -> bool:
        """发送日志"""
        logs = [logs] if isinstance(logs, dict) else logs
        protocol = protocol.lower()

        # 自动选择 stream 层级结构
        if stream_fields is None:
            stream_fields = "project,service" if self.project else "service"

        if protocol == "http":
            return self._send_http(logs, stream_fields, time_field, msg_field)
        elif protocol == "syslog":
            return self._send_syslog(logs)
        else:
            raise ValueError(f"不支持的协议: {protocol}")

    def _send_http(
        self, logs: List[Dict[str, Any]],
        stream_fields: str, time_field: str, msg_field: str
    ) -> bool:
        """通过 HTTP API 发送日志"""
        params = {
            "_stream_fields": stream_fields,
            "_time_field": time_field,
            "_msg_field": msg_field
        }
        json_lines = "\n".join(json.dumps(log, ensure_ascii=False) for log in logs) + "\n"

        try:
            resp = requests.post(
                self.http_insert_url,
                params=params,
                data=json_lines.encode("utf-8"),
                timeout=self.timeout
            )
            if resp.ok:
                # self.logger.info("✅ HTTP 日志发送成功")
                return True
            self.logger.error(f"❌ HTTP 发送失败: {resp.status_code} {resp.text}")
        except requests.RequestException as e:
            self.logger.error(f"❌ 无法连接到 VictoriaLogs HTTP 接口: {e}")
        return False

    def _send_syslog(self, logs: List[Dict[str, Any]]) -> bool:
        """通过 Syslog UDP 发送日志"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                for log in logs:
                    service = log.get("service", "unknown")
                    level = log.get("level", "INFO").upper()
                    message = log.get("message", "")
                    msg = f"<14>{service} [{level}] {message}"
                    sock.sendto(msg.encode("utf-8"), (self.host, self.syslog_udp_port))
            # self.logger.info("✅ Syslog UDP 日志发送成功")
            return True
        except OSError as e:
            self.logger.error(f"❌ Syslog 发送失败: {e}")
            return False

    # ----------------------------------------------------------------------
    # 🔍 查询相关
    # ----------------------------------------------------------------------
    def _query_logs(self, query: str = "*") -> List[Dict[str, Any]]:
        """执行 LogsQL 查询"""
        try:
            resp = requests.get(self.query_url, params={"query": query}, timeout=self.timeout)
            if not resp.ok:
                self.logger.error(f"❌ 查询失败: {resp.status_code} {resp.text}")
                return []

            logs = []
            for line in resp.text.strip().splitlines():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    self.logger.warning(f"⚠️ 无法解析日志行: {line}")

            self.logger.info(f"✅ 查询成功，共 {len(logs)} 条日志")
            return logs
        except requests.RequestException as e:
            self.logger.error(f"❌ 无法连接到 VictoriaLogs 查询接口: {e}")
            return []

    def PrintLogs(self, query: str = "*") -> None:
        """查询并打印日志"""
        logs = self._query_logs(query)
        if not logs:
            print("未查询到日志。")
            return
        for i, log in enumerate(logs, 1):
            print(f"\n--- 日志 {i} ---")
            for k, v in log.items():
                print(f"{k}: {v}")

    # ----------------------------------------------------------------------
    # 🧩 辅助函数
    # ----------------------------------------------------------------------
    def _get_caller_info(self, depth: int = 2) -> Dict[str, str]:
        """动态获取调用者的函数名、文件、行号"""
        stack = inspect.stack()
        if len(stack) > depth:
            frame_info = stack[depth]
            return {
                "function": frame_info.function,
                "filename": frame_info.filename,
                "lineno": str(frame_info.lineno),
                "module": frame_info.frame.f_globals.get("__name__", "unknown")
            }
        return {"function": "unknown", "filename": "unknown", "lineno": "0", "module": "unknown"}

    def _get_level_sender(self, level: str) -> "_LevelSender":
        return _LevelSender(self, level)

    @property
    def info(self) -> "_LevelSender":
        return self._get_level_sender("info")

    @property
    def warning(self) -> "_LevelSender":
        return self._get_level_sender("warning")

    @property
    def debug(self) -> "_LevelSender":
        return self._get_level_sender("debug")

    @property
    def error(self) -> "_LevelSender":
        return self._get_level_sender("error")


    # ----------------------------------------------------------------------
    # 🔧 Python logging 集成（增强版）
    # ----------------------------------------------------------------------
    def _setup_logging_handler(self, service: str = "python-app", level: int = logging.INFO) -> logging.Handler:
        """配置 Python logging Handler"""
        client = self

        class VictoriaLogsHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                try:
                    func = record.funcName
                    if func == "<module>":
                        func = record.filename.rsplit(".", 1)[0]

                    try:
                        formatted_message = self.format(record)
                    except Exception:
                        formatted_message = record.getMessage()

                    log = {
                        "message": formatted_message,
                        "level": record.levelname.lower(),
                        "service": service,
                        **({"project": client.project} if client.project else {}),
                        "function": func,
                        "filename": record.filename,
                        "lineno": str(record.lineno),
                        "module": record.module,
                        "source": "python-logging",
                        "environment": "development",
                        "thread": getattr(record, "thread", "unknown"),
                        "process": getattr(record, "process", "unknown")
                    }
                    client._send_logs(log)
                except Exception:
                    pass

        handler = VictoriaLogsHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s",
            "%Y-%m-%d %H:%M:%S"
        ))
        return handler


class _LevelSender:
    def __init__(self, client: VictoriaLogsServiceClient, level: str):
        self._client = client
        self._level = level

    def __call__(self, message: str, service: str = None, **kwargs) -> bool:
        return self.Sent(message, service, **kwargs)

    def Sent(self, message: str, service: str = None, **kwargs) -> bool:
        level = (self._level or "info").lower()
        if level not in {"error", "warning", "debug", "info"}:
            level = "info"

        service = service or self._client.name

        info = self._client._get_caller_info(depth=2)
        log = {
            "message": f"{service} | {message}",
            "level": level.upper(),
            "service": service,
            **({"project": self._client.project} if self._client.project else {}),
            **info,
            "source": "python-app",
            "environment": "development",
            **kwargs
        }

        log_message = f"{service} | {info['function']}:{info['lineno']} - {message}"
        if level == "error":
            self._client.logger.error(log_message)
        elif level == "warning":
            self._client.logger.warning(log_message)
        elif level == "debug":
            self._client.logger.debug(log_message)
        else:
            self._client.logger.info(log_message)

        return self._client._send_logs(log)


# 为了兼容旧版 API，在 VictoriaLogsClient 类上添加对 service 相关方法的代理
VictoriaLogsClient._Sent = lambda self, message, service=None, **kwargs: self.CreateClient(service).info(message, **kwargs)
VictoriaLogsClient.PrintLogs = lambda self, query="*": self.CreateClient().PrintLogs(query)


# ----------------------------------------------------------------------
# 🎯 示例
# ----------------------------------------------------------------------
def _demo_function():
    # 初始化主客户端，只包含基础配置
    base_client = VictoriaLogsClient("192.168.164.31", project="shortlink-system")
    # 创建服务特定的客户端
    service_client = base_client.CreateClient("shortlink-updater")
    service_client.info("从 demo_function 发出的日志")


if __name__ == "__main__":
    # 初始化主客户端，只包含基础配置
    base_client = VictoriaLogsClient("192.168.164.4", project="shortlink-system")
    
    # 为不同服务创建子客户端
    main_client = base_client.CreateClient("main")
    updater_client = base_client.CreateClient("shortlink-updater")

    # 模拟模块日志
    _demo_function()
    main_client.info("主模块启动完成")
    updater_client.info("短链更新成功")
    updater_client.warning("短链更新成功")
    updater_client.error("短链更新失败")
    

    # 查询
    main_client.PrintLogs('project:"shortlink-system" service:"shortlink-updater"')
