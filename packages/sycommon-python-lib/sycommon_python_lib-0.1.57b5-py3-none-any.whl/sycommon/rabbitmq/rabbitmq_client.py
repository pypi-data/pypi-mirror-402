import asyncio
import json
from typing import Optional, Callable, Coroutine, Dict, Any, Union
from aio_pika import Channel, Message, DeliveryMode, ExchangeType
from aio_pika.abc import (
    AbstractExchange,
    AbstractQueue,
    AbstractIncomingMessage,
    ConsumerTag,
    AbstractRobustConnection,
)
from sycommon.rabbitmq.rabbitmq_pool import RabbitMQConnectionPool
from sycommon.logging.kafka_log import SYLogger
from sycommon.models.mqmsg_model import MQMsgModel

logger = SYLogger


class RabbitMQClient:
    """
    RabbitMQ 客户端
    """

    def __init__(
        self,
        connection_pool: RabbitMQConnectionPool,
        exchange_name: str = "system.topic.exchange",
        exchange_type: str = "topic",
        queue_name: Optional[str] = None,
        app_name: Optional[str] = None,
        routing_key: str = "#",
        durable: bool = True,
        auto_delete: bool = False,
        auto_parse_json: bool = True,
        create_if_not_exists: bool = True,
        **kwargs,
    ):
        self.connection_pool = connection_pool
        if not self.connection_pool._initialized:
            raise RuntimeError("连接池未初始化，请先调用 connection_pool.init_pools()")

        self.exchange_name = exchange_name.strip()
        try:
            self.exchange_type = ExchangeType(exchange_type.lower())
        except ValueError:
            logger.warning(f"无效的exchange_type: {exchange_type}，默认使用'topic'")
            self.exchange_type = ExchangeType.TOPIC

        self.app_name = app_name.strip() if app_name else None
        self.queue_name = queue_name.strip() if queue_name else None
        self.routing_key = routing_key.strip() if routing_key else "#"
        self.durable = durable
        self.auto_delete = auto_delete
        self.auto_parse_json = auto_parse_json
        self.create_if_not_exists = create_if_not_exists

        # 资源状态
        self._channel: Optional[Channel] = None
        self._channel_conn: Optional[AbstractRobustConnection] = None
        self._exchange: Optional[AbstractExchange] = None
        self._queue: Optional[AbstractQueue] = None
        self._consumer_tag: Optional[ConsumerTag] = None
        self._message_handler: Optional[Callable[[
            MQMsgModel, AbstractIncomingMessage], Coroutine[Any, Any, None]]] = None
        self._closed = False

        # 并发控制
        self._consume_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()

        # 防止并发重连覆盖
        self._connecting = False
        self._connect_condition = asyncio.Condition()

        self._conn_close_callback: Optional[Callable] = None
        self._reconnect_semaphore = asyncio.Semaphore(1)
        self._current_reconnect_task: Optional[asyncio.Task] = None
        self._RECONNECT_INTERVAL = 15

    @property
    async def is_connected(self) -> bool:
        if self._closed:
            return False
        try:
            return (
                self._channel and not self._channel.is_closed
                and self._channel_conn and not self._channel_conn.is_closed
                and self._exchange is not None
                and (not self.queue_name or self._queue is not None)
            )
        except Exception:
            return False

    async def _rebuild_resources(self) -> None:
        if not self._channel or self._channel.is_closed:
            raise RuntimeError("无有效通道，无法重建资源")

        # 声明交换机
        self._exchange = await self._channel.declare_exchange(
            name=self.exchange_name,
            type=self.exchange_type,
            durable=self.durable,
            auto_delete=self.auto_delete,
            passive=not self.create_if_not_exists,
        )
        logger.info(f"交换机重建成功: {self.exchange_name}")

        # 声明队列
        if self.queue_name and self.queue_name.endswith(f".{self.app_name}"):
            self._queue = await self._channel.declare_queue(
                name=self.queue_name,
                durable=self.durable,
                auto_delete=self.auto_delete,
                passive=not self.create_if_not_exists,
            )
            await self._queue.bind(exchange=self._exchange, routing_key=self.routing_key)
            logger.info(f"队列重建成功: {self.queue_name}")

    async def connect(self) -> None:
        if self._closed:
            raise RuntimeError("客户端已关闭，无法重新连接")

        # 1. 并发控制：使用 _connect_lock 保证只有一个协程在执行连接流程
        async with self._connect_lock:
            # 如果已经在连了，等待其完成
            if self._connecting:
                logger.debug("连接正在进行中，等待现有连接完成...")
                try:
                    # 等待条件变量，超时设为 60 秒防止死等
                    await asyncio.wait_for(
                        self._connect_condition.wait_for(
                            lambda: not self._connecting),
                        timeout=60.0
                    )
                except asyncio.TimeoutError:
                    raise RuntimeError("等待连接超时")

                # 等待结束后，再次检查状态
                if not await self.is_connected:
                    raise RuntimeError("等待重连后，连接状态依然无效")
                return

            # 标记开始连接
            self._connecting = True

        # 释放 _connect_lock，允许其他协程读取状态，但在连接完成前阻止新的连接请求
        # 注意：这里释放了 _connect_lock，但 self._connecting = True 阻止了新的连接流程

        try:
            # --- 阶段1: 清理旧资源 ---
            # 重新获取锁进行资源清理
            async with self._connect_lock:
                was_consuming = self._consumer_tag is not None

                if self._channel_conn and self._conn_close_callback:
                    try:
                        self._channel_conn.close_callbacks.discard(
                            self._conn_close_callback)
                    except Exception:
                        pass

                self._channel = None
                self._channel_conn = None
                self._exchange = None
                self._queue = None
                self._conn_close_callback = None

            # --- 阶段2: 获取新连接 (耗时IO) ---
            self._channel, self._channel_conn = await self.connection_pool.acquire_channel()

            # 设置回调
            def on_conn_closed(conn, exc):
                logger.warning(f"检测到连接关闭: {exc}")
                if not self._closed and not self._connecting:
                    asyncio.create_task(self._safe_reconnect())

            self._conn_close_callback = on_conn_closed
            if self._channel_conn:
                self._channel_conn.close_callbacks.add(
                    self._conn_close_callback)

            # 重建资源
            await self._rebuild_resources()

            # --- 阶段3: 恢复消费 ---
            if was_consuming and self._message_handler and self.queue_name and self.queue_name.endswith(f".{self.app_name}"):
                logger.info("🔄 检测到重连前处于消费状态，尝试自动恢复...")
                try:
                    self._queue = await self._channel.declare_queue(
                        name=self.queue_name,
                        durable=self.durable,
                        auto_delete=self.auto_delete,
                        passive=False,
                    )
                    await self._queue.bind(exchange=self._exchange, routing_key=self.routing_key)
                    self._consumer_tag = await self._queue.consume(self._process_message_callback)
                    logger.info(f"✅ 消费已自动恢复: {self._consumer_tag}")
                except Exception as e:
                    logger.error(f"❌ 自动恢复消费失败: {e}")
                    self._consumer_tag = None
            else:
                self._consumer_tag = None

            logger.info("客户端连接初始化完成")

        except Exception as e:
            logger.error(f"客户端连接失败: {str(e)}", exc_info=True)

            # 异常时清理资源
            async with self._connect_lock:
                if self._channel_conn and self._conn_close_callback:
                    self._channel_conn.close_callbacks.discard(
                        self._conn_close_callback)
                self._channel = None
                self._channel_conn = None
                self._consumer_tag = None

            raise

        finally:
            # 【关键修复】必须在持有 Condition 内部锁的情况下调用 notify_all
            # 这里使用 async with self._connect_condition: 自动完成 acquire() ... notify_all() ... release()
            async with self._connect_condition:
                self._connecting = False
                self._connect_condition.notify_all()

    async def _safe_reconnect(self):
        """安全重连任务（仅用于被动监听连接关闭）"""
        async with self._reconnect_semaphore:
            if self._closed:
                return

            # 如果已经在重连，直接忽略
            if self._connecting:
                return

            logger.info(f"将在{self._RECONNECT_INTERVAL}秒后尝试重连...")
            await asyncio.sleep(self._RECONNECT_INTERVAL)

            if self._closed or await self.is_connected:
                return

            try:
                self._current_reconnect_task = asyncio.create_task(
                    self.connect())
                await self._current_reconnect_task
            except Exception as e:
                logger.warning(f"重连失败: {str(e)}")
            finally:
                self._current_reconnect_task = None

    async def set_message_handler(self, handler: Callable[..., Coroutine]) -> None:
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError("消息处理器必须是协程函数")
        async with self._consume_lock:
            self._message_handler = handler

    async def _process_message_callback(self, message: AbstractIncomingMessage):
        # 记录消息的原始追踪ID
        original_trace_id = message.headers.get(
            "trace-id") if message.headers else None
        current_retry = 0

        try:
            msg_obj: MQMsgModel

            # 1. 解析消息
            if self.auto_parse_json:
                try:
                    body_dict = json.loads(message.body.decode("utf-8"))
                    msg_obj = MQMsgModel(**body_dict)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    await message.reject(requeue=False)
                    return
            else:
                msg_obj = MQMsgModel(
                    body=message.body.decode("utf-8"),
                    routing_key=message.routing_key,
                    delivery_tag=message.delivery_tag,
                    traceId=original_trace_id,
                )

            # 2. 设置日志上下文
            # 注意：如果 header 中有 x-last-retry-ts，说明之前重试过
            current_retry = int(message.headers.get("x-retry-count", 0))
            SYLogger.set_trace_id(msg_obj.traceId)

            # 3. 执行业务逻辑
            if self._message_handler:
                await self._message_handler(msg_obj, message)

            # 4. 业务成功，Ack (移除 finally 中的 ack，成功即确认)
            await message.ack()

        except Exception as e:
            logger.error(f"消息处理异常 (第 {current_retry} 次尝试): {e}", exc_info=True)

            # 【核心修复】使用原生 Nack + Requeue
            if current_retry >= 3:
                # 超过重试次数，丢弃消息（或进入死信队列）
                logger.warning(f"重试次数超限 (3次)，丢弃消息: {message.delivery_tag}")
                await message.reject(requeue=False)
            else:
                # 还没到重试上限，重新入队
                # 为了防止立即重试导致的死循环，我们需要人为增加一点延迟
                # 但 Nack 本身不支持延迟，所以这里只能快速 Nack 让它尽快回来，
                # 并在业务层（或外层）做好限流保护。

                # 如果你有延迟队列插件，可以 publish 到延迟交换机。
                # 如果没有，直接 requeue 是最安全的不丢包方案。
                logger.info(f"消息处理失败，重新入队等待重试... (当前重试: {current_retry})")

                # 技巧：如果你不想立即重试，可以 Nack(False) 然后手动 Publish 延迟消息
                # 但为了解决你当前的“死循环”问题，直接 Nack(True) 是最有效的
                # 延迟5秒
                await asyncio.sleep(5)
                await message.nack(requeue=True)

    async def start_consuming(self) -> Optional[ConsumerTag]:
        if self._closed:
            raise RuntimeError("客户端已关闭，无法启动消费")

        async with self._consume_lock:
            if not self._message_handler:
                raise RuntimeError("未设置消息处理器")

            if not await self.is_connected:
                await self.connect()

            if not self._queue:
                if self.queue_name and self.queue_name.endswith(f".{self.app_name}"):
                    self._queue = await self._channel.declare_queue(
                        name=self.queue_name,
                        durable=self.durable,
                        auto_delete=self.auto_delete,
                        passive=not self.create_if_not_exists,
                    )
                    await self._queue.bind(exchange=self._exchange, routing_key=self.routing_key)
                else:
                    raise RuntimeError("未配置队列名")

            self._consumer_tag = await self._queue.consume(self._process_message_callback)
            logger.info(
                f"开始消费队列: {self._queue.name}，tag: {self._consumer_tag}")
            return self._consumer_tag

    async def stop_consuming(self) -> None:
        async with self._consume_lock:
            if self._consumer_tag and self._queue and self._channel:
                try:
                    await self._queue.cancel(self._consumer_tag)
                    logger.info(f"停止消费成功: {self._consumer_tag}")
                except Exception as e:
                    logger.warning(f"停止消费异常: {e}")
            self._consumer_tag = None

    async def _handle_publish_failure(self):
        try:
            logger.info("检测到发布异常，强制连接池切换节点...")
            await self.connection_pool.force_reconnect()
            # 连接池切换后，必须刷新客户端资源
            await self.connect()
            logger.info("故障转移完成，资源已刷新")
        except Exception as e:
            logger.error(f"故障转移失败: {e}")
            raise

    async def publish(
        self,
        message_body: Union[str, Dict[str, Any], MQMsgModel],
        headers: Optional[Dict[str, Any]] = None,
        content_type: str = "application/json",
        delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT,
        retry_count: int = 3,
    ) -> None:
        if self._closed:
            raise RuntimeError("客户端已关闭，无法发布消息")

        try:
            if isinstance(message_body, MQMsgModel):
                body = json.dumps(message_body.to_dict(),
                                  ensure_ascii=False).encode("utf-8")
            elif isinstance(message_body, dict):
                body = json.dumps(
                    message_body, ensure_ascii=False).encode("utf-8")
            elif isinstance(message_body, str):
                body = message_body.encode("utf-8")
            else:
                raise TypeError(f"不支持的消息体类型: {type(message_body)}")
        except Exception as e:
            logger.error(f"消息体序列化失败: {e}")
            raise

        message = Message(body=body, headers=headers or {},
                          content_type=content_type, delivery_mode=delivery_mode)
        last_exception = None

        for retry in range(retry_count):
            try:
                if not await self.is_connected:
                    await self.connect()

                result = await self._exchange.publish(
                    message=message,
                    routing_key=self.routing_key,
                    mandatory=True,
                    timeout=5.0
                )

                if result is None:
                    raise RuntimeError(f"消息未找到匹配的队列: {self.routing_key}")

                logger.info(f"发布成功: {self.routing_key}")
                return

            except RuntimeError as e:
                if "未找到匹配的队列" in str(e):
                    raise
                last_exception = str(e)
                await self._handle_publish_failure()

            except Exception as e:
                last_exception = str(e)
                logger.error(f"发布异常: {e}")
                await self._handle_publish_failure()

            await asyncio.sleep(5)

        raise RuntimeError(f"消息发布最终失败: {last_exception}")

    async def close(self) -> None:
        self._closed = True
        logger.info("开始关闭RabbitMQ客户端...")

        if self._current_reconnect_task and not self._current_reconnect_task.done():
            self._current_reconnect_task.cancel()
            try:
                await self._current_reconnect_task
            except asyncio.CancelledError:
                pass

        await self.stop_consuming()

        async with self._connect_lock:
            if self._conn_close_callback and self._channel_conn:
                self._channel_conn.close_callbacks.discard(
                    self._conn_close_callback)

            self._channel = None
            self._channel_conn = None
            self._exchange = None
            self._queue = None
            self._message_handler = None

            # 确保唤醒可能正在等待 connect 的任务
            self._connecting = False
            self._connect_condition.notify_all()

        logger.info("客户端已关闭")
