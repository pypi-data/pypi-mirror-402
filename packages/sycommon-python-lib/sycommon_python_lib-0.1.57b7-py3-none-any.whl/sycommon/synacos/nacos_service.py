import threading
import socket
import signal
import sys
import os
import time
from typing import Callable, Dict, List, Optional
from sycommon.config.Config import Config, SingletonMeta
from sycommon.logging.kafka_log import SYLogger

from sycommon.synacos.nacos_client_base import NacosClientBase
from sycommon.synacos.nacos_service_registration import NacosServiceRegistration
from sycommon.synacos.nacos_heartbeat_manager import NacosHeartbeatManager
from sycommon.synacos.nacos_config_manager import NacosConfigManager
from sycommon.synacos.nacos_service_discovery import NacosServiceDiscovery
from sycommon.tools.env import check_env_flag, get_env_var


class NacosService(metaclass=SingletonMeta):
    def __init__(self, config):
        if config:
            self.config = config
            self.nacos_config = config['Nacos']
            self.service_name = config['Name']
            self.host = config['Host']
            self.port = config['Port']
            self.version = get_env_var('VERSION')
            self.enable_register_nacos = check_env_flag(
                ['REGISTER-NACOS'], 'true')

            # 初始化基础模块
            self.client_base = NacosClientBase(
                self.nacos_config, self.enable_register_nacos)

            # 获取真实IP
            self.real_ip = self.get_service_ip(self.host)

            # 初始化各功能模块
            self.registration = NacosServiceRegistration(
                self.client_base, self.service_name, self.real_ip, self.port, self.version
            )
            self.config_manager = NacosConfigManager(self.client_base)
            self.discovery = NacosServiceDiscovery(self.client_base)

            # 心跳间隔配置
            self.heartbeat_interval = self.nacos_config.get(
                'heartbeatInterval', 15)
            self.heartbeat_manager = NacosHeartbeatManager(
                self.client_base, self.registration, self.heartbeat_interval
            )

            if self.enable_register_nacos:
                # 初始化客户端
                self.client_base._initialize_client()
                # 清理残留实例
                self.registration._cleanup_stale_instance()
            else:
                SYLogger.info("nacos:本地开发模式，不初始化Nacos客户端")

            # 读取配置并设置到全局配置
            self.share_configs = self.config_manager.read_configs(
                self.nacos_config.get('sharedConfigs', []))
            Config().set_attr(self.share_configs)

            # 启动配置监视线程
            self.config_manager.start_watch_configs()

            # 仅在需要注册时启动心跳
            if self.enable_register_nacos:
                self.heartbeat_manager.start_heartbeat()
            else:
                SYLogger.info("nacos:本地开发模式，不启动心跳和监控线程")

    @staticmethod
    def setup_nacos(config: dict):
        """创建并初始化Nacos管理器（保持原有接口）"""
        instance = NacosService(config)

        if instance.enable_register_nacos:
            # 启动注册线程
            timeout = 60
            start_time = time.time()

            register_thread = threading.Thread(
                target=instance.registration.register_with_retry,
                daemon=True,
                name="NacosRegisterThread"
            )
            register_thread.start()

            # 等待注册完成或超时
            while True:
                if instance.registration.registered:
                    break

                if time.time() - start_time >= timeout:
                    break

                time.sleep(1)

            # 最终状态检查
            if not instance.registration.registered:
                try:
                    instance.registration.deregister_service()
                except Exception as e:
                    SYLogger.error(f"nacos:服务注册失败后，注销服务时发生错误: {e}")
                raise RuntimeError("nacos:服务注册失败，应用启动终止")

            # 注册信号处理
            signal.signal(signal.SIGTERM, instance.handle_signal)
            signal.signal(signal.SIGINT, instance.handle_signal)

            # 启动连接监控线程
            threading.Thread(target=instance.discovery.monitor_connection,
                             args=(instance.registration,),
                             daemon=True,
                             name="NacosConnectionMonitorThread").start()
        else:
            SYLogger.info("nacos:本地开发模式，跳过服务注册流程")

        return instance

    def get_service_ip(self, config_ip):
        """获取服务实际IP地址（保持原有逻辑）"""
        if config_ip in ['127.0.0.1', '0.0.0.0']:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(('8.8.8.8', 80))
                    return s.getsockname()[0]
            except Exception:
                return '127.0.0.1'
        return config_ip

    def handle_signal(self, signum, frame):
        """处理退出信号（保持原有逻辑）"""
        SYLogger.info(f"nacos:收到信号 {signum}，正在关闭服务...")
        self.registration.deregister_service()
        sys.exit(0)

    # 以下为兼容原有接口的封装方法
    def add_config_listener(self, data_id: str, callback: Callable[[str], None]):
        return self.config_manager.add_config_listener(data_id, callback)

    def get_config(self, data_id: str, group: str = "DEFAULT_GROUP") -> Optional[str]:
        return self.config_manager.get_config(data_id, group)

    def discover_services(self, service_name: str, group: str = "DEFAULT_GROUP", version: str = None) -> List[Dict]:
        return self.discovery.discover_services(service_name, group, version)

    def get_service_instances(self, service_name: str, group: str = "DEFAULT_GROUP", target_version: str = None) -> List[Dict]:
        return self.discovery.get_service_instances(service_name, group, target_version)
