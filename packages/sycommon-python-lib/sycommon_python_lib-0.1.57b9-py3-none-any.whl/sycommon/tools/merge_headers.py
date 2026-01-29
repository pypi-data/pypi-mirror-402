def merge_headers(
    source_headers,  # 来源headers（支持多种格式：字典/MutableHeaders/键值对列表/元组）
    target_headers,  # 目标headers（原有值需保留，同名覆盖source）
    keep_keys=None,  # 需保留的key集合（None表示保留所有）
    delete_keys={'content-length', 'accept',
                 'content-type', 'sec-fetch-mode',
                 'sec-fetch-dest', 'sec-fetch-site',
                 'pragma', 'cache-control',
                 'accept-encoding', 'priority'},  # 需删除的source key集合
    encoding='utf-8'  # 字符编码（处理bytes转换）
) -> dict:
    """
    合并headers，最终规则：
    1. 所有key统一转为小写进行比较判断（完全大小写无关）
    2. target_headers 同名key 完全覆盖 source_headers（source同名key不生效）
    3. delete_keys 作用于source_headers：source中所有该列表内的key一律不添加（无论是否新增）
    4. target_headers 中的key即使在delete_keys也始终保留，不受删除规则影响
    5. 自动处理bytes/其他类型的键值转换为字符串
    6. 最终输出的key全部为小写
    """
    # 初始化并统一转为小写集合
    keep_keys = {k.lower() for k in keep_keys} if keep_keys else set()
    delete_keys = {k.lower() for k in delete_keys} if delete_keys else set()

    # 修复1：兼容 MutableHeaders/普通字典/None 等 target_headers 类型
    if target_headers is None:
        target_dict = {}
    elif hasattr(target_headers, 'items'):
        # 支持 MutableHeaders/Headers/普通字典（都有items()方法）
        target_dict = dict(target_headers.items())
    else:
        # 兜底：可迭代对象转为字典
        target_dict = dict(target_headers) if isinstance(
            target_headers, (list, tuple)) else {}

    # 标准化target_headers：key转为小写，保留原有值
    processed_headers = {k.lower(): v for k, v in target_dict.items()}
    target_original_keys = set(processed_headers.keys())

    # 修复2：统一处理 source_headers 格式，确保是键值对迭代器
    # 步骤1：将source_headers转为标准的键值对列表
    if source_headers is None:
        source_kv_list = []
    elif hasattr(source_headers, 'items'):
        # 字典/MutableHeaders → 转为键值对列表
        source_kv_list = list(source_headers.items())
    elif isinstance(source_headers, (list, tuple)):
        # 列表/元组 → 校验并过滤合法的键值对（仅保留长度为2的元组/列表）
        source_kv_list = []
        for item in source_headers:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                source_kv_list.append(item)
            else:
                # 跳过非法格式（如长度≠2的元素），避免解包报错
                continue
    else:
        # 其他类型 → 空列表（避免迭代报错）
        source_kv_list = []

    # 处理来源headers的键值转换和合并（遍历标准化后的键值对）
    for key, value in source_kv_list:
        # 转换key为字符串并统一转为小写（判断用）
        if not isinstance(key, str):
            try:
                key = key.decode(encoding, errors='replace') if isinstance(
                    key, bytes) else str(key)
            except Exception:
                # 极端情况：无法转换的key直接跳过
                continue

        key_lower = key.lower()

        # 转换value为字符串
        if not isinstance(value, str):
            try:
                value = value.decode(encoding, errors='replace') if isinstance(
                    value, bytes) else str(value)
            except Exception:
                # 无法转换的value设为空字符串
                value = ""

        # 过滤1：source的key在删除列表 → 直接跳过
        if key_lower in delete_keys:
            continue

        # 过滤2：仅保留指定的key（如果设置了keep_keys）
        if keep_keys and key_lower not in keep_keys:
            continue

        # 过滤3：target已有同名key → 直接跳过（target值覆盖source）
        if key_lower in target_original_keys:
            continue

        # 仅添加符合条件的key-value（最终key为小写）
        processed_headers[key_lower] = value

    return processed_headers


def get_header_value(headers: list, target_key: str, default=None):
    """
    从列表中查找指定 header 的值

    Args:
        headers: header 列表，例如 [('Content-Type', 'application/json'), ...]
        target_key: 要查找的 key
        default: 如果没找到返回的默认值
    """
    if not headers:
        return default

    for item in headers:
        # 兼容 list 和 tuple，确保长度为2
        if isinstance(item, (list, tuple)) and len(item) == 2 and item[0] == target_key:
            return item[1]

    return default
