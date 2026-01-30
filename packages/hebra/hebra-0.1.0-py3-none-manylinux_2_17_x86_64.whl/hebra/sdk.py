from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .run import HebraRun, HebraRunState, get_run
from .lib.utils import should_call_after_init


def init(
    project: Optional[str] = None,
    logdir: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    reinit: bool = False,
) -> HebraRun:
    """初始化hebra实验。

    Args:
        project: 项目名称，默认为当前目录名
        logdir: 日志存储目录，默认为"./hebralog"
        config: 可选的配置参数
        reinit: 是否重新初始化（会先结束当前运行）

    Returns:
        HebraRun实例

    Raises:
        RuntimeError: 已初始化且reinit=False时
    """
    _current_run = get_run()

    # 处理重复初始化
    if HebraRun.is_started():
        if reinit:
            print("[hebra] reinit=True，先结束当前实验...")
            _current_run.finish()
        else:
            print("[hebra] 警告: 实验已初始化，返回当前实例。使用reinit=True可重新初始化")
            return _current_run

    # 默认值处理
    if project is None:
        project = os.path.basename(os.getcwd())
    if logdir is None:
        logdir = os.path.join(os.getcwd(), "hebralog")

    return HebraRun(project=project, logdir=logdir, config=config)


@should_call_after_init("必须先调用hebra.init()才能使用log()")
def log(
    data: Dict[str, Any],
    step: Optional[int] = None,
) -> Dict[str, Any]:
    """记录数据到当前运行。

    Args:
        data: 键值对数据
        step: 可选的步数

    Returns:
        记录结果
    """
    return get_run().log(data, step)


@should_call_after_init("必须先调用hebra.init()才能使用finish()")
def finish(
    state: HebraRunState = HebraRunState.SUCCESS,
    error: Optional[str] = None,
) -> None:
    """结束当前运行。

    Args:
        state: 结束状态
        error: 错误信息
    """
    get_run().finish(state, error)
