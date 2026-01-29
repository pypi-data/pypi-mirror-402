import logging


def setup_logger_levels():
    """配置各模块的日志级别，抑制无关INFO/DEBUG日志"""
    # Nacos 客户端：仅输出WARNING及以上（屏蔽INFO级的心跳/注册日志）
    logging.getLogger("nacos.client").setLevel(logging.WARNING)

    # Kafka Python客户端：屏蔽INFO级的连接/版本检测日志
    logging.getLogger("kafka.conn").setLevel(logging.WARNING)
    logging.getLogger("kafka.producer").setLevel(logging.WARNING)

    # Uvicorn/FastAPI：屏蔽启动/应用初始化的INFO日志（保留ERROR/WARNING）
    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # 屏蔽访问日志
    # logging.getLogger("uvicorn.error").setLevel(logging.ERROR)     # 仅保留错误

    # 自定义的root日志（如同步数据库/监听器初始化）：屏蔽INFO
    logging.getLogger("root").setLevel(logging.WARNING)

    # RabbitMQ相关日志（如果有专属日志器）
    logging.getLogger("pika").setLevel(logging.WARNING)  # 若使用pika客户端
    logging.getLogger("rabbitmq").setLevel(logging.WARNING)
