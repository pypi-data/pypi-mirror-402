import threading
from typing import List, Dict
from sycommon.logging.kafka_log import SYLogger
from sycommon.synacos.nacos_client_base import NacosClientBase
from sycommon.synacos.nacos_service_registration import NacosServiceRegistration


class NacosServiceDiscovery:
    """Nacos服务发现类 - 负责服务实例发现和轮询"""

    def __init__(self, client_base: NacosClientBase):
        self.client_base = client_base

        # 轮询管理
        self._round_robin_index = 0
        self._round_robin_lock = threading.Lock()

        # 连接监控配置
        self.connection_check_interval = self.client_base.nacos_config.get(
            'connectionCheckInterval', 30)
        self._monitor_thread_started = False
        self._monitor_thread_lock = threading.Lock()

    def discover_services(self, service_name: str, group: str = "DEFAULT_GROUP", version: str = None) -> List[Dict]:
        """发现服务实例列表 (与Java格式兼容)"""
        if not self.client_base.ensure_client_connected():
            return []

        return self.get_service_instances(service_name, group, version)

    def get_service_instances(self, service_name: str, group: str = "DEFAULT_GROUP", target_version: str = None) -> List[Dict]:
        """
        获取服务实例列表，并按照以下优先级规则筛选：
        1. 相同版本号的实例
        2. 无版本号的实例
        3. 所有实例中轮询
        """
        try:
            namespace_id = self.client_base.nacos_config['namespaceId']
            instances = self.client_base.nacos_client.list_naming_instance(
                service_name,
                namespace_id=namespace_id,
                group_name=group,
                healthy_only=True,
            )

            if not instances or 'hosts' not in instances:
                SYLogger.info(f"nacos:未发现 {service_name} 的服务实例")
                return []

            all_instances = instances.get('hosts', [])
            all_instances = [
                instance for instance in all_instances
                if instance.get('enabled', True)
            ]
            SYLogger.info(
                f"nacos:共发现 {len(all_instances)} 个 {service_name} 服务实例")

            version_to_use = target_version

            if version_to_use:
                same_version_instances = [
                    instance for instance in all_instances
                    if instance.get('metadata', {}).get('version') == version_to_use
                ]

                if same_version_instances:
                    SYLogger.info(
                        f"nacos:筛选出 {len(same_version_instances)} 个与当前版本({version_to_use})匹配的实例")
                    return same_version_instances

                no_version_instances = [
                    instance for instance in all_instances
                    if 'version' not in instance.get('metadata', {})
                ]

                if no_version_instances:
                    SYLogger.info(
                        f"nacos:未找到相同版本({version_to_use})的实例，筛选出 {len(no_version_instances)} 个无版本号的实例")
                    return no_version_instances
            else:
                no_version_instances = [
                    instance for instance in all_instances
                    if 'version' not in instance.get('metadata', {})
                ]

                if no_version_instances:
                    # 从通用实例中轮询
                    with self._round_robin_lock:
                        selected_index = self._round_robin_index % len(
                            no_version_instances)
                        self._round_robin_index = (
                            selected_index + 1) % len(no_version_instances)

                    SYLogger.info(
                        f"nacos:无版本请求，从 {len(no_version_instances)} 个通用实例中选择")
                    return [no_version_instances[selected_index]]

            SYLogger.info(
                f"nacos:使用轮询方式从 {len(all_instances)} 个实例中选择")

            with self._round_robin_lock:
                selected_index = self._round_robin_index % len(all_instances)
                self._round_robin_index = (
                    selected_index + 1) % len(all_instances)

            return [all_instances[selected_index]]

        except Exception as e:
            SYLogger.error(f"nacos:服务发现失败: {service_name}: {str(e)}")
            return []

    def monitor_connection(self, registration: NacosServiceRegistration):
        """连接监控线程"""
        with self._monitor_thread_lock:
            if self.client_base._shutdown_event.is_set() or self._monitor_thread_started:
                SYLogger.warning("nacos:监控线程已启动/已关闭，拒绝重复启动")
                return
            self._monitor_thread_started = True

        check_interval = self.connection_check_interval
        SYLogger.info(
            f"nacos:连接监控线程启动 - 线程ID: {threading.current_thread().ident}")

        while not self.client_base._shutdown_event.is_set():
            try:
                if not self.client_base.is_connected:
                    SYLogger.warning("nacos:客户端未连接，尝试重新初始化")
                    self.client_base.ensure_client_connected()
                else:
                    current_registered = registration.check_service_registered()

                    if current_registered != registration.registered:
                        registration.registered = current_registered
                        if not current_registered:
                            SYLogger.warning("nacos:服务实例未注册，触发单次重新注册")
                            retry_thread = threading.Thread(
                                target=registration.register,
                                args=(True,),
                                daemon=True,
                                name="NacosSingleRetryThread"
                            )
                            retry_thread.start()
                        else:
                            SYLogger.info("nacos:服务实例已注册，触发单次验证")
                            registration.verify_registration()

                self.client_base._shutdown_event.wait(check_interval)

            except Exception as e:
                SYLogger.error(f"nacos:连接监控异常: {str(e)}")
                self.client_base._shutdown_event.wait(5)

        with self._monitor_thread_lock:
            self._monitor_thread_started = False
        SYLogger.info(
            f"nacos:连接监控线程退出 - 线程ID: {threading.current_thread().ident}")
