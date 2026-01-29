import json
import threading
import time
from typing import Callable, Optional, Dict, List
from sycommon.synacos.nacos_client_base import NacosClientBase
import yaml
from sycommon.logging.kafka_log import SYLogger


class NacosConfigManager:
    """Nacos配置管理类 - 负责配置读取、监听和更新"""

    def __init__(self, client_base: NacosClientBase):
        self.client_base = client_base

        # 配置
        self.config_watch_interval = self.client_base.nacos_config.get(
            'configWatchInterval', 30)

        # 状态
        self.share_configs: Dict = {}
        self._config_listeners: Dict[str, Callable[[str], None]] = {}
        self._config_cache: Dict[str, str] = {}
        self._watch_thread: Optional[threading.Thread] = None

    def read_configs(self, shared_configs: List[Dict]) -> dict:
        """读取共享配置"""
        configs = {}

        for config in shared_configs:
            data_id = config['dataId']
            group = config['group']

            for attempt in range(self.client_base.max_retries):
                try:
                    if not self.client_base.ensure_client_connected():
                        self.client_base.reconnect_nacos_client()

                    content = self.client_base.nacos_client.get_config(
                        data_id, group)

                    try:
                        configs[data_id] = json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            configs[data_id] = yaml.safe_load(content)
                        except yaml.YAMLError:
                            SYLogger.error(f"nacos:无法解析 {data_id} 的内容")
                    break
                except Exception as e:
                    if attempt < self.client_base.max_retries - 1:
                        SYLogger.warning(
                            f"nacos:读取配置 {data_id} 失败 (尝试 {attempt+1}/{self.client_base.max_retries}): {e}")
                        time.sleep(self.client_base.retry_delay)
                    else:
                        SYLogger.error(
                            f"nacos:读取配置 {data_id} 失败，已达到最大重试次数: {e}")

        self.share_configs = configs
        return configs

    def add_config_listener(self, data_id: str, callback: Callable[[str], None]):
        """添加配置变更监听器"""
        self._config_listeners[data_id] = callback
        if config := self.get_config(data_id):
            callback(config)

    def get_config(self, data_id: str, group: str = "DEFAULT_GROUP") -> Optional[str]:
        """获取配置内容"""
        if not self.client_base.ensure_client_connected():
            return None

        try:
            return self.client_base.nacos_client.get_config(data_id, group=group)
        except Exception as e:
            SYLogger.error(f"nacos:获取配置 {data_id} 失败: {str(e)}")
            return None

    def start_watch_configs(self):
        """启动配置监视线程"""
        self._watch_thread = threading.Thread(
            target=self._watch_configs, daemon=True)
        self._watch_thread.start()

    def _watch_configs(self):
        """配置监听线程"""
        check_interval = self.config_watch_interval

        while not self.client_base._shutdown_event.is_set():
            try:
                for data_id, callback in list(self._config_listeners.items()):
                    new_config = self.get_config(data_id)
                    if new_config and new_config != self._config_cache.get(data_id):
                        callback(new_config)
                        self._config_cache[data_id] = new_config
                        try:
                            self.share_configs[data_id] = json.loads(
                                new_config)
                        except json.JSONDecodeError:
                            try:
                                self.share_configs[data_id] = yaml.safe_load(
                                    new_config)
                            except yaml.YAMLError:
                                SYLogger.error(f"nacos:无法解析 {data_id} 的内容")
            except Exception as e:
                SYLogger.error(f"nacos:配置监视线程异常: {str(e)}")
            self.client_base._shutdown_event.wait(check_interval)
