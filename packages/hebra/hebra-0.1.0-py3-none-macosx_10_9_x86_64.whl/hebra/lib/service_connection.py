from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

import grpc

# Proto imports
from common.v1 import common_pb2
from core.collector.v1 import (
    collector_service_pb2,
    collector_service_pb2_grpc,
)
from core.lifecycle.v1 import (
    lifecycle_service_pb2,
    lifecycle_service_pb2_grpc,
)


class ServiceConnection:
    """管理与Go服务的连接（内部使用）"""

    def __init__(self, db_path: str):
        self._proc: Optional[subprocess.Popen] = None
        self._channel: Optional[grpc.Channel] = None
        self._workdir: Optional[Path] = None
        self._db_path = db_path

    def start(self) -> None:
        """启动Go服务进程"""
        if self._proc is not None:
            return

        server_bin = find_server_bin()
        self._workdir = Path(tempfile.mkdtemp(prefix="hebra-"))
        port_file = self._workdir / "port.txt"

        self._proc = subprocess.Popen(
            [
                str(server_bin),
                "--pid",
                str(os.getpid()),
                "--port-file",
                str(port_file),
                "--db-path",
                self._db_path,
            ],
            cwd=self._workdir,
        )

        addr_line = wait_for_address(port_file)
        kind, target = parse_address(addr_line)
        self._channel = make_channel(kind, target)

    def upload(
        self, data: common_pb2.KeyValueList
    ) -> collector_service_pb2.CollectorUploadResponse:
        """上传数据到Go服务"""
        if self._channel is None:
            raise RuntimeError("服务未启动")
        stub = collector_service_pb2_grpc.CollectorStub(self._channel)
        req = collector_service_pb2.CollectorUploadRequest(data=data)
        return stub.Upload(req, timeout=5)

    def shutdown(self, exit_code: int = 0, timeout: float = 5.0) -> None:
        """关闭Go服务"""
        if self._channel is not None and self._proc is not None:
            try:
                stub = lifecycle_service_pb2_grpc.LifecycleStub(self._channel)
                req = lifecycle_service_pb2.ShutdownRequest(exit_code=exit_code)
                stub.Shutdown(req, timeout=2)
            except grpc.RpcError:
                pass
            finally:
                self._channel.close()
                self._channel = None

        if self._proc is not None:
            try:
                self._proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()
            self._proc = None

        if self._workdir is not None:
            shutil.rmtree(self._workdir, ignore_errors=True)
            self._workdir = None


# 内部辅助函数


def find_server_bin() -> Path:
    """查找Go服务二进制文件"""
    from .. import PKG_ROOT

    exe_name = "core.exe" if os.name == "nt" else "core"
    bin_path = PKG_ROOT / "bin" / exe_name
    if bin_path.exists() and bin_path.is_file():
        return bin_path
    raise FileNotFoundError(f"服务二进制文件未找到: {bin_path}")


def wait_for_address(path: Path, timeout: float = 10.0) -> str:
    """等待端口文件生成并读取地址"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            text = path.read_text().strip()
            if text:
                return text.splitlines()[0].strip()
        time.sleep(0.1)
    raise TimeoutError(f"端口文件未在{timeout}秒内生成")


def parse_address(line: str) -> tuple:
    """解析地址格式"""
    if line.startswith("unix://"):
        return "unix", line[len("unix://") :]
    if line.startswith("tcp://"):
        return "tcp", line[len("tcp://") :]
    raise ValueError(f"未知地址格式: {line}")


def make_channel(kind: str, target: str) -> grpc.Channel:
    """创建gRPC通道"""
    if kind == "unix":
        return grpc.insecure_channel(f"unix://{target}")
    if target.startswith(":"):
        target = f"localhost{target}"
    return grpc.insecure_channel(target)
