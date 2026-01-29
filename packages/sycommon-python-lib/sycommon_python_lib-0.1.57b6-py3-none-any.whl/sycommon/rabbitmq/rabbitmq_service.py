from typing import Type
import asyncio
from sycommon.logging.kafka_log import SYLogger
from sycommon.rabbitmq.rabbitmq_service_connection_monitor import RabbitMQConnectionMonitor
from sycommon.rabbitmq.rabbitmq_service_consumer_manager import RabbitMQConsumerManager
from sycommon.rabbitmq.rabbitmq_service_producer_manager import RabbitMQProducerManager

logger = SYLogger


class RabbitMQService(RabbitMQConnectionMonitor, RabbitMQProducerManager, RabbitMQConsumerManager):
    """
    RabbitMQ服务对外统一接口 - 保持原有API兼容
    """
    @classmethod
    def init(cls, config: dict, has_listeners: bool = False, has_senders: bool = False) -> Type['RabbitMQService']:
        """初始化RabbitMQ服务（保持原有接口）"""
        # 初始化配置
        cls.init_config(config)

        # 设置模式标记
        cls.set_mode_flags(has_listeners=has_listeners,
                           has_senders=has_senders)

        # 初始化连接池
        asyncio.create_task(cls.init_connection_pool())

        # 启动连接监控
        cls.start_connection_monitor()

        return cls

    @classmethod
    async def shutdown(cls, timeout: float = 15.0) -> None:
        """优雅关闭所有资源（保持原有接口）"""
        async with cls._shutdown_lock:
            if cls._is_shutdown:
                logger.info("RabbitMQService已关闭，无需重复操作")
                return

            cls._is_shutdown = True
            logger.info("开始关闭RabbitMQ服务...")

            # 1. 停止连接监控任务
            await cls.stop_connection_monitor(timeout)

            # 2. 停止所有消费者任务
            await cls.shutdown_consumers(timeout)

            # 3. 关闭所有客户端
            await cls.shutdown_clients(timeout)

            # 4. 关闭连接池
            await cls.shutdown_core_resources(timeout)

            # 5. 清理剩余状态
            cls.clear_senders()

            logger.info("RabbitMQService已完全关闭")
