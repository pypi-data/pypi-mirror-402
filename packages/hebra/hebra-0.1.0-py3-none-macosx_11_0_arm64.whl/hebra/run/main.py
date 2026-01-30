from __future__ import annotations

import atexit
import os
import sys
import traceback
from typing import Any, Dict, Optional

from .state import HebraRunState
from ..lib.service_connection import ServiceConnection
from ..lib.utils import kvs_from_mapping


class HebraRun:
    """Hebra运行实例，类似SwanLabRun。

    一个进程同时只能有一个HebraRun实例在运行。
    """

    def __init__(
        self,
        project: str,
        logdir: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        """初始化HebraRun。

        Args:
            project: 项目名称
            logdir: 日志存储目录
            config: 可选的配置参数
        """
        if self.is_started():
            raise RuntimeError("HebraRun已经初始化，请先调用finish()结束当前运行")

        global _current_run

        # 保存配置
        self._project = project
        self._logdir = logdir
        self._config = config or {}
        self._state = HebraRunState.RUNNING
        self._step = 0

        # 创建日志目录
        logdir = os.path.abspath(logdir)
        os.makedirs(logdir, exist_ok=True)
        db_path = os.path.join(logdir, "db")

        # 启动服务连接
        self._conn = ServiceConnection(db_path)
        self._conn.start()

        # 注册系统回调
        self._register_sys_callback()

        # 设置全局实例
        _current_run = self

        print(f"[hebra] 实验已初始化: project={project}, logdir={logdir}")

    def _register_sys_callback(self) -> None:
        """注册系统退出回调"""
        self._orig_excepthook = sys.excepthook
        sys.excepthook = self._except_handler
        atexit.register(self._clean_handler)

    def _unregister_sys_callback(self) -> None:
        """注销系统退出回调"""
        sys.excepthook = self._orig_excepthook
        atexit.unregister(self._clean_handler)

    def _clean_handler(self) -> None:
        """正常退出时的清理函数（atexit）"""
        if self._state == HebraRunState.RUNNING:
            print("[hebra] 程序退出，自动关闭实验...")
            self.finish()

    def _except_handler(self, exc_type, exc_val, exc_tb) -> None:
        """异常退出时的处理函数（excepthook）"""
        # 生成错误堆栈
        error_lines = traceback.format_exception(exc_type, exc_val, exc_tb)
        error_msg = "".join(error_lines)

        # 标记为崩溃状态
        if self._state == HebraRunState.RUNNING:
            print("[hebra] 检测到异常，标记实验为CRASHED...")
            self.finish(state=HebraRunState.CRASHED, error=error_msg)

        # 调用原始excepthook打印错误
        self._orig_excepthook(exc_type, exc_val, exc_tb)

    @staticmethod
    def is_started() -> bool:
        """检查是否已初始化"""
        return get_run() is not None

    @staticmethod
    def get_state() -> HebraRunState:
        """获取当前运行状态"""
        run = get_run()
        return run._state if run else HebraRunState.NOT_STARTED

    @property
    def running(self) -> bool:
        """是否正在运行"""
        return self._state == HebraRunState.RUNNING

    @property
    def success(self) -> bool:
        """是否成功结束"""
        return self._state == HebraRunState.SUCCESS

    @property
    def crashed(self) -> bool:
        """是否异常结束"""
        return self._state == HebraRunState.CRASHED

    @property
    def config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config

    @property
    def project(self) -> str:
        """获取项目名称"""
        return self._project

    def log(
        self,
        data: Dict[str, Any],
        step: Optional[int] = None,
    ) -> Dict[str, Any]:
        """记录数据。

        Args:
            data: 键值对数据
            step: 可选的步数，不提供则自动递增

        Returns:
            记录结果
        """
        if self._state != HebraRunState.RUNNING:
            raise RuntimeError("实验已结束，无法继续记录数据")

        if not isinstance(data, dict):
            raise TypeError(f"data必须是dict类型，但收到了{type(data)}")

        # 处理step
        if step is None:
            step = self._step
            self._step += 1
        elif not isinstance(step, int) or step < 0:
            print(f"[hebra] 警告: step必须是非负整数，忽略传入的step={step}")
            step = self._step
            self._step += 1

        # 转换数据并上传
        kv_list = kvs_from_mapping(data)
        resp = self._conn.upload(kv_list)

        return {"step": step, "success": resp.success, "message": resp.message}

    def finish(
        self,
        state: HebraRunState = HebraRunState.SUCCESS,
        error: Optional[str] = None,
    ) -> None:
        """结束运行。

        Args:
            state: 结束状态
            error: 错误信息（仅当state为CRASHED时使用）
        """
        global _current_run

        if self._state != HebraRunState.RUNNING:
            print("[hebra] 警告: 实验已结束，忽略重复的finish调用")
            return

        # 更新状态
        self._state = state

        # 注销系统回调
        self._unregister_sys_callback()

        # 关闭服务连接
        exit_code = 0 if state == HebraRunState.SUCCESS else 1
        self._conn.shutdown(exit_code=exit_code)

        # 清除全局实例
        _current_run = None

        status = "SUCCESS" if state == HebraRunState.SUCCESS else "CRASHED"
        print(f"[hebra] 实验已结束: status={status}")

        if error:
            print(f"[hebra] 错误信息: {error[:200]}...")


# 全局运行实例
_current_run: Optional[HebraRun] = None


def get_run() -> Optional[HebraRun]:
    """获取当前运行实例。

    Returns:
        当前HebraRun实例，未初始化时返回None
    """
    return _current_run
