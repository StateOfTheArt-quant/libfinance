#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""旧参数名的弃用期支持。

服务端把"知识截止时间"与"数据日期"分成了两个名字，这个区分是有意义的：

    as_of —— 站在哪一天回头看（财报会被追溯修订，回测里传错就用上了未来信息）
    date  —— 要哪一天的数据

客户端此前一律叫 ``date``，于是 ``get_concept_weights(date=...)`` 直接被服务端拒绝
（``未知参数 ['date']；可用 ['as_of', ...]``）。

改名是破坏性的，所以给弃用期：旧名仍然接受，但发 DeprecationWarning 并转成新名。
两个都给则报错 —— 那说明调用方自己也不确定要哪个语义，不该替他猜。
"""
import warnings


def renamed(old, new, kwargs, func_name):
    """把 kwargs 里的 ``old`` 改名成 ``new``，原地修改并返回它。"""
    if old not in kwargs:
        return kwargs
    if kwargs.get(new) is not None and kwargs[old] is not None:
        raise TypeError(
            "{}: {!r} 与 {!r} 只能给一个（{!r} 是旧名，已弃用）".format(
                func_name, old, new, old
            )
        )
    value = kwargs.pop(old)
    if value is not None:
        warnings.warn(
            "{}: 参数 {!r} 已改名为 {!r}，旧名将在下一个大版本移除。"
            "服务端把'知识截止时间'(as_of)与'数据日期'(date)分开了，两者含义不同。"
            .format(func_name, old, new),
            DeprecationWarning,
            stacklevel=3,
        )
        kwargs[new] = value
    return kwargs
