from typing import Dict
import asyncio

from sycommon.logging.kafka_log import SYLogger
from sycommon.rabbitmq.rabbitmq_client import RabbitMQClient
from sycommon.rabbitmq.rabbitmq_service_core import RabbitMQCoreService

logger = SYLogger


class RabbitMQClientManager(RabbitMQCoreService):
    """
    RabbitMQ客户端管理类 - 负责客户端的创建、获取、重连、资源清理
    """
    # 客户端存储
    _clients: Dict[str, RabbitMQClient] = {}
    _init_locks: Dict[str, asyncio.Lock] = {}

    # 模式标记
    _has_listeners: bool = False
    _has_senders: bool = False

    @classmethod
    def set_mode_flags(cls, has_listeners: bool = False, has_senders: bool = False) -> None:
        """设置模式标记（是否有监听器/发送器）"""
        cls._has_listeners = has_listeners
        cls._has_senders = has_senders

    @classmethod
    async def _clean_client_resources(cls, client: RabbitMQClient) -> None:
        """清理客户端无效资源"""
        try:
            # 先停止消费
            if client._consumer_tag:
                await client.stop_consuming()
            logger.debug("客户端无效资源清理完成（单通道无需归还）")
        except Exception as e:
            logger.warning(f"释放客户端无效资源失败: {str(e)}")
        finally:
            # 强制重置客户端状态
            client._channel = None
            client._channel_conn = None
            client._exchange = None
            client._queue = None
            client._consumer_tag = None

    @classmethod
    async def _reconnect_client(cls, client_name: str, client: RabbitMQClient) -> bool:
        """客户端重连"""
        if cls._is_shutdown or not (cls._connection_pool and await cls._connection_pool.is_alive):
            return False

        # 重连冷却
        await asyncio.sleep(cls.RECONNECT_INTERVAL)

        try:
            # 清理旧资源
            await cls._clean_client_resources(client)

            # 执行重连
            await client.connect()

            # 验证重连结果
            if await client.is_connected:
                logger.info(f"客户端 '{client_name}' 重连成功")
                return True
            else:
                logger.warning(f"客户端 '{client_name}' 重连失败：资源未完全初始化")
                return False
        except Exception as e:
            logger.error(f"客户端 '{client_name}' 重连失败: {str(e)}", exc_info=True)
            return False

    @classmethod
    async def _create_client(cls, **kwargs) -> RabbitMQClient:
        """创建客户端实例"""
        if cls._is_shutdown:
            raise RuntimeError("RabbitMQService已关闭，无法创建客户端")

        # 等待连接池就绪
        await cls.wait_for_pool_ready()

        app_name = kwargs.get('app_name', cls._config.get(
            "APP_NAME", "")) if cls._config else ""
        queue_name = kwargs.get('queue_name', '')

        create_if_not_exists = kwargs.get('create_if_not_exists', True)

        processed_queue_name = queue_name
        if create_if_not_exists and processed_queue_name and app_name:
            if not processed_queue_name.endswith(f".{app_name}"):
                processed_queue_name = f"{processed_queue_name}.{app_name}"
                logger.info(f"监听器队列名称自动拼接app-name: {processed_queue_name}")
            else:
                logger.info(f"监听器队列已包含app-name: {processed_queue_name}")

        logger.info(
            f"创建客户端 - 原始队列名: {queue_name}, "
            f"处理后队列名: {processed_queue_name}, "
            f"是否创建队列: {create_if_not_exists}"
        )

        final_queue_name = None
        if create_if_not_exists and processed_queue_name.endswith(f".{app_name}"):
            final_queue_name = processed_queue_name

        # 创建客户端实例
        client = RabbitMQClient(
            connection_pool=cls._connection_pool,
            exchange_name=cls._config.get(
                'exchange_name', "system.topic.exchange"),
            exchange_type=kwargs.get('exchange_type', "topic"),
            queue_name=final_queue_name,
            app_name=app_name,
            routing_key=kwargs.get(
                'routing_key',
                f"{queue_name.split('.')[0]}.#"
            ),
            durable=kwargs.get('durable', True),
            auto_delete=kwargs.get('auto_delete', False),
            auto_parse_json=kwargs.get('auto_parse_json', True),
            create_if_not_exists=create_if_not_exists,
            prefetch_count=kwargs.get('prefetch_count', 2),
        )

        # 连接客户端
        await client.connect()

        return client

    @classmethod
    async def get_client(
        cls,
        client_name: str = "default",
        client_type: str = "sender",  # sender（发送器）/listener（监听器），默认sender
        **kwargs
    ) -> RabbitMQClient:
        """
        获取或创建RabbitMQ客户端
        :param client_name: 客户端名称
        :param client_type: 客户端类型 - sender(发送器)/listener(监听器)
        :param kwargs: 其他参数
        :return: RabbitMQClient实例
        """
        if cls._is_shutdown:
            raise RuntimeError("RabbitMQService已关闭，无法获取客户端")

        # 校验client_type合法性
        if client_type not in ["sender", "listener"]:
            raise ValueError(
                f"client_type只能是sender/listener，当前值：{client_type}")

        # 等待连接池就绪
        await cls.wait_for_pool_ready()

        # 确保锁存在
        if client_name not in cls._init_locks:
            cls._init_locks[client_name] = asyncio.Lock()

        async with cls._init_locks[client_name]:
            # ===== 原有“客户端已存在”的逻辑保留 =====
            if client_name in cls._clients:
                client = cls._clients[client_name]
                # 核心：根据client_type重置客户端的队列创建配置
                if client_type == "sender":
                    client.create_if_not_exists = False
                else:  # listener
                    client.create_if_not_exists = True
                    # 监听器必须有队列名，从kwargs补全
                    if not client.queue_name and kwargs.get("queue_name"):
                        client.queue_name = kwargs.get("queue_name")

                if await client.is_connected:
                    return client
                else:
                    logger.info(f"客户端 '{client_name}' 连接已断开，重新创建")
                    await cls._clean_client_resources(client)

            # ===== 核心逻辑：根据client_type统一控制队列创建 =====
            if client_type == "sender":
                kwargs["create_if_not_exists"] = False  # 禁用创建队列
            else:
                if not kwargs.get("queue_name"):
                    raise ValueError("监听器类型必须指定queue_name参数")
                kwargs["create_if_not_exists"] = True

            client = await cls._create_client(
                **kwargs
            )

            # 监听器额外验证队列创建结果
            if client_type == "listener" and not client._queue:
                raise RuntimeError(f"监听器队列 '{kwargs['queue_name']}' 创建失败")

            # 存储客户端
            cls._clients[client_name] = client
            return client

    @classmethod
    async def shutdown_clients(cls, timeout: float = 15.0) -> None:
        """关闭所有客户端"""
        # 关闭所有客户端
        for client in cls._clients.values():
            try:
                await client.close()
            except Exception as e:
                logger.error(f"关闭客户端失败: {str(e)}")

        # 清理客户端状态
        cls._clients.clear()
        cls._init_locks.clear()
