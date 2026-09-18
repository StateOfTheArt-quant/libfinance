#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 的签名契约。

这些是**静态**检查，不需要服务端。钉住的是几个曾经真的坏过的点。
"""
import ast
import inspect
import pathlib
import warnings

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _defaults(func):
    sig = inspect.signature(func)
    return {k: v.default for k, v in sig.parameters.items()}


def test_get_price_defaults_match_the_server():
    """默认值必须与服务端一致。

    此前客户端是 adjust_type='none' / skip_suspended=True，服务端是 'pre' / False ——
    同一个语义调用，走客户端和走服务端内部得到不同的数字，而这种不一致没有任何人能从
    文档上看出来。这是**静默的数值差异**，比报错危险。
    """
    from libfinance.api.get_price import get_price

    d = _defaults(get_price)
    assert d["adjust_type"] == "pre", "与服务端默认值脱节了"
    assert d["skip_suspended"] is False
    assert d["frequency"] == "1d"


def test_industry_source_default_is_one_the_server_accepts():
    """默认 source 必须是服务端认的。

    曾经是 '010303'（旧数据源的申万编码），服务端只支持 'sw'，于是这个接口用默认参数
    调**一直是报错的**：unsupported source: 010303; available: sw。
    """
    from libfinance.api.index_components import get_instrument_industry
    from libfinance.api.industry import get_industry, get_industry_mapping

    for func in (get_instrument_industry, get_industry, get_industry_mapping):
        assert _defaults(func)["source"] == "sw", func.__name__


def test_index_code_is_required_not_silently_defaulted():
    """get_index_weights 不该默认给沪深300 —— 拿错指数比报错更难发现。"""
    from libfinance.api.index_components import get_index_weights

    assert _defaults(get_index_weights)["index_code"] is inspect.Parameter.empty


def test_no_api_still_sends_the_retired_date_parameter_as_as_of():
    """服务端把 as_of（知识截止）与 date（数据日期）分开了，客户端要跟上。

    get_concept_weights 曾经发 date，被服务端直接拒绝：
    未知参数 ['date']；可用 ['as_of', 'concept_ids', 'market', 'source']
    """
    source = (_ROOT / "libfinance" / "api" / "concept_components.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if getattr(func, "attr", None) != "get_concept_weights":
            continue
        sent = {k.arg for k in node.keywords if k.arg}
        assert "date" not in sent, "又把 date 发给服务端了；它要的是 as_of"


def test_deprecated_names_still_work_but_warn():
    from libfinance.utils.compat import renamed

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = renamed("date", "as_of", {"date": "2026-01-01"}, "f")
    assert out == {"as_of": "2026-01-01"}
    assert caught and issubclass(caught[0].category, DeprecationWarning)

    # 两个都给 —— 不替调用方猜要哪个语义。
    with pytest.raises(TypeError, match="只能给一个"):
        renamed("date", "as_of", {"date": "2026-01-01", "as_of": "2026-02-01"}, "f")

    # 旧名给 None 等于没给，不该发警告。
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert renamed("date", "as_of", {"date": None, "as_of": "x"}, "f") == {"as_of": "x"}
    assert not caught


def test_instrument_helpers_that_validators_depends_on_exist():
    """validators.ensure_instruments 用名字 import 这两个，删了它 get_price 就崩。

    真发生过：重写 instrument.py 时删掉了它们，get_price 直接 ImportError ——
    而 import libfinance 本身不报错，只有调到 get_price 才炸。
    """
    from libfinance.api import instrument

    assert hasattr(instrument, "all_cached_obid_to_type_mapping")
    assert hasattr(instrument, "_get_instrument")

    source = (_ROOT / "libfinance" / "utils" / "validators.py").read_text(encoding="utf-8")
    assert "all_cached_obid_to_type_mapping" in source and "_get_instrument" in source


def test_get_price_resolves_codes_as_of_the_window_end_not_today():
    """代码表按**查询窗口末端**解析，不是按今天 —— 与服务端 compose/price.py 同口径。

    不这样的话，已退市的证券在客户端就被 ensure_instruments 当成"无效代码"整个丢掉，
    服务端根本没机会回答：

        get_price(['600837.XSHG'], '2022-09-01', '2022-09-20')
        -> ValueError: order_book_ids: at least one valid instrument expected, got none

    而 600837.XSHG（海通证券）在 2022 年确实在交易。服务端那侧已经按窗口末端解析了，
    客户端这一层不跟上就等于白改。
    """
    source = (_ROOT / "libfinance" / "api" / "get_price.py").read_text(encoding="utf-8")
    assert "classify_order_book_ids(\n        order_book_ids, as_of=end_date)" in source, \
        "get_price 没把 end_date 传给代码解析"

    import inspect

    from libfinance.api.instrument import _get_instrument, all_cached_obid_to_type_mapping
    from libfinance.utils.validators import ensure_instruments

    for func in (ensure_instruments, all_cached_obid_to_type_mapping, _get_instrument):
        assert "as_of" in inspect.signature(func).parameters, func.__name__


# ---------------------------------------------------------------------------
# 面板形状：两个市场给身份的方式不同，返回形状必须一样
# ---------------------------------------------------------------------------
def _panel(rows):
    pd = pytest.importorskip("pandas")
    from libfinance.api.get_price import _to_panel

    return _to_panel(pd.DataFrame(rows))


@pytest.mark.parametrize("namespace,code,expected", [
    ("XSHG", "600000", "600000.XSHG"),
    ("US", "AAPL", "AAPL.US"),
])
def test_both_markets_become_the_documented_panel(namespace, code, expected):
    """契约形状：`symbol_namespace` + `trading_code`，两个市场逐列同形。"""
    out = _panel([{"symbol_namespace": namespace, "trading_code": code,
                   "session_date": "2026-08-17", "close": 1.1}])
    assert list(out.index.names) == ["order_book_id", "datetime"]
    assert out.index.get_level_values("order_book_id").tolist() == [expected]
    assert "session_date" not in out.columns


def test_the_previous_cn_column_name_still_composes():
    """`exchange_id` 是 CN 上一版的列名：镜像回滚到旧 libfinanced 时还会出现。"""
    out = _panel([{"exchange_id": "XSHG", "trading_code": "600000",
                   "session_date": "2026-08-17", "close": 1.1}])
    assert out.index.get_level_values("order_book_id").tolist() == ["600000.XSHG"]


def test_a_composed_order_book_id_is_taken_as_is():
    """US 统一前给的就是整的一列，仍要拼成同一个面板。"""
    out = _panel([{"order_book_id": "AAPL.US", "session_date": "2026-08-17",
                   "close": 305.59}])
    assert list(out.index.names) == ["order_book_id", "datetime"]
    assert out.index.get_level_values("order_book_id").tolist() == ["AAPL.US"]


def test_an_unrecognised_shape_is_still_returned_as_is():
    """服务端换了形状就原样返回，让调用方看见真实的列，而不是在这里猜。"""
    pd = pytest.importorskip("pandas")
    out = _panel([{"something_else": 1, "close": 2.0}])
    assert isinstance(out, pd.DataFrame)
    assert "close" in out.columns
