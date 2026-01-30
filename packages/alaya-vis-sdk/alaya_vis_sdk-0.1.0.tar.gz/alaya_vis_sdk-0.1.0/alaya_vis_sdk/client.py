import time
import threading
import queue
import atexit
import requests
import logging
import psutil  # 依赖: pip install psutil
from typing import Optional

from .types import Status


logger = logging.getLogger("alayavis-sdk")


class AlayaVisClient:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, endpoint: str = "http://localhost:8088", module_name: str = "Unknown", queue_size: int = 1000):
        self.endpoint = endpoint.rstrip("/")
        self.module_name = module_name
        self.session = requests.Session()
        self.last_trace_id = ""

        # 异步发送队列与后台工作线程
        self.queue = queue.Queue(maxsize=queue_size)
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

        # 注册退出清理钩子
        atexit.register(self._shutdown)

    @classmethod
    def get_instance(cls):
        """获取单例"""
        if not cls._instance:
            logger.warning("AlayaVisClient not initialized, call init() first.")
        return cls._instance

    @classmethod
    def init(cls, endpoint: str, module_name: str, enable_system_monitor: bool = True):
        """
        全局初始化 SDK
        :param enable_system_monitor: 是否自动启动 CPU/内存 监控线程 (默认 True)
        """
        with cls._lock:
            if not cls._instance:
                cls._instance = AlayaVisClient(endpoint, module_name)
                # 自动启动系统资源监控
                if enable_system_monitor:
                    cls._instance.start_system_monitor()
        return cls._instance

    def start_system_monitor(self, interval_seconds: int = 5):
        """开启系统资源自动监控 (CPU/Memory)"""

        def _monitor_loop():
            # 首次调用可能返回 0，先调用一次
            psutil.cpu_percent(interval=None)
            while True:
                try:
                    time.sleep(interval_seconds)
                    cpu = psutil.cpu_percent(interval=None)
                    mem = psutil.virtual_memory()

                    payload = {
                        "last_trace_id": self.last_trace_id,
                        "cpu_percent": cpu,
                        "memory_used_mb": mem.used / 1024 / 1024,
                        "memory_percent": mem.percent,
                        "thread_count": threading.active_count(),
                    }
                    # 使用特殊的 Trace ID "system-heartbeat" 上报
                    self._send_span(
                        trace_id=f"system-{self.module_name}",
                        span_id="HEARTBEAT",
                        status=Status.SUCCESS,
                        payload=payload,
                    )
                except Exception as e:
                    logger.error(f"System monitor error: {e}")

        t = threading.Thread(target=_monitor_loop, daemon=True)
        t.start()
        logger.info("AlayaVis system monitor started.")

    def _send_span(self, trace_id: str, span_id, status, payload):
        if not str(trace_id).startswith("system"):
            self.last_trace_id = trace_id
        data = {
            "trace_id": trace_id,
            "span_id": span_id,
            "module": self.module_name,
            "status": status.value,
            "payload": payload,
        }

        # 将日志放入队列，如果队列已满则丢弃，避免阻塞主业务
        try:
            self.queue.put(data, block=False)
        except queue.Full:
            logger.warning("AlayaVis SDK queue full, dropping span.")

    def _worker(self):
        """后台消费者线程：从队列取出日志并发送"""
        while True:
            try:
                data = self.queue.get()
                if data is None:  # 退出信号
                    break
                self._post_data(data)
                self.queue.task_done()
            except Exception as e:
                logger.error(f"Worker thread error: {e}")

    def _post_data(self, data):
        try:
            url = f"{self.endpoint}/api/v1/report/span"
            response = self.session.post(url, json=data, timeout=1.0)
            if response.status_code >= 400:
                logger.warning(f"AlayaVis report failed: {response.status_code}")
        except Exception:
            # 静默失败，不影响主业务
            pass

    def _shutdown(self):
        """应用退出时的清理操作（可选等待队列清空）"""
        try:
            # 发送退出信号给 worker 并等待短时间
            try:
                self.queue.put(None, block=False)
            except Exception:
                pass
        except Exception:
            pass
