import os
from typing import Tuple, List, Optional, Any, Dict
from langfuse import Langfuse, get_client
from sycommon.config.Config import Config, SingletonMeta
from sycommon.logging.kafka_log import SYLogger
from langfuse.langchain import CallbackHandler
from sycommon.tools.env import get_env_var
from sycommon.tools.merge_headers import get_header_value


class LangfuseInitializer(metaclass=SingletonMeta):
    """
    Langfuse 初始化管理器
    """

    def __init__(self):
        self._langfuse_client: Optional[Langfuse] = None
        self._base_callbacks: List[Any] = []

        # 执行初始化
        self._initialize()

    def _initialize(self):
        """执行实际的配置读取和组件创建"""
        try:
            config_dict = Config().config

            server_name = config_dict.get('Name', '')
            langfuse_configs = config_dict.get('LangfuseConfig', [])
            environment = config_dict.get('Nacos', {}).get('namespaceId', '')

            # 3. 查找匹配的配置项
            target_config = next(
                (item for item in langfuse_configs if item.get(
                    'name') == server_name), None
            )

            # 4. 如果启用且配置存在，初始化 Langfuse
            if target_config and target_config.get('enable', False):
                # 设置环境变量
                os.environ["LANGFUSE_SECRET_KEY"] = target_config.get(
                    'secretKey', '')
                os.environ["LANGFUSE_PUBLIC_KEY"] = target_config.get(
                    'publicKey', '')
                os.environ["LANGFUSE_BASE_URL"] = target_config.get(
                    'baseUrl', '')
                os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = environment
                os.environ["OTEL_SERVICE_NAME"] = server_name

                self._langfuse_client = get_client()

                langfuse_handler = CallbackHandler()
                self._base_callbacks.append(langfuse_handler)

                SYLogger.info(f"Langfuse 初始化成功 [Service: {server_name}]")
            else:
                SYLogger.info(f"Langfuse 未启用或未找到匹配配置 [Service: {server_name}]")

        except Exception as e:
            SYLogger.error(f"Langfuse 初始化异常: {str(e)}", exc_info=True)

    @property
    def callbacks(self) -> List[Any]:
        """获取回调列表"""
        return self._base_callbacks

    @property
    def metadata(self) -> Dict[str, Any]:
        """动态生成包含 langfuse_session_id 和 langfuse_user_id 的 metadata"""
        trace_id = SYLogger.get_trace_id()
        userid = get_header_value(
            SYLogger.get_headers(), "x-userid-header")
        syVersion = get_header_value(
            SYLogger.get_headers(), "s-y-version")
        user_id = userid or syVersion or get_env_var('VERSION')
        metadata_config = {
            "langfuse_session_id": trace_id,
            "langfuse_user_id": user_id,
        }

        return metadata_config

    @property
    def client(self) -> Optional[Langfuse]:
        """获取 Langfuse 原生客户端实例"""
        return self._langfuse_client

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "callbacks": self.callbacks,
            "metadata": self.metadata,
        }

    def get_components(self) -> Tuple[List[Any], Optional[Langfuse]]:
        """获取 Langfuse 组件"""
        return list(self._base_callbacks), self._langfuse_client

    @staticmethod
    def get() -> Tuple[List[Any], Optional[Langfuse]]:
        """一句话获取组件"""
        initializer = LangfuseInitializer()
        return initializer.get_components()
