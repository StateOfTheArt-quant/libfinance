#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端调用的每个 RPC，服务端都必须真的有。

这条测试的由来：``libfinance/api/instrument.py`` 长期调用 ``get_all_obid_to_type``
与 ``get_all_instrument_dict_list``，而服务端**根本没有这两个 handler**
（``RpcError(code=1101): Function not found``）。也就是说 ``instruments()`` 与
``all_instruments()`` 这两个公开接口一直是坏的，而仓里没有任何东西会告诉你 ——
客户端与服务端各自演进，中间没有闸门。

做法是静态扫描：把源码里所有 ``get_client().X(...)`` / ``client.X(...)`` 的 X 收集起来，
跟服务端 ``describe_capabilities`` 报的名字比。需要一个在跑的服务端，没有就跳过 ——
这样它在 local-ci 里是真闸门，在没有服务的环境里不会误报。

    LIBFINANCE_TEST_HOST=127.0.0.1 LIBFINANCE_TEST_PORT=8080 pytest test/
"""
import os
import pathlib
import re

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
#: 传输层自己的方法，不是业务 RPC。
_TRANSPORT = {"call", "call_raw", "call_async", "send_ping", "close", "connect"}
#: 服务端总是提供、但不出现在 describe_capabilities 里的。
_ALWAYS = {"ping", "login", "describe_capabilities"}

_CALL = re.compile(r"(?:get_client\(\)|(?<![A-Za-z_])client)\.([a-z_][a-z0-9_]*)\s*\(")


def _client_rpc_names():
    names = set()
    for path in sorted((_ROOT / "libfinance").rglob("*.py")):
        for name in _CALL.findall(path.read_text(encoding="utf-8")):
            if name not in _TRANSPORT:
                names.add(name)
    return names


def test_the_scanner_finds_something():
    """扫描器本身失效时要红，否则上面那条会变成永远通过的空断言。"""
    names = _client_rpc_names()
    assert len(names) >= 8, names
    assert "get_price" in names and "get_shares" in names


@pytest.mark.skipif(
    not os.environ.get("LIBFINANCE_TEST_HOST"),
    reason="需要一个在跑的服务端：设 LIBFINANCE_TEST_HOST / LIBFINANCE_TEST_PORT",
)
def test_every_rpc_the_client_calls_exists_on_the_server():
    import libfinance
    from libfinance.client import get_client

    libfinance.init_client(
        host=os.environ["LIBFINANCE_TEST_HOST"],
        port=int(os.environ.get("LIBFINANCE_TEST_PORT", "8080")),
    )
    # 判据是**能不能路由到**，不是"在不在 describe_capabilities 里"。
    #
    # 那份清单只报 81 个 capability，而服务端注册了 102 个 handler：get_calendar_coverage /
    # get_concept_meta / get_last_quotes 这类扁平别名存在且可调，只是不在清单里。拿清单
    # 当白名单会把好接口误判成缺失。
    #
    # 所以逐个打一次空参调用：只有 FUNCTION_NOT_FOUND(1101) 算"不存在"，参数错、数据错
    # 都说明路由是通的 —— 这条测试只管"名字在不在"，不管参数对不对。
    client = get_client()
    missing = []
    for name in sorted(_client_rpc_names()):
        if name in _ALWAYS:
            continue
        try:
            client.call(name, {})
        except Exception as error:
            if getattr(error, "code", None) == 1101 or "Function not found" in str(error):
                missing.append(name)
    assert not missing, (
        "客户端调用了服务端没有的 RPC：{}。"
        "这类漂移不会在 import 时暴露，只会在用户调到那个接口时炸。".format(missing)
    )
