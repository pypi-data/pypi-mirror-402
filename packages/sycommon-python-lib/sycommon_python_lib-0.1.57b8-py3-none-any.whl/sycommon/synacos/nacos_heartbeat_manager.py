import threading
import time
from sycommon.logging.kafka_log import SYLogger
from sycommon.synacos.nacos_client_base import NacosClientBase
from sycommon.synacos.nacos_service_registration import NacosServiceRegistration


class NacosHeartbeatManager:
    """Nacos心跳管理类 - 负责心跳发送和监控"""

    def __init__(self, client_base: NacosClientBase, registration: NacosServiceRegistration, heartbeat_interval: int = 15):
        self.client_base = client_base
        self.registration = registration

        # 心跳配置
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = 15
        self.max_heartbeat_timeout = self.client_base.nacos_config.get(
            'maxHeartbeatTimeout', 30)

        # 状态管理
        self._heartbeat_lock = threading.Lock()
        self._heartbeat_thread = None
        self._last_heartbeat_time = 0
        self._heartbeat_fail_count = 0

    def start_heartbeat(self):
        """启动心跳线程（确保单例）"""
        with self._heartbeat_lock:
            if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
                return

            self._heartbeat_thread = None

            self._heartbeat_thread = threading.Thread(
                target=self._send_heartbeat_loop,
                name="NacosHeartbeatThread",
                daemon=True
            )
            self._heartbeat_thread.start()
            SYLogger.info(
                f"nacos:心跳线程启动，线程ID: {self._heartbeat_thread.ident}，"
                f"心跳间隔: {self.heartbeat_interval}秒，"
                f"心跳超时: {self.heartbeat_timeout}秒"
            )

    def _send_heartbeat_loop(self):
        """心跳发送循环"""
        current_thread = threading.current_thread()
        thread_ident = current_thread.ident
        SYLogger.info(
            f"nacos:心跳循环启动 - 线程ID: {thread_ident}, "
            f"配置间隔: {self.heartbeat_interval}秒, "
            f"超时时间: {self.heartbeat_timeout}秒"
        )

        consecutive_fail = 0

        while not self.client_base._shutdown_event.is_set():
            current_time = time.time()

            try:
                registered_status = self.registration.registered

                if not registered_status:
                    SYLogger.warning(
                        f"nacos:服务未注册，跳过心跳 - 线程ID: {thread_ident}")
                    consecutive_fail = 0
                else:
                    success = self.send_heartbeat()
                    if success:
                        consecutive_fail = 0
                        SYLogger.info(
                            f"nacos:心跳发送成功 - 时间: {current_time:.3f}, "
                            f"间隔: {self.heartbeat_interval}秒"
                        )
                    else:
                        consecutive_fail += 1
                        SYLogger.warning(
                            f"nacos:心跳发送失败 - 连续失败: {consecutive_fail}次"
                        )
                        if consecutive_fail >= 5:
                            SYLogger.error("nacos:心跳连续失败5次，尝试重连")
                            self.client_base.reconnect_nacos_client()
                            consecutive_fail = 0

            except Exception as e:
                consecutive_fail += 1
                SYLogger.error(
                    f"nacos:心跳异常: {str(e)}, 连续失败: {consecutive_fail}次")

            self.client_base._shutdown_event.wait(self.heartbeat_interval)

        SYLogger.info(f"nacos:心跳循环已停止 - 线程ID: {thread_ident}")

    def send_heartbeat(self) -> bool:
        """发送心跳并添加超时控制"""
        if not self.client_base.ensure_client_connected():
            SYLogger.warning("nacos:客户端未连接，心跳发送失败")
            return False

        result_list = []

        def heartbeat_task():
            try:
                result = self._send_heartbeat_internal()
                result_list.append(result)
            except Exception as e:
                SYLogger.error(f"nacos:心跳任务执行异常: {e}")
                result_list.append(False)

        task_thread = threading.Thread(
            target=heartbeat_task,
            daemon=True,
            name="NacosHeartbeatTaskThread"
        )
        task_thread.start()
        task_thread.join(timeout=self.heartbeat_timeout)

        if not result_list:
            SYLogger.error(f"nacos:心跳发送超时（{self.heartbeat_timeout}秒）")
            self.client_base._client_initialized = False
            return False

        return result_list[0]

    def _send_heartbeat_internal(self) -> bool:
        """实际的心跳发送逻辑"""
        result = self.client_base.nacos_client.send_heartbeat(
            service_name=self.registration.service_name,
            ip=self.registration.real_ip,
            port=int(self.registration.port),
            cluster_name="DEFAULT",
            weight=1.0,
            metadata={
                "version": self.registration.version} if self.registration.version else None
        )

        if result and isinstance(result, dict) and result.get('lightBeatEnabled', False):
            SYLogger.info(f"nacos:心跳发送成功，Nacos返回: {result}")
            return True
        else:
            SYLogger.warning(f"nacos:心跳发送失败，Nacos返回: {result}")
            return False
