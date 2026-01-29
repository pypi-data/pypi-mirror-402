import threading
import time
import atexit
from sycommon.logging.kafka_log import SYLogger
from sycommon.synacos.nacos_client_base import NacosClientBase


class NacosServiceRegistration:
    """Nacos服务注册类 - 负责服务注册、注销和状态验证"""

    def __init__(self, client_base: NacosClientBase, service_name: str, real_ip: str, port: int, version: str):
        self.client_base = client_base
        self.service_name = service_name
        self.real_ip = real_ip
        self.port = port
        self.version = version

        # 注册配置
        self.register_retry_interval = self.client_base.nacos_config.get(
            'registerRetryInterval', 15)
        self.long_term_retry_delay = self.client_base.nacos_config.get(
            'longTermRetryDelay', 30)
        self.max_long_term_retries = self.client_base.nacos_config.get(
            'maxLongTermRetries', -1)

        # 验证配置
        self.registration_verify_count = self.client_base.nacos_config.get(
            'registrationVerifyCount', 1)
        self.registration_verify_interval = self.client_base.nacos_config.get(
            'registrationVerifyInterval', 1)
        self.registration_post_delay = self.client_base.nacos_config.get(
            'registrationPostDelay', 3)

        # 状态管理
        self.registered = False
        self._long_term_retry_count = 0
        self._verify_lock = threading.Lock()
        self._last_verify_time = 0
        self._atexit_registered = False

    def _cleanup_stale_instance(self):
        """清理可能存在的残留实例"""
        if not self.client_base.is_connected:
            return

        try:
            self.client_base.nacos_client.remove_naming_instance(
                service_name=self.service_name,
                ip=self.real_ip,
                port=int(self.port),
                cluster_name="DEFAULT"
            )
            SYLogger.warning(f"nacos:清理残留实例: {self.real_ip}:{self.port}")
        except Exception as e:
            SYLogger.error(f"nacos:清理残留实例异常: {e}")

    def check_service_registered(self) -> bool:
        """检查服务是否已注册（基于实例列表）"""
        if not self.client_base.enable_register_nacos:
            return True

        if not self.client_base.ensure_client_connected():
            return False

        try:
            namespace_id = self.client_base.nacos_config['namespaceId']
            instances = self.client_base.nacos_client.list_naming_instance(
                service_name=self.service_name,
                namespace_id=namespace_id,
                group_name="DEFAULT_GROUP",
                healthy_only=True,
            )

            found = False
            for instance in instances.get('hosts', []):
                if (instance.get('ip') == self.real_ip and
                        instance.get('port') == int(self.port)):
                    SYLogger.info(f"nacos:找到已注册实例: {self.real_ip}:{self.port}")
                    found = True
                    break

            if not found:
                SYLogger.warning(f"nacos:未找到注册实例: {self.real_ip}:{self.port}")

            self.registered = found
            return found
        except Exception as e:
            SYLogger.error(f"nacos:检查服务注册状态失败: {e}")
            return False

    def verify_registration(self) -> bool:
        """多次验证服务是否成功注册（加锁防止重复执行）"""
        if self._verify_lock.locked():
            SYLogger.warning("nacos:注册验证已在执行中，跳过重复调用")
            return self.registered

        with self._verify_lock:
            current_time = time.time()
            if current_time - self._last_verify_time < 15:  # 15秒冷却
                return True

            success_count = 0
            verify_count = self.registration_verify_count
            SYLogger.info(
                f"nacos:开始验证服务注册状态，共验证 {verify_count} 次，间隔 {self.registration_verify_interval} 秒")

            self._last_verify_time = current_time

            for i in range(verify_count):
                if self.check_service_registered():
                    success_count += 1

                if i < verify_count - 1:
                    self.client_base._shutdown_event.wait(
                        self.registration_verify_interval)
                    if self.client_base._shutdown_event.is_set():
                        SYLogger.warning("nacos:应用正在关闭，终止注册验证")
                        break

            pass_threshold = verify_count / 2
            result = success_count >= pass_threshold

            if result:
                SYLogger.info(
                    f"nacos:服务注册验证成功，{success_count}/{verify_count} 次验证通过")
            else:
                SYLogger.error(
                    f"nacos:服务注册验证失败，仅 {success_count}/{verify_count} 次验证通过")

            return result

    def register(self, force: bool = False) -> bool:
        """注册服务到Nacos"""
        if self.registered and not force and self.check_service_registered():
            return True

        if self.registered and not force:
            self.registered = False
            SYLogger.warning("nacos:本地状态显示已注册，但Nacos中未找到服务实例，准备重新注册")

        metadata = {
            "ignore-metrics": "true",
        }
        if self.version:
            metadata["version"] = self.version

        for attempt in range(self.client_base.max_retries):
            if not self.client_base.ensure_client_connected():
                return False

            try:
                self.client_base.nacos_client.add_naming_instance(
                    service_name=self.service_name,
                    ip=self.real_ip,
                    port=int(self.port),
                    metadata=metadata,
                    cluster_name="DEFAULT",
                    healthy=True,
                    ephemeral=True,
                    heartbeat_interval=15  # 心跳间隔默认15秒
                )
                SYLogger.info(
                    f"nacos:服务 {self.service_name} 注册请求已发送: {self.real_ip}:{self.port}")

                if not self._atexit_registered:
                    atexit.register(self.deregister_service)
                    self._atexit_registered = True

                return True
            except Exception as e:
                if "signal only works in main thread" in str(e):
                    return True
                elif attempt < self.client_base.max_retries - 1:
                    SYLogger.warning(
                        f"nacos:服务注册失败 (尝试 {attempt+1}/{self.client_base.max_retries}): {e}")
                    time.sleep(self.client_base.retry_delay)
                else:
                    SYLogger.error(f"nacos:服务注册失败，已达到最大重试次数: {e}")
                    return False

    def register_with_retry(self) -> bool:
        """带重试机制的服务注册（基于实例列表检查）"""
        retry_count = 0
        last_error = None
        self.registered = False
        # 首次注册尝试标记
        first_attempt = True

        while (not self.registered) and (self.max_long_term_retries < 0 or retry_count < self.max_long_term_retries):
            if self.registered:
                return True

            try:
                register_success = self.register(force=True)
                if not register_success:
                    raise RuntimeError("nacos:服务注册请求失败")

                SYLogger.info(
                    f"nacos:服务注册请求已发送，{'首次启动信任注册，跳过阻塞验证' if first_attempt else f'延迟 {self.registration_post_delay} 秒后开始验证'}")

                # 核心逻辑：首次注册跳过阻塞验证，非首次按原逻辑
                if first_attempt:
                    # 首次注册：直接标记成功，不阻塞
                    self.registered = True
                    self.client_base._client_initialized = True
                    self.client_base._shutdown_event.set()
                    self.client_base._shutdown_event.clear()
                    self._long_term_retry_count = 0

                    SYLogger.info(f"nacos:首次启动信任注册成功: {self.service_name}")
                    first_attempt = False  # 标记为非首次
                    return True
                else:
                    # 非首次/重试：保留原有阻塞验证逻辑
                    time.sleep(self.registration_post_delay)
                    registered = self.verify_registration()
                    self.registered = registered

                    if self.registered:
                        self.client_base._client_initialized = True
                        self.client_base._shutdown_event.set()
                        self.client_base._shutdown_event.clear()
                        self._long_term_retry_count = 0

                        SYLogger.info(
                            f"nacos:服务注册成功并通过验证: {self.service_name}")
                        return True
                    else:
                        raise RuntimeError("nacos:服务注册验证失败")

            except Exception as e:
                last_error = str(e)
                retry_count += 1
                first_attempt = False  # 失败后标记为非首次
                delay = min(self.register_retry_interval,
                            self.client_base.max_retry_delay)

                SYLogger.warning(
                    f"nacos:服务注册尝试 {retry_count} 失败: {last_error}，{delay}秒后重试")
                time.sleep(delay)

        if self.registered:
            return True

        if last_error:
            SYLogger.error(f"nacos:服务注册失败，最终错误: {last_error}")
        else:
            SYLogger.error(f"nacos:服务注册失败，已达到最大重试次数: {self.service_name}")

        return False

    def deregister_service(self):
        """从Nacos注销服务"""
        if not self.registered or not self.client_base.is_connected:
            return

        SYLogger.info("nacos:正在注销服务...")
        try:
            self.client_base.nacos_client.remove_naming_instance(
                service_name=self.service_name,
                ip=self.real_ip,
                port=int(self.port),
                cluster_name="DEFAULT"
            )
            self.registered = False
            SYLogger.info(f"nacos:服务 {self.service_name} 已注销")
        except Exception as e:
            SYLogger.error(f"nacos:注销服务时发生错误: {e}")
        finally:
            self.client_base._shutdown_event.set()
