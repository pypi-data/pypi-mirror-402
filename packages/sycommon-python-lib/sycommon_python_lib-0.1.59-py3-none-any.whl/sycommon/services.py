import asyncio
import logging
import yaml
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, applications
from pydantic import BaseModel
from typing import Any, Callable, Dict, List, Tuple, Union, Optional, AsyncGenerator
from sycommon.config.Config import SingletonMeta
from sycommon.logging.logger_levels import setup_logger_levels
from sycommon.models.mqlistener_config import RabbitMQListenerConfig
from sycommon.models.mqsend_config import RabbitMQSendConfig
from sycommon.rabbitmq.rabbitmq_service import RabbitMQService
from sycommon.tools.docs import custom_redoc_html, custom_swagger_ui_html
from sycommon.sentry.sy_sentry import sy_sentry_init


class Services(metaclass=SingletonMeta):
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _config: Optional[dict] = None
    _initialized: bool = False
    _instance: Optional['Services'] = None
    _app: Optional[FastAPI] = None
    _user_lifespan: Optional[Callable] = None
    _shutdown_lock: asyncio.Lock = asyncio.Lock()

    def __init__(self, config: dict, app: FastAPI):
        super().__init__()
        if not Services._config:
            Services._config = config
        Services._instance = self
        Services._app = app

        # 在实例初始化时定义变量，防止类变量污染
        self._pending_async_db_setup: List[Tuple[Callable, str]] = []

        self._init_event_loop()

    def _init_event_loop(self):
        """初始化事件循环"""
        if not Services._loop:
            try:
                Services._loop = asyncio.get_running_loop()
            except RuntimeError:
                Services._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(Services._loop)

    @classmethod
    def plugins(
        cls,
        app: FastAPI,
        config: Optional[dict] = None,
        middleware: Optional[Callable[[FastAPI, dict], None]] = None,
        nacos_service: Optional[Callable[[dict], None]] = None,
        logging_service: Optional[Callable[[dict], None]] = None,
        database_service: Optional[Union[
            Tuple[Callable, str],
            List[Tuple[Callable, str]]
        ]] = None,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None
    ) -> FastAPI:
        load_dotenv()
        setup_logger_levels()
        cls._app = app
        cls._config = config
        # 保存原始的用户 lifespan
        cls._user_lifespan = app.router.lifespan_context

        applications.get_swagger_ui_html = custom_swagger_ui_html
        applications.get_redoc_html = custom_redoc_html

        if not cls._config:
            try:
                with open('app.yaml', 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                cls._config = config
            except FileNotFoundError:
                logging.warning("未找到 app.yaml，将使用空配置启动")
                cls._config = {}

        app.state.config = {
            "host": cls._config.get('Host', '0.0.0.0'),
            "port": cls._config.get('Port', 8080),
            "workers": cls._config.get('Workers', 1),
            "h11_max_incomplete_event_size": cls._config.get('H11MaxIncompleteEventSize', 1024 * 1024 * 10)
        }

        if middleware:
            middleware(app, cls._config)

        if nacos_service:
            nacos_service(cls._config)

        if logging_service:
            logging_service(cls._config)

        sy_sentry_init()

        @asynccontextmanager
        async def combined_lifespan(app_instance: FastAPI) -> AsyncGenerator[None, None]:
            # 获取 Services 实例
            instance = cls(config, app_instance)

            try:
                # 1. 处理数据库服务
                if database_service:
                    instance._pending_async_db_setup = []

                    items = [database_service] if isinstance(
                        database_service, tuple) else database_service
                    for item in items:
                        db_setup_func, db_name = item
                        if asyncio.iscoroutinefunction(db_setup_func):
                            logging.info(f"注册异步数据库服务: {db_name}")
                            instance._pending_async_db_setup.append(item)
                        else:
                            logging.info(f"执行同步数据库服务: {db_name}")
                            try:
                                db_setup_func(config, db_name)
                            except Exception as e:
                                logging.error(
                                    f"同步数据库服务 {db_name} 初始化失败: {e}", exc_info=True)
                                raise

                # 2. 执行挂起的异步数据库初始化
                if instance._pending_async_db_setup:
                    logging.info("开始执行异步数据库初始化...")
                    for db_setup_func, db_name in instance._pending_async_db_setup:
                        try:
                            await db_setup_func(config, db_name)
                            logging.info(f"异步数据库服务 {db_name} 初始化成功")
                        except Exception as e:
                            logging.error(
                                f"异步数据库服务 {db_name} 初始化失败: {e}", exc_info=True)
                            raise

                # 3. 初始化 MQ
                has_valid_listeners = bool(
                    rabbitmq_listeners and len(rabbitmq_listeners) > 0)
                has_valid_senders = bool(
                    rabbitmq_senders and len(rabbitmq_senders) > 0)

                try:
                    if has_valid_listeners or has_valid_senders:
                        await instance._setup_mq_async(
                            rabbitmq_listeners=rabbitmq_listeners if has_valid_listeners else None,
                            rabbitmq_senders=rabbitmq_senders if has_valid_senders else None,
                            has_listeners=has_valid_listeners,
                            has_senders=has_valid_senders
                        )
                    cls._initialized = True
                    logging.info("Services初始化完成")
                except Exception as e:
                    logging.error(f"MQ初始化失败: {str(e)}", exc_info=True)
                    raise

                app_instance.state.services = instance

                # 4. 执行用户定义的生命周期
                if cls._user_lifespan:
                    async with cls._user_lifespan(app_instance):
                        yield
                else:
                    yield

            except Exception:
                # 如果启动过程中发生任何异常，确保进入 shutdown
                logging.error("启动阶段发生异常，准备执行清理...")
                raise
            finally:
                # 无论成功或失败，都会执行关闭逻辑
                await cls.shutdown()
                logging.info("Services已关闭")

        app.router.lifespan_context = combined_lifespan
        return app

    async def _setup_mq_async(
        self,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None,
        has_listeners: bool = False,
        has_senders: bool = False,
    ):
        """异步设置MQ相关服务"""
        if not (has_listeners or has_senders):
            logging.info("无RabbitMQ监听器/发送器配置，跳过RabbitMQService初始化")
            return

        RabbitMQService.init(self._config, has_listeners, has_senders)

        start_time = asyncio.get_event_loop().time()
        timeout = 30  # 超时时间秒

        # 等待连接池初始化
        while not (RabbitMQService._connection_pool and RabbitMQService._connection_pool._initialized) \
                and not RabbitMQService._is_shutdown:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logging.error("RabbitMQ连接池初始化超时")
                raise TimeoutError(f"RabbitMQ连接池初始化超时（{timeout}秒）")

            logging.debug("等待RabbitMQ连接池初始化...")
            await asyncio.sleep(0.5)

        if RabbitMQService._is_shutdown:
            raise RuntimeError("RabbitMQService 在初始化期间被关闭")

        if has_senders and rabbitmq_senders:
            if has_listeners and rabbitmq_listeners:
                for sender in rabbitmq_senders:
                    for listener in rabbitmq_listeners:
                        if sender.queue_name == listener.queue_name:
                            sender.prefetch_count = listener.prefetch_count
            await self._setup_senders_async(rabbitmq_senders, has_listeners)

        if has_listeners and rabbitmq_listeners:
            await self._setup_listeners_async(rabbitmq_listeners, has_senders)

        if has_listeners:
            listener_count = len(RabbitMQService._consumer_tasks)
            logging.info(f"监听器初始化完成，共启动 {listener_count} 个消费者")
            if listener_count == 0:
                logging.warning("未成功初始化任何监听器，请检查配置或MQ服务状态")

    async def _setup_senders_async(self, rabbitmq_senders, has_listeners: bool):
        """设置发送器"""
        await RabbitMQService.setup_senders(rabbitmq_senders, has_listeners)
        logging.info(f"RabbitMQ发送器注册完成")

    async def _setup_listeners_async(self, rabbitmq_listeners, has_senders: bool):
        """设置监听器"""
        await RabbitMQService.setup_listeners(rabbitmq_listeners, has_senders)

    @classmethod
    async def send_message(
        cls,
        queue_name: str,
        data: Union[str, Dict[str, Any], BaseModel, None],
        max_retries: int = 3,
        retry_delay: float = 1.0, **kwargs
    ) -> None:
        """发送消息"""
        if not cls._initialized or not cls._loop:
            logging.error("Services not properly initialized!")
            raise ValueError("服务未正确初始化")

        if RabbitMQService._is_shutdown:
            logging.error("RabbitMQService已关闭，无法发送消息")
            raise RuntimeError("RabbitMQ服务已关闭")

        for attempt in range(max_retries):
            try:
                # 依赖 RabbitMQService 的内部状态
                sender = await RabbitMQService.get_sender(queue_name)

                if not sender:
                    raise ValueError(
                        f"发送器 '{queue_name}' 不存在或未在 RabbitMQService 中注册")

                await RabbitMQService.send_message(data, queue_name, **kwargs)
                logging.info(f"消息发送成功（尝试 {attempt+1}/{max_retries}）")
                return

            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(
                        f"消息发送失败（已尝试 {max_retries} 次）: {str(e)}", exc_info=True)
                    raise
                logging.warning(
                    f"消息发送失败（尝试 {attempt+1}/{max_retries}）: {str(e)}，{retry_delay}秒后重试...")
                await asyncio.sleep(retry_delay)

    @classmethod
    async def shutdown(cls):
        """关闭所有服务"""
        async with cls._shutdown_lock:
            if RabbitMQService._is_shutdown:
                logging.info("RabbitMQService已关闭，无需重复操作")
                return

            try:
                await RabbitMQService.shutdown()
            except Exception as e:
                logging.error(f"关闭 RabbitMQService 时发生异常: {e}", exc_info=True)

            cls._initialized = False

            # 清理实例数据
            if cls._instance:
                cls._instance._pending_async_db_setup.clear()

            # 这对于热重载（reload）时防止旧实例内存泄漏至关重要
            if cls._app:
                cls._app.state.services = None

            logging.info("所有服务已关闭")
