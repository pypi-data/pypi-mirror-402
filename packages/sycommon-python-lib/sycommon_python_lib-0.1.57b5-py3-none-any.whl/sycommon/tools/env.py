import os


def _normalize_env_key(key: str) -> str:
    """
    环境变量名标准化：
    1. 转小写
    2. 中划线(-)和下划线(_)统一替换为下划线(_)
    :param key: 原始环境变量名
    :return: 标准化后的key
    """
    return key.lower().replace('-', '_')


def check_env_flag(target_keys: list, default: str = 'false') -> bool:
    """
    检查环境变量是否为"true"（自动兼容：大小写、中划线/下划线）
    :param target_keys: 目标变量名列表（如 ['REGISTER-NACOS']，无需传双key）
    :param default: 默认值（未找到变量时使用）
    :return: 布尔值
    """
    # 1. 标准化目标key（小写+统一下划线）
    target_keys_normalized = [_normalize_env_key(k) for k in target_keys]

    # 2. 遍历所有环境变量，标准化后匹配
    for env_key, env_val in os.environ.items():
        env_key_normalized = _normalize_env_key(env_key)
        if env_key_normalized in target_keys_normalized:
            # 3. 值去空格 + 转小写 判断
            return env_val.strip().lower() == 'true'

    # 4. 未找到变量时，判断默认值
    return default.strip().lower() == 'true'


def get_env_var(key: str, default='', case_insensitive: bool = True) -> str:
    """
    获取环境变量值（自动兼容：大小写、中划线/下划线）
    :param key: 目标环境变量名（如 'REGISTER-NACOS'/'version'）
    :param default: 无匹配时的默认值，默认空字符串
    :param case_insensitive: 是否忽略变量名大小写（默认True，建议保持）
    :return: 匹配到的环境变量值 / 默认值
    """
    if case_insensitive:
        # 标准化目标key（小写+统一下划线）
        target_key_normalized = _normalize_env_key(key)

        # 遍历环境变量，标准化后匹配
        for env_key, env_val in os.environ.items():
            env_key_normalized = _normalize_env_key(env_key)
            if env_key_normalized == target_key_normalized:
                return env_val
        return default
    else:
        # 不忽略大小写时，仅自动兼容中划线/下划线
        target_key_1 = key  # 原始key
        target_key_2 = key.replace(
            '-', '_') if '-' in key else key.replace('_', '-')  # 替换格式的key
        val = os.getenv(target_key_1)
        if val is not None:
            return val
        return os.getenv(target_key_2, default)
