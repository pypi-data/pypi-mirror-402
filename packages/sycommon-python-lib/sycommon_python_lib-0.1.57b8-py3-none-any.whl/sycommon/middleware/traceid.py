import json
import re
from typing import Dict, Any
from fastapi import Request, Response
from sycommon.logging.kafka_log import SYLogger
from sycommon.tools.merge_headers import merge_headers
from sycommon.tools.snowflake import Snowflake


def setup_trace_id_handler(app):
    @app.middleware("http")
    async def trace_id_and_log_middleware(request: Request, call_next):
        # ========== 1. 请求阶段：获取/生成 TraceID ==========
        trace_id = request.headers.get("x-traceid-header")
        if not trace_id:
            trace_id = Snowflake.id

        # 设置 trace_id 到日志上下文
        token = SYLogger.set_trace_id(trace_id)
        header_token = SYLogger.set_headers(request.headers.raw)

        # 获取请求参数
        query_params = dict(request.query_params)
        request_body: Dict[str, Any] = {}
        files_info: Dict[str, str] = {}

        json_content_types = [
            "application/json",
            "text/plain;charset=utf-8",
            "text/plain"
        ]
        content_type = request.headers.get("content-type", "").lower()
        is_json_content = any(ct in content_type for ct in json_content_types)

        if is_json_content and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 兼容纯文本格式的 JSON
                if "text/plain" in content_type:
                    raw_text = await request.text(encoding="utf-8")
                    request_body = json.loads(raw_text)
                else:
                    request_body = await request.json()
            except Exception:
                try:
                    request_body = await request.json()
                except Exception as e:
                    request_body = {"error": f"JSON parse failed: {str(e)}"}

        elif "multipart/form-data" in content_type and request.method in ["POST", "PUT"]:
            try:
                boundary = None
                if "boundary=" in content_type:
                    boundary = content_type.split("boundary=")[1].strip()
                    boundary = boundary.encode('ascii')

                if boundary:
                    body = await request.body()
                    parts = body.split(boundary)
                    for part in parts:
                        part_str = part.decode('utf-8', errors='ignore')
                        filename_match = re.search(
                            r'filename="([^"]+)"', part_str)
                        if filename_match:
                            field_name_match = re.search(
                                r'name="([^"]+)"', part_str)
                            field_name = field_name_match.group(
                                1) if field_name_match else "unknown"
                            filename = filename_match.group(1)
                            files_info[field_name] = filename
            except Exception as e:
                request_body = {
                    "error": f"Failed to process form data: {str(e)}"}

        # 构建请求日志
        request_message = {
            "traceId": trace_id,
            "method": request.method,
            "url": str(request.url),
            "query_params": query_params,
            "request_body": request_body,
            "uploaded_files": files_info if files_info else None
        }
        SYLogger.info(json.dumps(request_message, ensure_ascii=False))

        # 标记位：默认认为会发生异常
        # 这样如果中途代码报错跳转到 except，finally 就不会 reset，保留 trace_id 给 Exception Handler
        had_exception = True

        try:
            # ========== 2. 处理请求 ==========
            response = await call_next(request)

            # ========== 3. 响应处理阶段 ==========
            # 注意：此阶段发生的任何异常都会被下方的 except 捕获
            # 从而保证 trace_id 不被清除，能够透传

            response_content_type = response.headers.get(
                "content-type", "").lower()

            # 处理 SSE (Server-Sent Events)
            if "text/event-stream" in response_content_type:
                try:
                    response.headers["x-traceid-header"] = trace_id
                    expose_headers = response.headers.get(
                        "access-control-expose-headers", "")
                    if expose_headers:
                        if "x-traceid-header" not in expose_headers.lower():
                            response.headers[
                                "access-control-expose-headers"] = f"{expose_headers}, x-traceid-header"
                    else:
                        response.headers["access-control-expose-headers"] = "x-traceid-header"

                    # SSE 必须移除 Content-Length
                    headers_lower = {
                        k.lower(): k for k in response.headers.keys()}
                    if "content-length" in headers_lower:
                        del response.headers[headers_lower["content-length"]]
                except AttributeError:
                    # 流式响应头只读处理
                    new_headers = dict(response.headers) if hasattr(
                        response.headers, 'items') else {}
                    new_headers["x-traceid-header"] = trace_id
                    if "access-control-expose-headers" in new_headers:
                        if "x-traceid-header" not in new_headers["access-control-expose-headers"].lower():
                            new_headers["access-control-expose-headers"] += ", x-traceid-header"
                    else:
                        new_headers["access-control-expose-headers"] = "x-traceid-header"
                    new_headers.pop("content-length", None)
                    response.init_headers(new_headers)

                # SSE 不处理 Body，直接返回
                had_exception = False
                return response

            # 处理非 SSE 响应
            # 备份 CORS 头
            cors_headers = {}
            cors_header_keys = [
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-headers",
                "access-control-expose-headers",
                "access-control-allow-credentials",
                "access-control-max-age"
            ]
            for key in cors_header_keys:
                for k in response.headers.keys():
                    if k.lower() == key:
                        cors_headers[key] = response.headers[k]
                        break

            # 合并 Headers
            merged_headers = merge_headers(
                source_headers=request.headers,
                target_headers=response.headers,
                keep_keys=None,
                delete_keys={'content-length', 'accept', 'content-type'}
            )

            # 强制加入 x-traceid-header
            merged_headers["x-traceid-header"] = trace_id
            merged_headers.update(cors_headers)

            # 更新暴露头
            expose_headers = merged_headers.get(
                "access-control-expose-headers", "")
            if expose_headers:
                if "x-traceid-header" not in expose_headers.lower():
                    merged_headers["access-control-expose-headers"] = f"{expose_headers}, x-traceid-header"
            else:
                merged_headers["access-control-expose-headers"] = "x-traceid-header"

            # 应用 Headers
            if hasattr(response.headers, 'clear'):
                response.headers.clear()
                for k, v in merged_headers.items():
                    response.headers[k] = v
            elif hasattr(response, "init_headers"):
                response.init_headers(merged_headers)
            else:
                for k, v in merged_headers.items():
                    try:
                        response.headers[k] = v
                    except (AttributeError, KeyError):
                        pass

            # 处理响应体
            response_body = b""
            try:
                async for chunk in response.body_iterator:
                    response_body += chunk

                content_disposition = response.headers.get(
                    "content-disposition", "").lower()

                # JSON 响应体注入 traceId
                if "application/json" in response_content_type and not content_disposition.startswith("attachment"):
                    try:
                        data = json.loads(response_body)
                        new_body = response_body
                        if isinstance(data, dict):
                            data["traceId"] = trace_id
                            new_body = json.dumps(
                                data, ensure_ascii=False).encode()

                        # 重建 Response 以更新 Body 和 Content-Length
                        response = Response(
                            content=new_body,
                            status_code=response.status_code,
                            headers=dict(response.headers),
                            media_type=response.media_type
                        )
                        response.headers["content-length"] = str(len(new_body))
                        response.headers["x-traceid-header"] = trace_id
                        # 恢复 CORS
                        for k, v in cors_headers.items():
                            response.headers[k] = v
                    except json.JSONDecodeError:
                        # 非 JSON 或解析失败，仅更新长度
                        response = Response(
                            content=response_body,
                            status_code=response.status_code,
                            headers=dict(response.headers),
                            media_type=response.media_type
                        )
                        response.headers["content-length"] = str(
                            len(response_body))
                        response.headers["x-traceid-header"] = trace_id
                        for k, v in cors_headers.items():
                            response.headers[k] = v
                else:
                    # 非 JSON 响应
                    response = Response(
                        content=response_body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
                    response.headers["content-length"] = str(
                        len(response_body))
                    response.headers["x-traceid-header"] = trace_id
                    for k, v in cors_headers.items():
                        response.headers[k] = v
            except StopAsyncIteration:
                pass

            # 构建响应日志
            response_message = {
                "traceId": trace_id,
                "status_code": response.status_code,
                "response_body": response_body.decode('utf-8', errors='ignore'),
            }
            SYLogger.info(json.dumps(response_message, ensure_ascii=False))

            # 兜底：确保 Header 必有 TraceId
            try:
                response.headers["x-traceid-header"] = trace_id
            except AttributeError:
                new_headers = dict(response.headers) if hasattr(
                    response.headers, 'items') else {}
                new_headers["x-traceid-header"] = trace_id
                if hasattr(response, "init_headers"):
                    response.init_headers(new_headers)

            # 如果执行到这里，说明一切正常，标记为无异常
            had_exception = False
            return response

        except Exception as e:
            # ========== 4. 异常处理阶段 ==========
            # 记录中间件层面的异常日志
            error_message = {
                "traceId": trace_id,
                "error": f"Middleware Error: {str(e)}",
                "query_params": query_params,
                "request_body": request_body,
                "uploaded_files": files_info if files_info else None
            }
            # 使用 SYLogger.error，由于处于 except 块，会自动捕获堆栈
            SYLogger.error(error_message)

            # 关键：重新抛出异常，让 Global Exception Handler 接管
            # 此时 had_exception 仍为 True，finally 不会 reset，trace_id 得以保留
            raise

        finally:
            # ========== 5. 清理阶段 ==========
            # 只有在没有任何异常的情况下（had_exception=False），才手动清除上下文
            if not had_exception:
                SYLogger.reset_trace_id(token)
                SYLogger.reset_headers(header_token)
            # 如果 had_exception 为 True，这里什么都不做，保留 ContextVar 供 Exception Handler 读取

    return app
