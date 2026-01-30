import functools
import time
from typing import Any

from .client import AlayaVisClient
from .types import Status


def notify(*, span_id: str):
    """
    自动上报函数执行情况的装饰器。

    使用规则:
    1. 被装饰的函数如果有名为 `trace_id` 的参数(kwargs)，会自动关联上下文。
    2. 如果没有 `trace_id`，会自动生成一个新的 Trace 作为根节点（由上层决定）。
    3. 自动捕获执行时间、入参(摘要)和异常。
    """
    if not isinstance(span_id, str) or not span_id:
        raise TypeError("notify(): span_id 必须是非空字符串")


    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client = AlayaVisClient.get_instance()
            if not client:  # 未初始化则直接执行业务逻辑
                return func(*args, **kwargs)

            # 尝试获取上下文 (Context Propagation)
            trace_id = kwargs.get("trace_id")
            base_payload = kwargs.get("payload") or {}

            # 上报函数开始 (RUNNING)
            start_ts = time.time()
            client._send_span(
                trace_id=trace_id,
                span_id=span_id,
                status=Status.RUNNING,
                payload={**base_payload, "start_ts": start_ts},
            )
            try:
                # === 执行原业务函数 ===
                result = func(*args, **kwargs)
                # ======================

                duration = (time.time() - start_ts) * 1000

                # 上报函数结束 (SUCCESS)
                client._send_span(
                    trace_id=trace_id,
                    span_id=span_id,
                    status=Status.SUCCESS,
                    payload={**base_payload, "latency_ms": duration},
                )
                return result

            except Exception as e:
                duration = (time.time() - start_ts) * 1000
                # 上报异常 (FAILED)
                client._send_span(
                    trace_id=trace_id,
                    span_id=span_id,
                    status=Status.FAILED,
                    payload={
                        **base_payload,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                )
                raise

        return wrapper

    return decorator
