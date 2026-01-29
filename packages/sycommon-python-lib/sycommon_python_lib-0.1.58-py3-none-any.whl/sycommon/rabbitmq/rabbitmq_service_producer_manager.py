from typing import List, Optional, Union, Dict, Any
import asyncio
import json
import time
from pydantic import BaseModel

from sycommon.logging.kafka_log import SYLogger
from sycommon.models.mqsend_config import RabbitMQSendConfig
from sycommon.config.Config import Config
from sycommon.models.sso_user import SsoUser
from sycommon.models.mqmsg_model import MQMsgModel
from sycommon.rabbitmq.rabbitmq_client import RabbitMQClient
from sycommon.rabbitmq.rabbitmq_service_client_manager import RabbitMQClientManager

logger = SYLogger


class RabbitMQProducerManager(RabbitMQClientManager):
    """
    RabbitMQ生产者管理类 - 负责发送器设置、消息发送
    """
    # 发送器相关状态
    _sender_client_names: List[str] = []

    @classmethod
    async def setup_senders(cls, senders: List[RabbitMQSendConfig], has_listeners: bool = False, **kwargs) -> None:
        """设置消息发送器（适配client_type参数，确保发送器不创建队列）"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法设置发送器")
            return

        cls.set_mode_flags(has_listeners=has_listeners, has_senders=True)
        logger.info(f"开始设置 {len(senders)} 个消息发送器，纯发送器模式: {not has_listeners}")

        for idx, sender_config in enumerate(senders):
            try:
                if not sender_config.queue_name:
                    raise ValueError(f"发送器配置第{idx+1}项缺少queue_name")

                prefetch_count = sender_config.prefetch_count
                queue_name = sender_config.queue_name
                app_name = cls._config.get(
                    "APP_NAME", "") if cls._config else ""

                # 处理发送器客户端名称（非队列名）
                normalized_name = queue_name
                if app_name and normalized_name.endswith(f".{app_name}"):
                    normalized_name = normalized_name[:-len(f".{app_name}")]
                    logger.info(f"发送器客户端名称移除app-name后缀: {normalized_name}")

                # 检查是否已初始化
                if normalized_name in cls._sender_client_names:
                    logger.info(f"发送客户端 '{normalized_name}' 已存在，跳过")
                    continue

                # ===== 处理已有客户端重连 =====
                if normalized_name in cls._clients:
                    client = cls._clients[normalized_name]
                    if not await client.is_connected:
                        client.queue_name = normalized_name
                        client.create_if_not_exists = False
                        await client.connect()
                else:
                    client = await cls.get_client(
                        client_name=normalized_name,
                        client_type="sender",
                        exchange_type=sender_config.exchange_type,
                        durable=sender_config.durable,
                        auto_delete=sender_config.auto_delete,
                        auto_parse_json=sender_config.auto_parse_json,
                        queue_name=queue_name,
                        create_if_not_exists=False,
                        prefetch_count=prefetch_count,
                        **kwargs
                    )

                # 记录客户端
                if normalized_name not in cls._clients:
                    cls._clients[normalized_name] = client
                    logger.info(f"发送客户端 '{normalized_name}' 已添加")

                if normalized_name not in cls._sender_client_names:
                    cls._sender_client_names.append(normalized_name)
                    logger.info(f"发送客户端 '{normalized_name}' 初始化成功（纯发送器模式）")

            except Exception as e:
                logger.error(
                    f"初始化发送客户端第{idx+1}项失败: {str(e)}", exc_info=True)

        logger.info(
            f"消息发送器设置完成，共 {len(cls._sender_client_names)} 个发送器，纯发送器模式: {not has_listeners}")

    @classmethod
    async def get_sender(cls, queue_name: str) -> Optional[RabbitMQClient]:
        """获取发送客户端"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法获取发送器")
            return None

        if not queue_name:
            logger.warning("发送器名称不能为空")
            return None

        # 检查是否在已注册的发送器中
        if queue_name in cls._sender_client_names and queue_name in cls._clients:
            client = cls._clients[queue_name]
            if await client.is_connected:
                return client
            else:
                logger.info(f"发送器 '{queue_name}' 连接已断开，尝试重连")
                try:
                    client.create_if_not_exists = False
                    await client.connect()
                    if await client.is_connected:
                        return client
                except Exception as e:
                    logger.error(f"发送器 '{queue_name}' 重连失败: {str(e)}")
            return None

        # 检查是否带有app-name后缀
        app_name = cls._config.get("APP_NAME", "") if cls._config else ""
        if app_name:
            suffixed_name = f"{queue_name}.{app_name}"
            if suffixed_name in cls._sender_client_names and suffixed_name in cls._clients:
                client = cls._clients[suffixed_name]
                if await client.is_connected:
                    return client
                else:
                    logger.info(f"发送器 '{suffixed_name}' 连接已断开，尝试重连")
                    try:
                        client.create_if_not_exists = False
                        await client.connect()
                        if await client.is_connected:
                            return client
                    except Exception as e:
                        logger.error(f"发送器 '{suffixed_name}' 重连失败: {str(e)}")

        logger.info(f"未找到可用的发送器 '{queue_name}'")
        return None

    @classmethod
    async def send_message(
        cls,
        data: Union[BaseModel, str, Dict[str, Any], None],
        queue_name: str, **kwargs
    ) -> None:
        """发送消息到指定队列"""
        if cls._is_shutdown:
            raise RuntimeError("RabbitMQService已关闭，无法发送消息")

        # 获取发送客户端
        sender = await cls.get_sender(queue_name)
        if not sender:
            error_msg = f"未找到可用的RabbitMQ发送器 (queue_name: {queue_name})"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 确保连接有效
        if not await sender.is_connected:
            logger.info(f"发送器 '{queue_name}' 连接已关闭，尝试重新连接")
            max_retry = 3
            retry_count = 0
            last_exception = None

            while retry_count < max_retry and not cls._is_shutdown:
                try:
                    sender.create_if_not_exists = False
                    await sender.connect()
                    if await sender.is_connected:
                        logger.info(
                            f"发送器 '{queue_name}' 第 {retry_count + 1} 次重连成功")
                        break
                except Exception as e:
                    last_exception = e
                    retry_count += 1
                    logger.warning(
                        f"发送器 '{queue_name}' 第 {retry_count} 次重连失败: {str(e)}")
                    await asyncio.sleep(cls.RECONNECT_INTERVAL)

            if retry_count >= max_retry and not await sender.is_connected:
                error_msg = f"发送器 '{queue_name}' 经过 {max_retry} 次重连仍失败"
                logger.error(f"{error_msg}: {str(last_exception)}")
                raise Exception(error_msg) from last_exception

        try:
            # 处理消息数据
            msg_content = ""
            if isinstance(data, str):
                msg_content = data
            elif isinstance(data, BaseModel):
                msg_content = data.model_dump_json()
            elif isinstance(data, dict):
                msg_content = json.dumps(data, ensure_ascii=False)

            # 创建标准消息模型
            mq_message = MQMsgModel(
                topicCode=queue_name.split('.')[0] if queue_name else "",
                msg=msg_content,
                correlationDataId=kwargs.get(
                    'correlationDataId', logger.get_trace_id()),
                groupId=kwargs.get('groupId', ''),
                dataKey=kwargs.get('dataKey', ""),
                manualFlag=kwargs.get('manualFlag', False),
                traceId=logger.get_trace_id()
            )

            # 构建消息头
            namespaceId = Config().config.get('Nacos', {}).get('namespaceId', '')
            tenant_id = "T000002" if namespaceId == "prod" or namespaceId == "wsuat1" else "T000003"
            mq_header = {
                "context": SsoUser(
                    tenant_id=tenant_id,
                    customer_id="SYSTEM",
                    user_id="SYSTEM",
                    user_name="SYSTEM",
                    request_path="/",
                    req_type="SYSTEM",
                    trace_id=logger.get_trace_id(),
                ).model_dump_json(),
                "tenant_id": logger.get_trace_id(),
                "createTime": str(int(time.time() * 1000)),
            }

            # 发送消息
            await sender.publish(
                message_body=mq_message.model_dump_json(),
                headers=mq_header,
                content_type="application/json"
            )
            logger.info(f"消息发送成功 (队列: {queue_name})")
        except Exception as e:
            logger.error(f"消息发送失败: {str(e)}", exc_info=True)
            raise

    @classmethod
    def clear_senders(cls) -> None:
        """清理发送器状态"""
        cls._sender_client_names.clear()
