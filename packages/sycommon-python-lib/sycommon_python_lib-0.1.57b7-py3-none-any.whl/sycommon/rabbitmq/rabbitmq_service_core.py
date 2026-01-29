import asyncio
from typing import Optional

from sycommon.logging.kafka_log import SYLogger
from sycommon.rabbitmq.rabbitmq_client import RabbitMQConnectionPool

logger = SYLogger


class RabbitMQCoreService:
    """
    RabbitMQ核心服务类 - 负责基础初始化、连接池管理、全局状态控制
    """
    # 全局共享状态
    _config: Optional[dict] = None
    _connection_pool: Optional[RabbitMQConnectionPool] = None
    _is_shutdown: bool = False
    _shutdown_lock = asyncio.Lock()

    # 配置常量
    RECONNECT_INTERVAL = 15  # 重连基础间隔（秒）
    CONNECTION_POOL_TIMEOUT = 30  # 连接池初始化超时（秒）

    @classmethod
    def init_config(cls, config: dict) -> None:
        """初始化基础配置（从Nacos加载）"""
        from sycommon.synacos.nacos_service import NacosService

        if cls._config:
            logger.warning("RabbitMQ配置已初始化，无需重复调用")
            return

        # 从Nacos获取MQ配置
        cls._config = NacosService(config).share_configs.get(
            "mq.yml", {}).get('spring', {}).get('rabbitmq', {})
        cls._config["APP_NAME"] = config.get("Name", "")

        # 打印关键配置信息
        logger.info(
            f"RabbitMQ服务初始化 - 集群节点: {cls._config.get('host')}, "
            f"端口: {cls._config.get('port')}, "
            f"虚拟主机: {cls._config.get('virtual-host')}, "
            f"应用名: {cls._config.get('APP_NAME')}, "
            f"心跳: {cls._config.get('heartbeat', 30)}s"
        )
        cls._is_shutdown = False

    @classmethod
    async def init_connection_pool(cls) -> None:
        """初始化单通道连接池（带重试机制）"""
        if cls._connection_pool or not cls._config or cls._is_shutdown:
            return

        try:
            # 解析集群节点
            hosts_str = cls._config.get('host', "")
            hosts_list = [host.strip()
                          for host in hosts_str.split(',') if host.strip()]
            if not hosts_list:
                raise ValueError("RabbitMQ集群配置为空，请检查host参数")

            global_prefetch_count = cls._config.get('prefetch_count', 2)

            # 创建单通道连接池
            cls._connection_pool = RabbitMQConnectionPool(
                hosts=hosts_list,
                port=cls._config.get('port', 5672),
                username=cls._config.get('username', ""),
                password=cls._config.get('password', ""),
                virtualhost=cls._config.get('virtual-host', "/"),
                app_name=cls._config.get("APP_NAME", ""),
                prefetch_count=global_prefetch_count,
                heartbeat=cls._config.get('heartbeat', 15),
                connection_timeout=cls._config.get('connection_timeout', 15),
                reconnect_interval=cls._config.get('reconnect_interval', 5),
            )

            # 初始化连接池
            await asyncio.wait_for(cls._connection_pool.init_pools(), timeout=cls.CONNECTION_POOL_TIMEOUT)
            logger.info("RabbitMQ单通道连接池初始化成功")

        except Exception as e:
            logger.error(f"RabbitMQ连接池初始化失败: {str(e)}", exc_info=True)
            # 连接池初始化失败时重试（未关闭状态下）
            if not cls._is_shutdown:
                await asyncio.sleep(cls.RECONNECT_INTERVAL)
                asyncio.create_task(cls.init_connection_pool())

    @classmethod
    async def wait_for_pool_ready(cls) -> None:
        """等待连接池就绪（带超时）"""
        if not cls._config:
            raise ValueError("RabbitMQ配置尚未初始化，请先调用init_config方法")

        start_time = asyncio.get_event_loop().time()
        while not (cls._connection_pool and cls._connection_pool._initialized) and not cls._is_shutdown:
            if asyncio.get_event_loop().time() - start_time > cls.CONNECTION_POOL_TIMEOUT:
                raise TimeoutError("等待连接池初始化超时")
            await asyncio.sleep(1)

        if cls._is_shutdown:
            raise RuntimeError("服务关闭中，取消等待连接池")

    @classmethod
    async def shutdown_core_resources(cls, timeout: float = 15.0) -> None:
        """关闭核心资源（连接池）"""
        # 关闭连接池
        if cls._connection_pool and cls._connection_pool._initialized:
            try:
                await cls._connection_pool.close()
                logger.info("RabbitMQ单通道连接池已关闭")
            except Exception as e:
                logger.error(f"关闭连接池失败: {str(e)}")

        # 清理核心状态
        cls._config = None
        cls._connection_pool = None
