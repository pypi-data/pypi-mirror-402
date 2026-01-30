from __future__ import annotations

from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from ..run import HebraRun

# Proto imports (需要在包初始化时设置好 sys.path)
from common.v1 import common_pb2


def should_call_before_init(error_message: str):
    """装饰器：限制必须在init之前调用"""
    from ..run import HebraRun

    def decorator(func):
        def wrapper(*args, **kwargs):
            if HebraRun.is_started():
                raise RuntimeError(error_message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def should_call_after_init(error_message: str):
    """装饰器：限制必须在init之后调用"""
    from ..run import HebraRun

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not HebraRun.is_started():
                raise RuntimeError(error_message)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def to_any(value: Any) -> common_pb2.AnyValue:
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
        arr = common_pb2.ArrayValue(values=[to_any(v) for v in value])
        return common_pb2.AnyValue(array_value=arr)
    # 其他类型转为字符串
    return common_pb2.AnyValue(string_value=str(value))


def kvs_from_mapping(kvs: Mapping[str, Any]) -> common_pb2.KeyValueList:
    """将字典转换为KeyValueList"""
    kv_list = common_pb2.KeyValueList()
    for k, v in kvs.items():
        if not k:
            continue
        kv_list.values.append(common_pb2.KeyValue(key=str(k), value=to_any(v)))
    return kv_list
