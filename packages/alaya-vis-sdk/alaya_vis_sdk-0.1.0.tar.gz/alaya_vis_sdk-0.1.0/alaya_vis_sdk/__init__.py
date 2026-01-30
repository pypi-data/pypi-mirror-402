"""Alaya VIS SDK package

提供轻量的导出接口：AlayaVisClient, TaskType, Status, notify
"""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("alaya-vis-sdk")
except PackageNotFoundError:
    # 在源码树中直接使用时退回到默认版本号
    __version__ = "0.1.0"

from .client import AlayaVisClient, logger  # noqa: E402
from .types import TaskType, Status  # noqa: E402
from .decorators import notify  # noqa: E402

__all__ = ["AlayaVisClient", "TaskType", "Status", "notify", "logger", "__version__"]
