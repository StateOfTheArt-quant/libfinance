#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""按**服务端数据版本**缓存参考数据。

日历、instrument 全表、行业分类这类数据一天才变一次，但重查一次要几十毫秒 ——
``all_instruments`` 实测 75 ms / 14 rps，而单个登录用户的限额就是 20 rps，
**一个用户就能把服务端打满**\ 。而 ``get_price`` 每次都要 instrument 全表来分类标的。
所以客户端缓存不是优化，是这条链路能用的前提。

只按 TTL 缓存会同时犯两种错：

* 数据切了而 TTL 没到 —— 用着旧的 instrument 表，新股查不到；
* 数据没切而 TTL 到了 —— 白拉一次 75 ms 的重查询。

服务端的 ``ping`` 会返回 ``data_version``\ （current 那一版的 aggregate digest，
0.17 ms 且免限流）。缓存挂在它上面就没有窗口期：\ **变了立刻失效，没变永远命中**\ 。

``data_version`` 为 None 时（服务端还没有 current，或旧版服务端不报这个字段）退回
TTL 语义，不把 None 当成某个固定版本 —— 那样会把"未知"缓存成"没变"。
"""
import threading
import time

#: 向服务端问一次版本的最小间隔（秒）。ping 很便宜，但没必要每次调用都问。
_VERSION_POLL_SECONDS = 2.0
#: data_version 不可用时的退化 TTL（秒）。
_FALLBACK_TTL = 300.0

_lock = threading.Lock()
_version = None
_version_checked_at = 0.0
_caches = []


def current_data_version(force=False):
    r"""服务端当前的数据版本；拿不到时返回 None。

    结果在 ``_VERSION_POLL_SECONDS`` 内复用：同一次 ``get_price`` 里的几次查表不必
    各问一次。探活失败\ **不抛**——缓存不该让查询失败，退回 TTL 就是了。
    """
    global _version, _version_checked_at
    now = time.time()
    with _lock:
        if not force and now - _version_checked_at < _VERSION_POLL_SECONDS:
            return _version
    try:
        from libfinance.client import get_client

        pong = get_client().call("ping", {}, timeout=5.0)
        value = pong.get("data_version") if isinstance(pong, dict) else None
    except Exception:
        value = None
    with _lock:
        _version, _version_checked_at = value, time.time()
    return value


def versioned_cache(func):
    """按数据版本缓存。版本变了自动失效，版本不可用时退回 5 分钟 TTL。"""
    store = {}
    lock = threading.Lock()

    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        version = current_data_version()
        now = time.time()
        with lock:
            hit = store.get(key)
            if hit is not None:
                cached_version, cached_at, value = hit
                if version is not None and cached_version == version:
                    return value
                if version is None and cached_version is None and now - cached_at < _FALLBACK_TTL:
                    return value
        value = func(*args, **kwargs)
        with lock:
            store[key] = (version, now, value)
        return value

    def clear():
        with lock:
            store.clear()

    wrapper.clear = clear
    wrapper.__wrapped__ = func
    _caches.append(wrapper)
    try:
        from functools import update_wrapper

        update_wrapper(wrapper, func)
        wrapper.clear = clear
        wrapper.__wrapped__ = func
    except Exception:
        pass
    return wrapper


def clear_all():
    """清掉全部版本化缓存。数据切换会自动失效，这个是给测试和手工排错用的。"""
    global _version, _version_checked_at
    for c in _caches:
        c.clear()
    with _lock:
        _version, _version_checked_at = None, 0.0


# ---------------------------------------------------------------------------
# 分档限制：让它可见，而不是表现为一张空表
# ---------------------------------------------------------------------------
@versioned_cache
def _described():
    from libfinance.client import get_client

    return get_client().call("describe_capabilities", {}, timeout=10.0)


def limits_for(api_name):
    r"""当前账号在某个接口上的分档限制；拿不到时返回 {}。

    未登录时服务端会把 ``get_price`` 的 start_date 夹到"今天往前 2 年 3 个月"，
    而且 end_date 早于边界时也一起上拉 —— 于是 start==end，返回一张\ **空表**\ 。
    从调用方看，"这只股票没交易"、"数据没有"、"我的档位不够"长得一模一样。

    限制本来就在 describe_capabilities 里报着，客户端只是没读。
    """
    try:
        described = _described()
        for item in described.get("capabilities", ()):
            if item.get("api") == api_name or item.get("name") == api_name:
                return item.get("limits") or {}
    except Exception:
        pass
    return {}


def warn_if_clamped(api_name, start_date):
    """请求会被分档限制夹紧时给一句警告。返回边界日期，没有限制则返回 None。"""
    import warnings

    window = (limits_for(api_name) or {}).get("clamp_date_window")
    if not window or not start_date:
        return None
    try:
        import datetime

        from dateutil.relativedelta import relativedelta

        boundary = (datetime.datetime.today() - relativedelta(
            years=window.get("years", 0), months=window.get("months", 0),
            days=window.get("days", 0))).strftime("%Y-%m-%d")
    except Exception:
        return None
    if str(start_date) >= boundary:
        return None
    warnings.warn(
        "{}: 当前账号的可查区间起点是 {}，比它更早的 start_date={} 会被服务端夹到边界"
        "（end_date 早于边界时也会一起上拉，结果可能是空表）。"
        .format(api_name, boundary, start_date),
        stacklevel=3,
    )
    return boundary
