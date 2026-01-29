import asyncio
from typing import Optional
from sycommon.rabbitmq.rabbitmq_service_client_manager import RabbitMQClientManager
from sycommon.logging.kafka_log import SYLogger

logger = SYLogger


class RabbitMQConnectionMonitor(RabbitMQClientManager):
    """
    RabbitMQ连接监控类 - 负责连接状态监控、自动重连
    """
    _connection_monitor_task: Optional[asyncio.Task] = None

    @classmethod
    async def _monitor_connections(cls):
        """连接监控任务：定期检查所有客户端连接状态"""
        logger.info("RabbitMQ连接监控任务启动")
        while not cls._is_shutdown:
            try:
                await asyncio.sleep(cls.RECONNECT_INTERVAL)

                # 跳过未初始化的连接池
                if not cls._connection_pool or not cls._connection_pool._initialized:
                    continue

                # 检查连接池本身状态
                pool_alive = await cls._connection_pool.is_alive
                if not pool_alive:
                    logger.error("RabbitMQ连接池已断开，等待原生自动重连")
                    continue

                # 检查所有客户端连接
                for client_name, client in list(cls._clients.items()):
                    try:
                        client_connected = await client.is_connected
                        if not client_connected:
                            logger.warning(
                                f"客户端 '{client_name}' 连接异常，触发重连")
                            asyncio.create_task(
                                cls._reconnect_client(client_name, client))
                    except Exception as e:
                        logger.error(
                            f"监控客户端 '{client_name}' 连接状态失败: {str(e)}", exc_info=True)

            except Exception as e:
                logger.error("RabbitMQ连接监控任务异常", exc_info=True)
                await asyncio.sleep(cls.RECONNECT_INTERVAL)

        logger.info("RabbitMQ连接监控任务停止")

    @classmethod
    def start_connection_monitor(cls) -> None:
        """启动连接监控任务"""
        if cls._connection_monitor_task and not cls._connection_monitor_task.done():
            return

        cls._connection_monitor_task = asyncio.create_task(
            cls._monitor_connections())

    @classmethod
    async def stop_connection_monitor(cls, timeout: float = 15.0) -> None:
        """停止连接监控任务"""
        if cls._connection_monitor_task and not cls._connection_monitor_task.done():
            cls._connection_monitor_task.cancel()
            try:
                await asyncio.wait_for(cls._connection_monitor_task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("连接监控任务关闭超时")
            except Exception as e:
                logger.error(f"关闭连接监控任务失败: {str(e)}")

        cls._connection_monitor_task = None
