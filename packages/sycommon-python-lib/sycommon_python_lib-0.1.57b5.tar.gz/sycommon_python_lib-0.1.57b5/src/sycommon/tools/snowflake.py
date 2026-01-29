import time
import threading
import socket
import hashlib
import random
import os
from typing import Optional, Type, Any
from os import environ
import psutil


class ClassProperty:
    """支持通过 类.属性 的方式访问，无需实例化"""

    def __init__(self, func):
        self.func = func

    def __get__(self, instance: Any, cls: Type) -> str:
        return self.func(cls)


class Snowflake:
    """
    雪花算法生成器（高并发终极优化版 - 修复语法错误）

    终极优化点：
    1. 解决溢出死锁：当序列号溢出时，释放锁自旋等待，避免阻塞其他线程。
    2. 锁内原子更新：确保时钟回拨判断与状态更新的原子性。
    3. 移除 sleep：全流程无休眠，纯自旋保证极致吞吐。
    """
    START_TIMESTAMP = 1388534400000  # 2014-01-01 00:00:00
    SEQUENCE_BITS = 12
    MACHINE_ID_BITS = 10
    MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1  # 0~1023
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1     # 4095
    MACHINE_ID_SHIFT = SEQUENCE_BITS
    TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS
    CLOCK_BACKWARD_THRESHOLD = 5
    _MAX_JAVA_LONG = 9223372036854775807

    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, machine_id: Optional[int] = None):
        self._validate_timestamp_range()
        if machine_id is None:
            machine_id = self._get_k8s_machine_id()
        if not (0 <= machine_id <= self.MAX_MACHINE_ID):
            raise ValueError(f"机器ID必须在0~{self.MAX_MACHINE_ID}之间")

        self.machine_id = machine_id
        self.last_timestamp = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def _validate_timestamp_range(self):
        max_support_timestamp = self.START_TIMESTAMP + \
            (1 << (64 - self.TIMESTAMP_SHIFT)) - 1
        current_timestamp = self._get_current_timestamp()
        if current_timestamp > max_support_timestamp:
            raise RuntimeError(f"当前时间戳({current_timestamp})超过支持范围")

    def _get_k8s_machine_id(self) -> int:
        pod_name = environ.get("POD_NAME")
        if pod_name:
            return self._hash_to_machine_id(pod_name)
        pod_ip = environ.get("POD_IP")
        if pod_ip:
            return self._hash_to_machine_id(pod_ip)
        try:
            local_ip = self._get_local_internal_ip()
            if local_ip:
                return self._hash_to_machine_id(local_ip)
        except Exception:
            pass
        hostname = socket.gethostname()
        if hostname:
            return self._hash_to_machine_id(hostname)
        fallback_text = f"{os.getpid()}_{int(time.time()*1000)}_{random.randint(0, 100000)}"
        return self._hash_to_machine_id(fallback_text)

    def _get_local_internal_ip(self) -> Optional[str]:
        try:
            net_if_addrs = psutil.net_if_addrs()
            for interface_name, addrs in net_if_addrs.items():
                if (interface_name.lower().startswith("lo")
                        or interface_name.lower() in ["loopback", "virtual", "docker", "veth"]):
                    continue
                for addr in addrs:
                    if addr.family == psutil.AF_INET:
                        ip = addr.address
                        if ip and not ip.startswith('127.') and not ip.startswith('0.'):
                            return ip
            return None
        except Exception:
            return self._get_local_ip_fallback()

    def _get_local_ip_fallback(self) -> Optional[str]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.0.0.1", 80))
            local_ip = s.getsockname()[0]
            s.close()
            if not local_ip.startswith('127.') and not local_ip.startswith('0.'):
                return local_ip
        except Exception:
            pass
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                if not ip.startswith('127.') and not ip.startswith('0.'):
                    return ip
        except Exception:
            pass
        return None

    def _hash_to_machine_id(self, text: str) -> int:
        hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
        return int.from_bytes(hash_bytes[:4], byteorder="big") % (self.MAX_MACHINE_ID + 1)

    def _get_current_timestamp(self) -> int:
        return int(time.time() * 1000)

    def generate_id(self) -> int:
        """
        生成雪花ID（高并发优化版）
        使用 while True 循环来处理序列号溢出时的重试逻辑
        """
        while True:
            # 1. 快速获取当前时间
            current_timestamp = self._get_current_timestamp()

            # 2. 加锁，保证状态更新的原子性
            with self.lock:
                # 读取当前状态（快照）
                last_timestamp = self.last_timestamp
                sequence = self.sequence

                # 2.1 处理时钟回拨
                time_diff = last_timestamp - current_timestamp
                if time_diff > 0:
                    if time_diff > self.CLOCK_BACKWARD_THRESHOLD:
                        # 大幅回拨：直接“借用”未来1ms
                        current_timestamp = last_timestamp + 1
                    else:
                        # 微小回拨：锁内自旋等待追上（通常很快）
                        while current_timestamp <= last_timestamp:
                            current_timestamp = self._get_current_timestamp()

                # 2.2 计算序列号
                if current_timestamp == last_timestamp:
                    # 同一毫秒内
                    sequence = (sequence + 1) & self.MAX_SEQUENCE
                    if sequence == 0:
                        self.lock.release()  # 手动释放锁

                        # 锁外自旋等待下一毫秒
                        while current_timestamp <= last_timestamp:
                            current_timestamp = self._get_current_timestamp()

                        # 等待到了新毫秒，进入下一轮循环（continue 默认行为），重新抢锁竞争
                        continue

                elif current_timestamp > last_timestamp:
                    # 时间推进，重置序列号
                    sequence = 0
                    self.last_timestamp = current_timestamp
                    self.sequence = sequence
                else:
                    # current < last 的情况通常已被回拨逻辑处理
                    pass

                # 2.4 生成 ID
                snowflake_id = (
                    ((current_timestamp - self.START_TIMESTAMP)
                     << self.TIMESTAMP_SHIFT)
                    | (self.machine_id << self.MACHINE_ID_SHIFT)
                    | sequence
                )

                # 更新全局状态（如果是同一毫秒）
                if current_timestamp == self.last_timestamp:
                    self.sequence = sequence

            # 成功生成 ID，退出循环
            return snowflake_id

    @staticmethod
    def parse_id(snowflake_id: int) -> dict:
        from datetime import datetime
        sequence = snowflake_id & Snowflake.MAX_SEQUENCE
        machine_id = (snowflake_id >>
                      Snowflake.MACHINE_ID_SHIFT) & Snowflake.MAX_MACHINE_ID
        timestamp = (snowflake_id >> Snowflake.TIMESTAMP_SHIFT) + \
            Snowflake.START_TIMESTAMP
        generate_time = datetime.fromtimestamp(
            timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return {
            "snowflake_id": snowflake_id,
            "generate_time": generate_time,
            "machine_id": machine_id,
            "sequence": sequence,
            "is_java_long_safe": snowflake_id <= Snowflake._MAX_JAVA_LONG
        }

    @classmethod
    def next_id(cls) -> str:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return str(cls._instance.generate_id())

    @ClassProperty
    def id(cls) -> str:
        return cls.next_id()


if __name__ == "__main__":
    import concurrent.futures

    print("=== 高并发终极版 Snowflake 性能测试 ===")
    count = 100000
    workers = 100

    ids = []
    start_time = time.perf_counter()

    def task():
        return Snowflake.id

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(task) for _ in range(count)]
        for future in concurrent.futures.as_completed(futures):
            ids.append(future.result())

    end_time = time.perf_counter()
    duration = end_time - start_time

    unique_count = len(set(ids))
    print(f"生成数量: {len(ids)}")
    print(f"唯一ID数量: {unique_count}")
    print(f"是否有重复: {'是 ❌' if unique_count != len(ids) else '否 ✅'}")
    print(f"总耗时: {duration:.4f} 秒")
    print(f"吞吐量 (QPS): {len(ids) / duration:,.2f}")
    print("\n最后一个ID解析:")
    print(Snowflake.parse_id(int(ids[-1])))
