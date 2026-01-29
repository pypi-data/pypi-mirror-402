from typing import Dict, List, Callable, Coroutine, Any
import asyncio
from aio_pika.abc import AbstractIncomingMessage, ConsumerTag

from sycommon.logging.kafka_log import SYLogger
from sycommon.models.mqlistener_config import RabbitMQListenerConfig
from sycommon.rabbitmq.rabbitmq_service_client_manager import RabbitMQClientManager
from sycommon.models.mqmsg_model import MQMsgModel

logger = SYLogger


class RabbitMQConsumerManager(RabbitMQClientManager):
    """
    RabbitMQ消费者管理类 - 负责监听器设置、消费启动/停止、消费验证
    """
    # 消费者相关状态
    _message_handlers: Dict[str, Callable[[
        MQMsgModel, AbstractIncomingMessage], Coroutine[Any, Any, None]]] = {}
    _consumer_tasks: Dict[str, asyncio.Task] = {}
    _consumer_events: Dict[str, asyncio.Event] = {}
    _consumer_tags: Dict[str, ConsumerTag] = {}

    # 配置常量
    CONSUMER_START_TIMEOUT = 30  # 消费启动超时（秒）

    @classmethod
    async def add_listener(
        cls,
        queue_name: str,
        handler: Callable[[MQMsgModel, AbstractIncomingMessage], Coroutine[Any, Any, None]], **kwargs
    ) -> None:
        """添加消息监听器"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法添加监听器")
            return

        if queue_name in cls._message_handlers:
            logger.info(f"监听器 '{queue_name}' 已存在，跳过重复添加")
            return

        # 创建并初始化客户端
        await cls.get_client(
            client_name=queue_name,
            client_type="listener",
            queue_name=queue_name,
            ** kwargs
        )

        # 注册消息处理器
        cls._message_handlers[queue_name] = handler
        logger.info(f"监听器 '{queue_name}' 已添加")

    @classmethod
    async def setup_listeners(cls, listeners: List[RabbitMQListenerConfig], has_senders: bool = False, **kwargs) -> None:
        """设置消息监听器"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法设置监听器")
            return

        cls.set_mode_flags(has_listeners=True, has_senders=has_senders)
        logger.info(f"开始设置 {len(listeners)} 个消息监听器")

        for idx, listener_config in enumerate(listeners):
            try:
                # 转换配置
                listener_dict = listener_config.model_dump()
                listener_dict['create_if_not_exists'] = True
                listener_dict['prefetch_count'] = listener_config.prefetch_count
                queue_name = listener_dict['queue_name']

                logger.info(
                    f"设置监听器 {idx+1}/{len(listeners)}: {queue_name} (prefetch_count: {listener_config.prefetch_count})")

                # 添加监听器
                await cls.add_listener(**listener_dict)
            except Exception as e:
                logger.error(
                    f"设置监听器 {idx+1} 失败: {str(e)}", exc_info=True)
                logger.warning("继续处理其他监听器")

        # 启动所有消费者
        await cls.start_all_consumers()

        # 验证消费者启动结果
        await cls._verify_consumers_started()

        logger.info(f"消息监听器设置完成")

    @classmethod
    async def _verify_consumers_started(cls, timeout: int = 30) -> None:
        """验证消费者是否成功启动"""
        start_time = asyncio.get_event_loop().time()
        required_clients = list(cls._message_handlers.keys())
        running_clients = []

        while len(running_clients) < len(required_clients) and \
                (asyncio.get_event_loop().time() - start_time) < timeout and \
                not cls._is_shutdown:

            running_clients = [
                name for name, task in cls._consumer_tasks.items()
                if not task.done() and name in cls._consumer_tags
            ]

            logger.info(
                f"消费者启动验证: {len(running_clients)}/{len(required_clients)} 已启动")
            await asyncio.sleep(1)

        failed_clients = [
            name for name in required_clients if name not in running_clients and not cls._is_shutdown]
        if failed_clients:
            logger.error(f"以下消费者启动失败: {', '.join(failed_clients)}")
            for client_name in failed_clients:
                logger.info(f"尝试重新启动消费者: {client_name}")
                asyncio.create_task(cls.start_consumer(client_name))

    @classmethod
    async def start_all_consumers(cls) -> None:
        """启动所有已注册的消费者"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法启动消费者")
            return

        for client_name in cls._message_handlers:
            await cls.start_consumer(client_name)

    @classmethod
    async def start_consumer(cls, client_name: str) -> None:
        """启动指定客户端的消费者"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法启动消费者")
            return

        # 检查任务状态
        if client_name in cls._consumer_tasks:
            existing_task = cls._consumer_tasks[client_name]
            if not existing_task.done():
                if existing_task.exception() is not None:
                    logger.info(f"消费者 '{client_name}' 任务异常，重启")
                    existing_task.cancel()
                else:
                    logger.info(f"消费者 '{client_name}' 已在运行中，无需重复启动")
                    return
            else:
                logger.info(f"消费者 '{client_name}' 任务已完成，重新启动")

        if client_name not in cls._clients:
            raise ValueError(f"RabbitMQ客户端 '{client_name}' 未初始化")

        client = cls._clients[client_name]
        handler = cls._message_handlers.get(client_name)

        if not handler:
            logger.warning(f"未找到客户端 '{client_name}' 的处理器")
            return

        # 设置消息处理器
        await client.set_message_handler(handler)

        # 确保客户端已连接
        start_time = asyncio.get_event_loop().time()
        while not await client.is_connected and not cls._is_shutdown:
            if asyncio.get_event_loop().time() - start_time > cls.CONSUMER_START_TIMEOUT:
                raise TimeoutError(f"等待客户端 '{client_name}' 连接超时")

            logger.info(f"等待客户端 '{client_name}' 连接就绪...")
            await asyncio.sleep(1)
        if cls._is_shutdown:
            return

        # 创建停止事件
        stop_event = asyncio.Event()
        cls._consumer_events[client_name] = stop_event

        # 定义消费任务
        async def consume_task():
            try:
                # 启动消费，带重试机制
                max_attempts = 3
                attempt = 0
                consumer_tag = None

                while attempt < max_attempts and not stop_event.is_set() and not cls._is_shutdown:
                    try:
                        # 启动消费前再次校验
                        if not await client.is_connected:
                            logger.info(f"消费者 '{client_name}' 连接断开，尝试重连")
                            await client.connect()

                        if not client._queue:
                            raise Exception("队列未初始化完成")
                        if not client._message_handler:
                            raise Exception("消息处理器未设置")

                        consumer_tag = await client.start_consuming()
                        if consumer_tag:
                            break
                    except Exception as e:
                        attempt += 1
                        logger.warning(
                            f"启动消费者尝试 {attempt}/{max_attempts} 失败: {str(e)}")
                        if attempt < max_attempts:
                            await asyncio.sleep(2)

                if cls._is_shutdown:
                    return

                if not consumer_tag:
                    raise Exception(f"经过 {max_attempts} 次尝试仍无法启动消费者")

                # 记录消费者标签
                cls._consumer_tags[client_name] = consumer_tag
                logger.info(
                    f"消费者 '{client_name}' 开始消费（单通道），tag: {consumer_tag}"
                )

                # 等待停止事件
                await stop_event.wait()
                logger.info(f"收到停止信号，消费者 '{client_name}' 准备退出")

            except asyncio.CancelledError:
                logger.info(f"消费者 '{client_name}' 被取消")
            except Exception as e:
                logger.error(
                    f"消费者 '{client_name}' 错误: {str(e)}", exc_info=True)
                # 非主动停止时尝试重启
                if not stop_event.is_set() and not cls._is_shutdown:
                    logger.info(f"尝试重启消费者 '{client_name}'")
                    await asyncio.sleep(cls.RECONNECT_INTERVAL)
                    asyncio.create_task(cls.start_consumer(client_name))
            finally:
                # 清理资源
                try:
                    await client.stop_consuming()
                except Exception as e:
                    logger.error(f"停止消费者 '{client_name}' 时出错: {str(e)}")

                # 移除状态记录
                if client_name in cls._consumer_tags:
                    del cls._consumer_tags[client_name]
                if client_name in cls._consumer_events:
                    del cls._consumer_events[client_name]

                logger.info(f"消费者 '{client_name}' 已停止")

        # 创建并跟踪消费任务
        task = asyncio.create_task(
            consume_task(), name=f"consumer-{client_name}")
        cls._consumer_tasks[client_name] = task

        # 添加任务完成回调
        def task_done_callback(t: asyncio.Task) -> None:
            try:
                if t.done():
                    t.result()
            except Exception as e:
                logger.error(f"消费者任务 '{client_name}' 异常结束: {str(e)}")
                if client_name in cls._message_handlers and not cls._is_shutdown:
                    asyncio.create_task(cls.start_consumer(client_name))

        task.add_done_callback(task_done_callback)
        logger.info(f"消费者任务 '{client_name}' 已创建")

    @classmethod
    async def shutdown_consumers(cls, timeout: float = 15.0) -> None:
        """关闭所有消费者"""
        # 停止所有消费者任务
        for client_name, task in cls._consumer_tasks.items():
            if not task.done():
                # 触发停止事件
                if client_name in cls._consumer_events:
                    cls._consumer_events[client_name].set()
                # 取消任务
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=timeout)
                except Exception as e:
                    logger.error(f"关闭消费者 '{client_name}' 失败: {str(e)}")

        # 清理消费者状态
        cls._message_handlers.clear()
        cls._consumer_tasks.clear()
        cls._consumer_events.clear()
        cls._consumer_tags.clear()
