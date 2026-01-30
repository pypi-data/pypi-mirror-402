"""hebra: SwanLab风格的实验追踪SDK（demo版本）。

使用方式：
    import hebra

    # 1. 初始化（启动Go服务进程）
    run = hebra.init(project="my-project", logdir="./logs")

    # 2. 记录数据
    hebra.log({"loss": 0.1, "acc": 0.9})
    # 或通过run对象
    run.log({"loss": 0.1})

    # 3. 可选：手动结束（不调用会自动结束）
    hebra.finish()
"""

from __future__ import annotations

import sys
from pathlib import Path

# ============================================================================
# Proto 路径配置（必须在导入模块前完成）
# ============================================================================

PKG_ROOT = Path(__file__).resolve().parent
PKG_PROTO_ROOT = PKG_ROOT / "proto"

if str(PKG_PROTO_ROOT) not in sys.path and PKG_PROTO_ROOT.exists():
    sys.path.append(str(PKG_PROTO_ROOT))

# ============================================================================
# 导入核心 API
# ============================================================================

from .run import HebraRun, HebraRunState, get_run
from .sdk import init, log, finish

# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "init",
    "log",
    "finish",
    "get_run",
    "HebraRun",
    "HebraRunState",
]
