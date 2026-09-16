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
