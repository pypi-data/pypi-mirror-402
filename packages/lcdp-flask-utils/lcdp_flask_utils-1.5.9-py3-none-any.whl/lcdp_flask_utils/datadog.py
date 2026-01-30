import os

# Enable ddtrace only if DD_ENABLED
dd_enabled = os.getenv("DD_ENABLED") == "true"

def inject_middlewares(middlewares):
    if dd_enabled:
        from ddtrace.contrib.asgi import TraceMiddleware
        middlewares.insert(0, TraceMiddleware)