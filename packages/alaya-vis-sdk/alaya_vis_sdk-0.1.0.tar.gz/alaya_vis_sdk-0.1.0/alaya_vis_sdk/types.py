from enum import Enum


class TaskType(str, Enum):
    INFERENCE = "INFERENCE"   # 问答推理
    INGESTION = "INGESTION"   # 知识入库/ETL
    SYSTEM = "SYSTEM"         # 系统状态/管理
    EVALUATION = "EVALUATION" # 评测任务


class Status(str, Enum):
    START = "START"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
