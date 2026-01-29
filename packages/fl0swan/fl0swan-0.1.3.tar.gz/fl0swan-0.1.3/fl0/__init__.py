from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

import grpc

# 路径配置

PKG_ROOT = Path(__file__).resolve().parent
PKG_PROTO_ROOT = PKG_ROOT / "proto"

if str(PKG_PROTO_ROOT) not in sys.path and PKG_PROTO_ROOT.exists():
    sys.path.append(str(PKG_PROTO_ROOT))

from common.v1 import common_pb2
from core.collector.v1 import (
    collector_service_pb2,
    collector_service_pb2_grpc,
)
from core.lifecycle.v1 import (
    lifecycle_service_pb2,
    lifecycle_service_pb2_grpc,
)


class Fl0RunState(Enum):
    """运行状态枚举"""

    NOT_STARTED = "not_started"  # 未启动
    RUNNING = "running"  # 运行中
    SUCCESS = "success"  # 成功结束
    CRASHED = "crashed"  # 异常结束


# 调用顺序装饰器


def _should_call_before_init(error_message: str):
    """装饰器：限制必须在init之前调用"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if Fl0Run.is_started():
                raise RuntimeError(error_message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _should_call_after_init(error_message: str):
    """装饰器：限制必须在init之后调用"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not Fl0Run.is_started():
                raise RuntimeError(error_message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


# 内部服务连接类
class _ServiceConnection:
    """管理与Go服务的连接"""

    def __init__(self, db_path: str):
        self._proc: Optional[subprocess.Popen] = None
        self._channel: Optional[grpc.Channel] = None
        self._workdir: Optional[Path] = None
        self._db_path = db_path

    def start(self) -> None:
        """启动Go服务进程"""
        if self._proc is not None:
            return

        server_bin = _find_server_bin()
        self._workdir = Path(tempfile.mkdtemp(prefix="fl0-"))
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

        addr_line = _wait_for_address(port_file)
        kind, target = _parse_address(addr_line)
        self._channel = _make_channel(kind, target)

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


# Fl0Run 类
class Fl0Run:
    """Fl0运行实例，类似SwanLabRun。

    一个进程同时只能有一个Fl0Run实例在运行。
    """

    def __init__(
        self,
        project: str,
        logdir: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        """初始化Fl0Run。

        Args:
            project: 项目名称
            logdir: 日志存储目录
            config: 可选的配置参数
        """
        if self.is_started():
            raise RuntimeError("Fl0Run已经初始化，请先调用finish()结束当前运行")

        global _current_run

        # 保存配置
        self._project = project
        self._logdir = logdir
        self._config = config or {}
        self._state = Fl0RunState.RUNNING
        self._step = 0

        # 创建日志目录
        logdir = os.path.abspath(logdir)
        os.makedirs(logdir, exist_ok=True)
        db_path = os.path.join(logdir, "db")

        # 启动服务连接
        self._conn = _ServiceConnection(db_path)
        self._conn.start()

        # 注册系统回调
        self._register_sys_callback()

        # 设置全局实例
        _current_run = self

        print(f"[fl0] 实验已初始化: project={project}, logdir={logdir}")

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
        if self._state == Fl0RunState.RUNNING:
            print("[fl0] 程序退出，自动关闭实验...")
            self.finish()

    def _except_handler(self, exc_type, exc_val, exc_tb) -> None:
        """异常退出时的处理函数（excepthook）"""
        # 生成错误堆栈
        error_lines = traceback.format_exception(exc_type, exc_val, exc_tb)
        error_msg = "".join(error_lines)

        # 标记为崩溃状态
        if self._state == Fl0RunState.RUNNING:
            print("[fl0] 检测到异常，标记实验为CRASHED...")
            self.finish(state=Fl0RunState.CRASHED, error=error_msg)

        # 调用原始excepthook打印错误
        self._orig_excepthook(exc_type, exc_val, exc_tb)

    @staticmethod
    def is_started() -> bool:
        """检查是否已初始化"""
        return get_run() is not None

    @staticmethod
    def get_state() -> Fl0RunState:
        """获取当前运行状态"""
        run = get_run()
        return run._state if run else Fl0RunState.NOT_STARTED

    @property
    def running(self) -> bool:
        """是否正在运行"""
        return self._state == Fl0RunState.RUNNING

    @property
    def success(self) -> bool:
        """是否成功结束"""
        return self._state == Fl0RunState.SUCCESS

    @property
    def crashed(self) -> bool:
        """是否异常结束"""
        return self._state == Fl0RunState.CRASHED

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
        if self._state != Fl0RunState.RUNNING:
            raise RuntimeError("实验已结束，无法继续记录数据")

        if not isinstance(data, dict):
            raise TypeError(f"data必须是dict类型，但收到了{type(data)}")

        # 处理step
        if step is None:
            step = self._step
            self._step += 1
        elif not isinstance(step, int) or step < 0:
            print(f"[fl0] 警告: step必须是非负整数，忽略传入的step={step}")
            step = self._step
            self._step += 1

        # 转换数据并上传
        kv_list = _kvs_from_mapping(data)
        resp = self._conn.upload(kv_list)

        return {"step": step, "success": resp.success, "message": resp.message}

    def finish(
        self,
        state: Fl0RunState = Fl0RunState.SUCCESS,
        error: Optional[str] = None,
    ) -> None:
        """结束运行。

        Args:
            state: 结束状态
            error: 错误信息（仅当state为CRASHED时使用）
        """
        global _current_run

        if self._state != Fl0RunState.RUNNING:
            print("[fl0] 警告: 实验已结束，忽略重复的finish调用")
            return

        # 更新状态
        self._state = state

        # 注销系统回调
        self._unregister_sys_callback()

        # 关闭服务连接
        exit_code = 0 if state == Fl0RunState.SUCCESS else 1
        self._conn.shutdown(exit_code=exit_code)

        # 清除全局实例
        _current_run = None

        status = "SUCCESS" if state == Fl0RunState.SUCCESS else "CRASHED"
        print(f"[fl0] 实验已结束: status={status}")

        if error:
            print(f"[fl0] 错误信息: {error[:200]}...")


_current_run: Optional[Fl0Run] = None


def init(
    project: Optional[str] = None,
    logdir: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    reinit: bool = False,
) -> Fl0Run:
    """初始化fl0实验。

    Args:
        project: 项目名称，默认为当前目录名
        logdir: 日志存储目录，默认为"./fl0log"
        config: 可选的配置参数
        reinit: 是否重新初始化（会先结束当前运行）

    Returns:
        Fl0Run实例

    Raises:
        RuntimeError: 已初始化且reinit=False时
    """
    global _current_run

    # 处理重复初始化
    if Fl0Run.is_started():
        if reinit:
            print("[fl0] reinit=True，先结束当前实验...")
            _current_run.finish()
        else:
            print("[fl0] 警告: 实验已初始化，返回当前实例。使用reinit=True可重新初始化")
            return _current_run

    # 默认值处理
    if project is None:
        project = os.path.basename(os.getcwd())
    if logdir is None:
        logdir = os.path.join(os.getcwd(), "fl0log")

    return Fl0Run(project=project, logdir=logdir, config=config)


@_should_call_after_init("必须先调用fl0.init()才能使用log()")
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
    return _current_run.log(data, step)


@_should_call_after_init("必须先调用fl0.init()才能使用finish()")
def finish(
    state: Fl0RunState = Fl0RunState.SUCCESS,
    error: Optional[str] = None,
) -> None:
    """结束当前运行。

    Args:
        state: 结束状态
        error: 错误信息
    """
    _current_run.finish(state, error)


def get_run() -> Optional[Fl0Run]:
    """获取当前运行实例。

    Returns:
        当前Fl0Run实例，未初始化时返回None
    """
    return _current_run


def _find_server_bin() -> Path:
    """查找Go服务二进制文件"""
    exe_name = "core.exe" if os.name == "nt" else "core"
    bin_path = PKG_ROOT / "bin" / exe_name
    if bin_path.exists() and bin_path.is_file():
        return bin_path
    raise FileNotFoundError(f"服务二进制文件未找到: {bin_path}")


def _wait_for_address(path: Path, timeout: float = 10.0) -> str:
    """等待端口文件生成并读取地址"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists():
            text = path.read_text().strip()
            if text:
                return text.splitlines()[0].strip()
        time.sleep(0.1)
    raise TimeoutError(f"端口文件未在{timeout}秒内生成")


def _parse_address(line: str) -> tuple:
    """解析地址格式"""
    if line.startswith("unix://"):
        return "unix", line[len("unix://") :]
    if line.startswith("tcp://"):
        return "tcp", line[len("tcp://") :]
    raise ValueError(f"未知地址格式: {line}")


def _make_channel(kind: str, target: str) -> grpc.Channel:
    """创建gRPC通道"""
    if kind == "unix":
        return grpc.insecure_channel(f"unix://{target}")
    if target.startswith(":"):
        target = f"localhost{target}"
    return grpc.insecure_channel(target)


def _to_any(value: Any) -> common_pb2.AnyValue:
    """将Python值转换为AnyValue"""
    if isinstance(value, bool):
        return common_pb2.AnyValue(bool_value=value)
    if isinstance(value, int):
        return common_pb2.AnyValue(int_value=value)
    if isinstance(value, float):
        return common_pb2.AnyValue(double_value=value)
    if isinstance(value, str):
        return common_pb2.AnyValue(string_value=value)
    if isinstance(value, (list, tuple)):
        arr = common_pb2.ArrayValue(values=[_to_any(v) for v in value])
        return common_pb2.AnyValue(array_value=arr)
    # 其他类型转为字符串
    return common_pb2.AnyValue(string_value=str(value))


def _kvs_from_mapping(kvs: Mapping[str, Any]) -> common_pb2.KeyValueList:
    """将字典转换为KeyValueList"""
    kv_list = common_pb2.KeyValueList()
    for k, v in kvs.items():
        if not k:
            continue
        kv_list.values.append(common_pb2.KeyValue(key=str(k), value=_to_any(v)))
    return kv_list


# 导出
__all__ = [
    "init",
    "log",
    "finish",
    "get_run",
    "Fl0Run",
    "Fl0RunState",
]
