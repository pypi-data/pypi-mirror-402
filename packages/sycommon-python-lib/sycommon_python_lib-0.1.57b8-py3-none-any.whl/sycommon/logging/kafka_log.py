import os
import sys
import json
import socket
import threading
import traceback
import asyncio
from datetime import datetime

from kafka import KafkaProducer
from loguru import logger

from sycommon.config.Config import Config, SingletonMeta
from sycommon.middleware.context import current_trace_id, current_headers
from sycommon.tools.env import check_env_flag
from sycommon.tools.snowflake import Snowflake

# 配置Loguru的颜色方案
LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


class KafkaSink:
    """
    自定义 Loguru Sink，负责格式化日志并发送到 Kafka
    """

    def __init__(self, service_id: str):
        self.service_id = service_id
        # 获取配置
        from sycommon.synacos.nacos_service import NacosService
        common = NacosService(
            Config().config).share_configs.get("common.yml", {})
        bootstrap_servers = common.get("log", {}).get(
            "kafka", {}).get("servers", None)

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(
                v, ensure_ascii=False).encode('utf-8'),
            # 保持原有的优化配置
            max_block_ms=60000,
            retries=5,
            request_timeout_ms=30000,
            compression_type='gzip',
            batch_size=16384,
            linger_ms=5,
            buffer_memory=33554432,
        )

    def write(self, message):
        """
        Loguru 会调用此方法。
        message 参数实际上是 loguru.Message 对象，可以通过 message.record 获取所有字段。
        """
        try:
            # 1. 获取原始日志记录
            record = message.record

            # 2. 提取 TraceID
            trace_id = None
            try:
                # 如果业务方传的是 JSON 字符串作为 message
                msg_obj = json.loads(record["message"])
                if isinstance(msg_obj, dict):
                    trace_id = msg_obj.get("trace_id")
            except:
                pass

            if not trace_id:
                trace_id = current_trace_id.get()

            if not trace_id:
                trace_id = str(Snowflake.id)
            else:
                trace_id = str(trace_id)

            # 3. 提取异常详情 (如果有)
            error_detail = ""
            if record["exception"] is not None:
                # Loguru 的 exception 对象
                error_detail = "".join(traceback.format_exception(
                    record["exception"].type,
                    record["exception"].value,
                    record["exception"].traceback
                ))
            elif "error" in record["extra"]:
                # 兼容其他方式注入的异常
                error_detail = str(record["extra"].get("error"))

            # 4. 获取主机信息
            try:
                ip = socket.gethostbyname(socket.gethostname())
            except:
                ip = '127.0.0.1'
            host_name = socket.gethostname()

            # 5. 获取线程/协程信息
            try:
                task = asyncio.current_task()
                thread_info = f"coroutine:{task.get_name()}" if task else f"thread:{threading.current_thread().name}"
            except RuntimeError:
                thread_info = f"thread:{threading.current_thread().name}"

            # 6. 提取类名/文件名信息
            file_name = record["file"].name
            logger_name = record["name"]
            if logger_name and logger_name != file_name:
                class_name = f"{file_name}:{logger_name}"
            else:
                class_name = file_name

            # 7. 构建最终的 Kafka 日志结构
            log_entry = {
                "traceId": trace_id,
                "sySpanId": "",
                "syBizId": "",
                "ptxId": "",
                "time": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
                "day": datetime.now().strftime("%Y.%m.%d"),
                "msg": record["message"],
                "detail": error_detail,
                "ip": ip,
                "hostName": host_name,
                "tenantId": "",
                "userId": "",
                "customerId": "",
                "env": Config().config.get('Nacos', {}).get('namespaceId', ''),
                "priReqSource": "",
                "reqSource": "",
                "serviceId": self.service_id,
                "logLevel": record["level"].name,
                "className": class_name,
                "method": record["function"],
                "line": str(record["line"]),
                "theadName": thread_info,
                "sqlCost": 0,
                "size": len(str(record["message"])),
                "uid": int(Snowflake.id)
            }

            # 8. 发送
            self._producer.send("shengye-json-log", log_entry)

        except Exception as e:
            print(f"KafkaSink Error: {e}")

    def flush(self):
        if self._producer:
            self._producer.flush(timeout=5)


