from enum import Enum


class HebraRunState(Enum):
    """运行状态枚举"""

    NOT_STARTED = "not_started"  # 未启动
    RUNNING = "running"  # 运行中
    SUCCESS = "success"  # 成功结束
    CRASHED = "crashed"  # 异常结束
