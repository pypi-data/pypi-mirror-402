from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sycommon.logging.kafka_log import SYLogger


def setup_exception_handler(app, config: dict):
    # 设置上传文件大小限制为 MaxBytes
    app.config = {'MAX_CONTENT_LENGTH': config.get('MaxBytes', 209715200)}

    # 1. 处理文件大小超限异常
    @app.exception_handler(413)
    async def request_entity_too_large(request: Request, exc):
        MaxBytes = config.get('MaxBytes', 209715200)
        int_MaxBytes = int(MaxBytes) / 1024 / 1024
        return JSONResponse(
            content={
                'code': 413, 'error': f'File size exceeds the allowed limit of {int_MaxBytes}MB.', 'traceId': SYLogger.get_trace_id()},
            status_code=413
        )

    # 2. 处理 HTTP 异常
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
                "traceId": SYLogger.get_trace_id()
            }
        )

    # 3. 处理 Pydantic 验证错误
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "message": "参数验证失败",
                "details": exc.errors(),
                "traceId": SYLogger.get_trace_id()
            }
        )

    # 4. 自定义业务异常
    class BusinessException(Exception):
        def __init__(self, code: int, message: str):
            self.code = code
            self.message = message

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        return JSONResponse(
            status_code=exc.code,
            content={
                "code": exc.code,
                "message": exc.message,
                "traceId": SYLogger.get_trace_id()
            }
        )

    # 5. 全局异常处理器（捕获所有未处理的异常）
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # 返回统一格式的错误响应（生产环境可选择不返回详细信息）
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "服务器内部错误，请稍后重试",
                "detail": str(exc) if config.get('DEBUG', False) else "Internal Server Error",
                "traceId": SYLogger.get_trace_id()
            }
        )

    return app
