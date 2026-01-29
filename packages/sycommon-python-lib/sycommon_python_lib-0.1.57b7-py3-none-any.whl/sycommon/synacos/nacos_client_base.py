import threading
import time
from typing import Optional
import nacos
from sycommon.config.Config import Config
from sycommon.logging.kafka_log import SYLogger


class NacosClientBase:
    """Nacos客户端基础类 - 负责客户端初始化和连接管理"""

    def __init__(self, nacos_config: dict, enable_register_nacos: bool):
        self.nacos_config = nacos_config
        self.enable_register_nacos = enable_register_nacos

        # 客户端配置
        self.max_retries = self.nacos_config.get('maxRetries', 5)
        self.retry_delay = self.nacos_config.get('retryDelay', 5)
        self.max_retry_delay = self.nacos_config.get('maxRetryDelay', 30)

        # 状态管理
        self._client_initialized = False
        self._state_lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self.nacos_client: Optional[nacos.NacosClient] = None

    def _initialize_client(self) -> bool:
        """初始化Nacos客户端（仅首次调用时执行）"""
        if self._client_initialized:
            return True

        for attempt in range(self.max_retries):
            try:
                register_ip = self.nacos_config['registerIp']
                namespace_id = self.nacos_config['namespaceId']
                self.nacos_client = nacos.NacosClient(
                    server_addresses=register_ip,
                    namespace=namespace_id
                )
                SYLogger.info("nacos:客户端初始化成功")
                self._client_initialized = True
                return True
            except Exception as e:
                delay = min(self.retry_delay, self.max_retry_delay)
                SYLogger.error(
                    f"nacos:客户端初始化失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                time.sleep(delay)

        SYLogger.warning("nacos:无法连接到 Nacos 服务器，已达到最大重试次数")
        return False

    def ensure_client_connected(self, retry_once: bool = False) -> bool:
        """确保Nacos客户端已连接，返回连接状态"""
        with self._state_lock:
            if self._client_initialized:
                return True

        SYLogger.warning("nacos:客户端未初始化，尝试连接...")

        max_attempts = 2 if retry_once else self.max_retries
        attempt = 0

        while attempt < max_attempts:
            try:
                register_ip = self.nacos_config['registerIp']
                namespace_id = self.nacos_config['namespaceId']

                self.nacos_client = nacos.NacosClient(
                    server_addresses=register_ip,
                    namespace=namespace_id
                )

                if self._verify_client_connection():
                    with self._state_lock:
                        self._client_initialized = True
                    SYLogger.info("nacos:客户端初始化成功")
                    return True
                else:
                    raise ConnectionError("nacos:客户端初始化后无法验证连接")

            except Exception as e:
                attempt += 1
                delay = min(self.retry_delay, self.max_retry_delay)
                SYLogger.error(
                    f"nacos:客户端初始化失败 (尝试 {attempt}/{max_attempts}): {e}")
                time.sleep(delay)

        SYLogger.error("nacos:无法连接到 Nacos 服务器，已达到最大重试次数")
        return False

    def _verify_client_connection(self) -> bool:
        """验证客户端是否真正连接成功"""
        if not self.enable_register_nacos:
            return True

        try:
            namespace_id = self.nacos_config['namespaceId']
            service_name = Config().config.get('Name', '')
            self.nacos_client.list_naming_instance(
                service_name=service_name,
                namespace_id=namespace_id,
                group_name="DEFAULT_GROUP",
                healthy_only=True
            )
            return True
        except Exception as e:
            SYLogger.warning(f"nacos:客户端连接验证失败: {e}")
            return False

    def reconnect_nacos_client(self) -> bool:
        """重新连接Nacos客户端"""
        SYLogger.warning("nacos:尝试重新连接Nacos客户端")
        with self._state_lock:
            self._client_initialized = False
        return self.ensure_client_connected()

    @property
    def is_connected(self) -> bool:
        """检查客户端是否已连接"""
        with self._state_lock:
            return self._client_initialized
