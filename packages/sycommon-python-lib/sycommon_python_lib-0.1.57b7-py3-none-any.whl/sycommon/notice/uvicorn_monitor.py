from datetime import datetime
import sys
import traceback
import aiohttp
import asyncio
import json
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sycommon.config.Config import Config
from sycommon.logging.kafka_log import SYLogger


async def send_wechat_markdown_msg(
    content: str,
    webhook: str = None
) -> Optional[dict]:
    """
    异步发送企业微信Markdown格式的WebHook消息

    Args:
        content: Markdown格式的消息内容（支持企业微信支持的markdown语法）
        webhook: 完整的企业微信WebHook URL（默认值包含key）

    Returns:
        接口返回的JSON数据（dict），失败返回None
    """
    # 设置请求头
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }

    # 构造请求体（Markdown格式）
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=webhook,
                data=json.dumps(payload, ensure_ascii=False),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                status = response.status
                response_text = await response.text()
                response_data = json.loads(
                    response_text) if response_text else {}

                if status == 200 and response_data.get("errcode") == 0:
                    SYLogger.info(f"消息发送成功: {response_data}")
                    return response_data
                else:
                    SYLogger.info(
                        f"消息发送失败 - 状态码: {status}, 响应: {response_data}")
                    return None
    except Exception as e:
        SYLogger.info(f"错误：未知异常 - {str(e)}")
        return None


async def send_webhook(error_info: dict = None, webhook: str = None):
    """
    发送服务启动结果的企业微信通知
    Args:
        error_info: 错误信息字典（启动失败时必填），包含：error_type, error_msg, stack_trace, elapsed_time
        webhook: 完整的企业微信WebHook URL（覆盖默认值）
    """
    # 获取服务名和环境（兼容配置读取失败）
    try:
        service_name = Config().config.get('Name', "未知服务")
        env = Config().config.get('Nacos', {}).get('namespaceId', '未知环境')
        webHook = Config().config.get('llm', {}).get('WebHook', '未知环境')
    except Exception as e:
        service_name = "未知服务"
        env = "未知环境"
        webHook = None
        SYLogger.info(f"读取配置失败: {str(e)}")

    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 启动失败的通知内容（包含详细错误信息）
    error_type = error_info.get("error_type", "未知错误")
    error_msg = error_info.get("error_msg", "无错误信息")
    stack_trace = error_info.get("stack_trace", "无堆栈信息")[:500]  # 限制长度避免超限
    elapsed_time = error_info.get("elapsed_time", 0)

    markdown_content = f"""### {service_name}服务启动失败告警 ⚠️
> 环境: <font color="warning">{env}</font>
> 启动时间: <font color="comment">{start_time}</font>
> 耗时: <font color="comment">{elapsed_time:.2f}秒</font>
> 错误类型: <font color="danger">{error_type}</font>
> 错误信息: <font color="danger">{error_msg}</font>
> 错误堆栈: {stack_trace}"""

    if webhook or webHook:
        result = await send_wechat_markdown_msg(
            content=markdown_content,
            webhook=webhook or webHook
        )
        SYLogger.info(f"通知发送结果: {result}")
    else:
        SYLogger.info("未设置企业微信WebHook")


def run(*args, webhook: str = None, **kwargs):
    """
    带企业微信告警的Uvicorn启动监控
    调用方式1（默认配置）：uvicorn_monitor.run("app:app", **app.state.config)
    调用方式2（自定义webhook）：uvicorn_monitor.run("app:app", webhook="完整URL", **app.state.config)

    Args:
        *args: 传递给uvicorn.run的位置参数（如"app:app"）
        webhook: 完整的企业微信WebHook URL（可选，覆盖默认值）
        **kwargs: 传递给uvicorn.run的关键字参数（如app.state.config）
    """
    # 判断环境
    env = Config().config.get('Nacos', {}).get('namespaceId', '未知环境')
    if env == "prod":
        import uvicorn
        uvicorn.run(*args, **kwargs)
        return

    # 记录启动开始时间
    start_time = datetime.now()

    if webhook:
        # 脱敏展示webhook（隐藏key的后半部分）
        parsed = urlparse(webhook)
        query = parse_qs(parsed.query)
        if 'key' in query and query['key'][0]:
            key = query['key'][0]
            masked_key = key[:8] + "****" if len(key) > 8 else key + "****"
            query['key'] = [masked_key]
            masked_query = urlencode(query, doseq=True)
            masked_webhook = urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, masked_query, parsed.fragment))
            SYLogger.info(f"自定义企业微信WebHook: {masked_webhook}")

    # 初始化错误信息
    error_info = None

    try:
        import uvicorn
        # 执行启动（如果启动成功，此方法会阻塞，不会执行后续except）
        uvicorn.run(*args, **kwargs)

    except KeyboardInterrupt:
        # 处理用户手动中断（不算启动失败）
        elapsed = (datetime.now() - start_time).total_seconds()
        SYLogger.info(f"\n{'='*50}")
        SYLogger.info(f"ℹ️  应用被用户手动中断")
        SYLogger.info(f"启动耗时: {elapsed:.2f} 秒")
        SYLogger.info(f"{'='*50}\n")
        sys.exit(0)

    except Exception as e:
        # 捕获启动失败异常，收集错误信息
        elapsed = (datetime.now() - start_time).total_seconds()
        # 捕获堆栈信息
        stack_trace = traceback.format_exc()

        # 构造错误信息字典
        error_info = {
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "stack_trace": stack_trace,
            "elapsed_time": elapsed
        }

        # 打印错误信息
        SYLogger.info(f"\n{'='*50}")
        SYLogger.info(f"🚨 应用启动失败！")
        SYLogger.info(f"失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        SYLogger.info(f"错误类型: {type(e).__name__}")
        SYLogger.info(f"错误信息: {str(e)}")
        SYLogger.info(f"\n📝 错误堆栈（关键）:")
        SYLogger.info(f"-"*50)
        traceback.print_exc(file=sys.stdout)
        SYLogger.info(f"\n⏱️  启动耗时: {elapsed:.2f} 秒")
        SYLogger.info(f"{'='*50}\n")

    finally:
        # 运行异步通知函数，传递自定义的webhook参数
        try:
            asyncio.run(send_webhook(
                error_info=error_info,
                webhook=webhook
            ))
        except Exception as e:
            SYLogger.info(f"错误：异步通知失败 - {str(e)}")
        # 启动失败时退出程序
        sys.exit(1)


# 兼容旧调用方式（可选）
run_uvicorn_with_monitor = run
