import asyncio
import random
from typing import Optional, List, Dict, Callable, Tuple
from aio_pika import connect_robust, RobustChannel, Message
from aio_pika.abc import (
    AbstractRobustConnection, AbstractQueue, AbstractExchange, AbstractMessage
)
from sycommon.logging.kafka_log import SYLogger

logger = SYLogger


class AsyncProperty:
    """实现 await obj.attr 的支持"""

    def __init__(self, method):
        self.method = method

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self.method(obj)


class RabbitMQConnectionPool:
    """单连接单通道RabbitMQ客户端 (严格执行“先清理后连接”策略)"""

    def __init__(
        self,
        hosts: List[str],
        port: int,
        username: str,
        password: str,
        virtualhost: str = "/",
        heartbeat: int = 15,
        app_name: str = "",
        connection_timeout: int = 15,
        reconnect_interval: int = 5,
        prefetch_count: int = 2,
    ):
        self.hosts = [host.strip() for host in hosts if host.strip()]
        if not self.hosts:
            raise ValueError("至少需要提供一个RabbitMQ主机地址")

        self.port = port
        self.username = username
        self.password = password
        self.virtualhost = virtualhost
        self.app_name = app_name or "rabbitmq-client"
        self.heartbeat = heartbeat
        self.connection_timeout = connection_timeout
        self.reconnect_interval = reconnect_interval
        self.prefetch_count = prefetch_count

        self._current_host: str = random.choice(self.hosts)
        logger.info(f"[INIT] 随机选择RabbitMQ主机: {self._current_host}")

        # 核心资源
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[RobustChannel] = None
        self._consumer_channels: Dict[str, RobustChannel] = {}

        # 状态控制
        self._lock = asyncio.Lock()
        self._initialized = False
        self._is_shutdown = False

    @AsyncProperty
    async def is_alive(self) -> bool:
        """对外暴露的连接存活状态"""
        async with self._lock:
            if self._is_shutdown:
                return False
            if not self._initialized:
                return False
            if self._connection is None or self._connection.is_closed:
                return False
            if self._channel is None or self._channel.is_closed:
                return False
            return True

    async def _cleanup_resources(self):
        """
        彻底清理旧资源
        必须在持有 self._lock 的情况下调用
        """
        logger.info("🧹 [CLEANUP] 开始清理旧资源...")

        # 1. 清理所有消费者通道
        if self._consumer_channels:
            channels_to_close = list(self._consumer_channels.values())
            self._consumer_channels.clear()

            for ch in channels_to_close:
                try:
                    if not ch.is_closed:
                        await ch.close()
                except Exception as e:
                    logger.warning(f"⚠️ [CLEANUP_CH] 关闭消费者通道失败: {e}")

        # 2. 关闭主通道
        if self._channel:
            try:
                if not self._channel.is_closed:
                    await self._channel.close()
            except Exception as e:
                logger.warning(f"⚠️ [CLEANUP_MAIN_CH] 关闭主通道失败: {e}")
            finally:
                self._channel = None

        # 3. 关闭连接
        if self._connection:
            try:
                if not self._connection.is_closed:
                    # close() 可能是同步的，也可能是异步的，aio_pika 中通常是异步的
                    await self._connection.close()
            except Exception as e:
                logger.warning(f"⚠️ [CLEANUP_CONN] 关闭连接失败: {e}")
            finally:
                self._connection = None

        logger.info("✅ [CLEANUP] 资源清理完成")

    async def _create_connection_impl(self, host: str) -> AbstractRobustConnection:
        conn_url = (
            f"amqp://{self.username}:{self.password}@{host}:{self.port}/"
            f"{self.virtualhost}?name={self.app_name}&heartbeat={self.heartbeat}"
            f"&reconnect_interval={self.reconnect_interval}&fail_fast=1"
        )
        logger.info(f"🔌 [CONNECT] 尝试连接节点: {host}")
        try:
            conn = await asyncio.wait_for(
                connect_robust(conn_url),
                timeout=self.connection_timeout + 5
            )
            logger.info(f"✅ [CONNECT_OK] 节点连接成功: {host}")
            return conn
        except Exception as e:
            logger.error(f"❌ [CONNECT_FAIL] 节点 {host} 连接失败: {str(e)}")
            raise ConnectionError(f"无法连接RabbitMQ {host}") from e

    async def _ensure_main_channel(self) -> RobustChannel:
        """
        确保主通道有效
        逻辑：
        1. 检查连接状态
        2. 如果断开 -> 清理 -> 轮询重试
        3. 如果连接在但通道断开 -> 仅重建通道
        """
        async with self._lock:
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭")

            # --- 阶段A：连接恢复逻辑 (如果连接断了) ---
            if self._connection is None or self._connection.is_closed:

                # 1. 【强制】先彻底清理所有旧资源
                await self._cleanup_resources()

                retry_hosts = self.hosts.copy()
                random.shuffle(retry_hosts)
                last_error = None
                max_attempts = min(len(retry_hosts), 3)

                # 2. 轮询尝试新连接
                for _ in range(max_attempts):
                    if not retry_hosts:
                        break

                    host = retry_hosts.pop()
                    self._current_host = host
                    temp_conn = None

                    try:
                        temp_conn = await self._create_connection_impl(host)

                        # 3. 只有在连接成功后，才更新 self._connection
                        self._connection = temp_conn
                        temp_conn = None  # 转移所有权
                        self._initialized = True
                        last_error = None
                        logger.info(f"🔗 [RECONNECT_OK] 切换到节点: {host}")
                        break

                    except Exception as e:
                        logger.warning(f"⚠️ [RECONNECT_RETRY] 节点 {host} 不可用")
                        if temp_conn is not None:
                            # 尝试连接失败了，必须把这个“半成品”连接关掉
                            try:
                                await temp_conn.close()
                            except Exception:
                                pass
                        last_error = e
                        await asyncio.sleep(self.reconnect_interval)

                # 4. 如果所有尝试都失败
                if last_error:
                    # 确保状态是干净的
                    self._connection = None
                    self._initialized = False
                    logger.error("💥 [RECONNECT_FATAL] 所有节点重试失败")
                    raise ConnectionError("所有 RabbitMQ 节点连接失败") from last_error

            # --- 阶段B：通道恢复逻辑 (如果连接在但通道断了) ---
            # 注意：这里不需要清理连接，只重置通道
            if self._channel is None or self._channel.is_closed:
                try:
                    self._channel = await self._connection.channel()
                    await self._channel.set_qos(prefetch_count=self.prefetch_count)
                    logger.info(f"✅ [CHANNEL_OK] 主通道已恢复")
                except Exception as e:
                    # 如果连通道都创建不了，说明这个连接也是坏的，回滚到阶段A
                    logger.error(f"❌ [CHANNEL_FAIL] 通道创建失败，标记连接无效: {e}")
                    # 强制清理连接，触发下一次进入阶段A
                    await self._cleanup_resources()
                    raise

            return self._channel

    async def init_pools(self):
        """初始化入口"""
        async with self._lock:
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭")
            if self._initialized:
                return

        # 在 try 之前声明变量，确保 except 块能访问
        conn_created_in_this_try = None

        try:
            # 锁外创建连接，减少锁持有时间
            init_host = random.choice(self.hosts)
            conn = await self._create_connection_impl(init_host)

            # 记录本次创建的连接
            conn_created_in_this_try = conn

            async with self._lock:
                if self._is_shutdown:
                    raise RuntimeError("客户端已关闭")

                # 提交新资源
                self._connection = conn
                self._channel = await self._connection.channel()
                await self._channel.set_qos(prefetch_count=self.prefetch_count)
                self._initialized = True

                # 所有权转移成功，清空临时引用，防止 finally 重复关闭
                conn_created_in_this_try = None

                logger.info(f"🚀 [INIT_OK] 连接池初始化完成: {init_host}")

        except Exception as e:
            logger.error(f"💥 [INIT_FAIL] 初始化异常: {str(e)}")

            # 这里现在可以合法访问 conn_created_in_this_try
            if conn_created_in_this_try is not None:
                try:
                    await conn_created_in_this_try.close()
                except Exception:
                    pass

            if not self._is_shutdown:
                await self.close()
            raise

    async def force_reconnect(self):
        """
        强制重连
        严格执行：清理所有资源 -> 尝试建立新资源
        """
        async with self._lock:
            if self._is_shutdown:
                return

            logger.warning("🔄 [FORCE_RECONNECT] 开始强制重连...")

            # 1. 【关键】标记未初始化，迫使 _ensure_main_channel 走清理流程
            self._initialized = False

            # 2. 【关键】立即清理旧资源 (在锁内)
            await self._cleanup_resources()

            # 此时 self._connection 和 self._channel 均为 None

        # 3. 锁外触发恢复 (避免阻塞锁太久)
        try:
            await self.acquire_channel()
            logger.info("✅ [FORCE_RECONNECT_OK] 强制重连成功")
        except Exception as e:
            logger.error(f"❌ [FORCE_RECONNECT_FAIL] 强制重连失败: {e}")
            raise

    async def acquire_channel(self) -> Tuple[RobustChannel, AbstractRobustConnection]:
        """获取主通道"""
        if not self._initialized and not self._is_shutdown:
            await self.init_pools()
        return await self._ensure_main_channel(), self._connection

    async def publish_message(self, routing_key: str, message_body: bytes, exchange_name: str = "", **kwargs):
        channel, _ = await self.acquire_channel()
        try:
            exchange = channel.default_exchange if not exchange_name else await channel.get_exchange(exchange_name)
            message = Message(body=message_body, **kwargs)
            await exchange.publish(message, routing_key=routing_key)
        except Exception as e:
            logger.error(f"❌ [PUBLISH_FAIL] 发布失败: {str(e)}")
            raise

    async def consume_queue(self, queue_name: str, callback: Callable[[AbstractMessage], asyncio.Future], auto_ack: bool = False, **kwargs):
        if not self._initialized:
            await self.init_pools()

        # 检查是否已存在
        async with self._lock:
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭")
            if queue_name in self._consumer_channels:
                logger.warning(f"⚠️ [CONSUMER_EXISTS] 队列 {queue_name} 已在消费中")
                return
            if not self._connection or self._connection.is_closed:
                raise RuntimeError("连接不可用，无法启动消费")

        # 声明队列 (使用主通道)
        await self.declare_queue(queue_name, **kwargs)

        try:
            # 获取最新连接
            _, conn = await self.acquire_channel()

            # 创建消费者通道
            consumer_channel = await conn.channel()
            await consumer_channel.set_qos(prefetch_count=self.prefetch_count)

            async with self._lock:
                # 再次检查，防止并发创建
                if self._is_shutdown:
                    await consumer_channel.close()
                    return
                if queue_name in self._consumer_channels:
                    await consumer_channel.close()  # 其他协程已经创建了
                    return

                self._consumer_channels[queue_name] = consumer_channel

            async def consume_callback_wrapper(message: AbstractMessage):
                try:
                    await callback(message)
                    if not auto_ack:
                        await message.ack()
                except Exception as e:
                    logger.error(f"❌ [CALLBACK_ERR] {queue_name}: {e}")
                    if not auto_ack:
                        await message.nack(requeue=True)

            await consumer_channel.basic_consume(
                queue_name, consumer_callback=consume_callback_wrapper, auto_ack=auto_ack
            )
            logger.info(f"🎧 [CONSUME_START] {queue_name}")

        except Exception as e:
            logger.error(f"💥 [CONSUME_ERR] {queue_name}: {e}")
            # 失败时清理字典
            async with self._lock:
                if queue_name in self._consumer_channels:
                    # 注意：这里清理的是字典里的引用，通道本身应该在 try 块里被关闭了吗？
                    # 如果 consumer_channel 创建成功但 basic_consume 失败，需要手动关闭
                    ch = self._consumer_channels.pop(queue_name, None)
                    if ch:
                        try:
                            await ch.close()
                        except:
                            pass
            raise

    async def close(self):
        """资源销毁"""
        async with self._lock:
            if self._is_shutdown:
                return
            self._is_shutdown = True
            self._initialized = False

        logger.info("🛑 [CLOSE] 开始关闭连接池...")

        # 1. 清理所有资源
        await self._cleanup_resources()

        logger.info("🏁 [CLOSE] 连接池已关闭")

    async def declare_queue(self, queue_name: str, **kwargs) -> AbstractQueue:
        channel, _ = await self.acquire_channel()
        return await channel.declare_queue(queue_name, **kwargs)

    async def declare_exchange(self, exchange_name: str, exchange_type: str = "direct", **kwargs) -> AbstractExchange:
        channel, _ = await self.acquire_channel()
        return await channel.declare_exchange(exchange_name, exchange_type, **kwargs)
