import contextvars

current_trace_id = contextvars.ContextVar("trace_id", default=None)

current_headers = contextvars.ContextVar("headers", default=None)