class KafkaLogger(metaclass=SingletonMeta):
    _sink_instance = None

    @staticmethod
    def setup_logger(config: dict):
        logger.remove()

        from sycommon.synacos.nacos_service import NacosService
        service_id = NacosService(config).service_name

        KafkaLogger._sink_instance = KafkaSink(service_id)

        logger.add(
            KafkaLogger._sink_instance,
            level="INFO",
            format="{message}",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )

        logger.add(
            sink=sys.stdout,
            level="ERROR",
            format=LOGURU_FORMAT,
            colorize=True,
            backtrace=True,
            diagnose=True
        )

        sys.excepthook = KafkaLogger._handle_exception

    @staticmethod
    def _handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        trace_id = current_trace_id.get() or str(Snowflake.id)
        error_msg = json.dumps({
            "trace_id": trace_id,
            "message": f"Uncaught exception: {exc_type.__name__}",
            "level": "ERROR"
        }, ensure_ascii=False)

        logger.opt(exception=(exc_type, exc_value,
                   exc_traceback)).error(error_msg)

    @staticmethod
    def close():
        if KafkaLogger._sink_instance:
            KafkaLogger._sink_instance.flush()


class SYLogger:
    @staticmethod
    def get_trace_id():
        return current_trace_id.get()

    @staticmethod
    def set_trace_id(trace_id: str):
        return current_trace_id.set(trace_id)

    @staticmethod
    def reset_trace_id(token):
        current_trace_id.reset(token)

    @staticmethod
    def get_headers():
        return current_headers.get()

    @staticmethod
    def set_headers(headers: list[tuple[str, str]]):
        return current_headers.set(headers)

    @staticmethod
    def reset_headers(token):
        current_headers.reset(token)

    @staticmethod
    def _get_execution_context() -> str:
        try:
            task = asyncio.current_task()
            if task:
                return f"coroutine:{task.get_name()}"
        except RuntimeError:
            pass
        return f"thread:{threading.current_thread().name}"

    @staticmethod
    def _log(msg: any, level: str = "INFO"):
        """
        统一日志记录入口
        修复：手动提取堆栈信息并写入 message，确保 Kafka 能收到
        """
        # 序列化消息
        if isinstance(msg, dict) or isinstance(msg, list):
            msg_str = json.dumps(msg, ensure_ascii=False)
        else:
            msg_str = str(msg)

        # 构建基础日志字典
        log_dict = {
            "trace_id": str(SYLogger.get_trace_id() or Snowflake.id),
            "message": msg_str,
            "level": level,
            "threadName": SYLogger._get_execution_context()
        }

        # 如果是 ERROR 级别，手动获取堆栈并加入 log_dict
        if level == "ERROR":
            # 获取当前异常信息 (sys.exc_info() 在 except 块中有效)
            exc_info = sys.exc_info()
            if exc_info and exc_info[0] is not None:
                # 将堆栈格式化为字符串，放入 detail 字段
                # 这样 KafkaSink 解析 message 时，就能拿到 detail
                tb_str = "".join(traceback.format_exception(*exc_info))
                log_dict["detail"] = tb_str

        # 将字典转为 JSON 字符串传给 Loguru
        log_json = json.dumps(log_dict, ensure_ascii=False)

        if level == "ERROR":
            # 依然使用 opt(exception=True) 让控制台打印彩色堆栈
            # 注意：Loguru 内部可能会忽略我们已经塞进去的 detail 字符串，
            # 但这没关系，因为 KafkaSink 解析 message 字符串时会重新读取 detail
            logger.opt(exception=True).error(log_json)
        elif level == "WARNING":
            logger.warning(log_json)
        else:
            logger.info(log_json)

        if check_env_flag(['DEV-LOG']):
            print(log_json)

    @staticmethod
    def info(msg: any, *args, **kwargs):
        SYLogger._log(msg, "INFO")

    @staticmethod
    def warning(msg: any, *args, **kwargs):
        SYLogger._log(msg, "WARNING")

    @staticmethod
    def debug(msg: any, *args, **kwargs):
        SYLogger._log(msg, "DEBUG")

    @staticmethod
    def error(msg: any, *args, **kwargs):
        SYLogger._log(msg, "ERROR")

    @staticmethod
    def exception(msg: any, *args, **kwargs):
        SYLogger._log(msg, "ERROR")
