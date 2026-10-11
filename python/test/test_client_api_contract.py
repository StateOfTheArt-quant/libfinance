#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""客户端 API 的签名契约。

这些是**静态**检查，不需要服务端。钉住的是几个曾经真的坏过的点。
"""
import inspect
import pathlib

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


def test_industry_defaults_mean_every_classification():
    """source / level 省略即全部分类体系、全部层级，不替用户选一个。

    曾经默认 source='010303'（旧数据源的申万编码），服务端不认，于是用默认参数调**一直是报错的**。
    现在分类体系由服务端的 industryconstituents 给出（SW、GICS……），不存在一个对所有市场都对的默认值。
    指数的发布机构、主题的定义方同理。
    """
    from libfinance.api.index_components import get_instrument_indices
    from libfinance.api.industry import get_instrument_industry
    from libfinance.api.theme import get_instrument_themes

    defaults = _defaults(get_instrument_industry)
    assert defaults["source"] is None and defaults["level"] is None and defaults["as_of"] is None
    for func in (get_instrument_indices, get_instrument_themes):
        assert _defaults(func)["source"] is None and _defaults(func)["as_of"] is None, func.__name__


def test_the_object_is_required_not_silently_defaulted():
    """按对象查的函数不替用户选对象：get_index_weights 曾经默认沪深300，拿错指数比报错更难发现。"""
    import libfinance

    for name in ("get_index_constituents", "get_index_weights", "get_industry_constituents",
                 "get_industry_weights", "get_theme_constituents", "get_theme_weights"):
        assert _defaults(getattr(libfinance, name))["order_book_id"] is inspect.Parameter.empty, name


def test_get_price_sends_the_codes_to_daybar_as_given(monkeypatch):
    """daybar 自己按 instrument 路由股票与指数：客户端不再查 all_instruments 分流，
    代码原样（去重、保序）交给服务端，由它按 end_date 解析。"""
    pd = pytest.importorskip("pandas")
    from libfinance.api import get_price as module

    calls = []

    class Client:
        def get_price(self, **kwargs):
            calls.append(kwargs)
            return pd.DataFrame([{"order_book_id": "000300.XSHG",
                                  "session_date": "2026-08-17", "close": 4000.0}])

        def __getattr__(self, name):
            raise AssertionError("get_price must not call {}".format(name))

    monkeypatch.setattr(module, "get_client", lambda: Client())
    monkeypatch.setattr(module, "warn_if_clamped", lambda *args: None)
    monkeypatch.setattr(module, "_warn_beyond_coverage", lambda *args: None)
    out = module.get_price(["600000.XSHG", "000300.XSHG", "600000.XSHG"], "2026-08-01", "2026-08-17",
                           fields="close", adjust_orig="2026-08-17")
    assert calls == [{"order_book_ids": ["600000.XSHG", "000300.XSHG"], "start_date": "2026-08-01",
                      "end_date": "2026-08-17", "frequency": "1d", "fields": ["close"],
                      "skip_suspended": False, "include_now": True, "adjust_type": "pre",
                      "adjust_orig": "2026-08-17"}]
    assert list(out.index.names) == ["order_book_id", "datetime"] and list(out.columns) == ["close"]


@pytest.mark.parametrize("kwargs,match", [
    ({"frequency": "1m"}, "frequency"),
    ({"adjust_type": "both"}, "adjust_type"),
    ({"skip_suspended": "yes"}, "skip_suspended"),
])
def test_get_price_refuses_what_daybar_does_not_publish(kwargs, match):
    from libfinance.api.get_price import get_price

    with pytest.raises(ValueError, match=match):
        get_price("600000.XSHG", "2026-08-01", "2026-08-17", **kwargs)


# ---------------------------------------------------------------------------
# 面板形状：daybar 的扁平表 -> (order_book_id, datetime)
# ---------------------------------------------------------------------------
def _panel(rows):
    pd = pytest.importorskip("pandas")
    from libfinance.api.get_price import _to_panel

    return _to_panel(pd.DataFrame(rows))


def test_daybar_rows_become_the_documented_panel():
    out = _panel([{"order_book_id": "AAPL.US", "session_date": "2026-08-18", "close": 2.0},
                  {"order_book_id": "000300.XSHG", "session_date": "2026-08-17", "close": 1.0},
                  {"order_book_id": "AAPL.US", "session_date": "2026-08-17", "close": 3.0}])
    assert list(out.index.names) == ["order_book_id", "datetime"]
    assert out.index.tolist()[0][0] == "000300.XSHG" and out.loc["AAPL.US"]["close"].tolist() == [3.0, 2.0]
    assert "session_date" not in out.columns


def test_an_unrecognised_shape_is_still_returned_as_is():
    """服务端换了形状就原样返回，让调用方看见真实的列，而不是在这里猜。"""
    pd = pytest.importorskip("pandas")
    out = _panel([{"something_else": 1, "close": 2.0}])
    assert isinstance(out, pd.DataFrame)
    assert "close" in out.columns


def test_get_price_coverage_is_by_type_and_venue(monkeypatch):
    """股票的 end 取复权价的上界（除权因子 cutoff 更早时取它），指数不复权，end 即 raw_end。"""
    from libfinance.api import get_price as module
    from libfinance.utils import cache

    venue = lambda start, end: {"coverage_start": start, "coverage_end": end}
    answers = {
        "daybar.coverage": {"stock": {"CN": {"XSHG": venue("2000-01-04", "2026-09-10")},
                                      "US": {"US": venue("2000-01-03", "2026-09-09")}},
                            "index": {"CN": {"XSHG": venue("2005-01-04", "2026-09-10")}}},
        "exfactor.coverage": {"market": "CN", "cutoff": "2026-09-08"},
    }
    calls = []

    class Client:
        def call(self, name, args):
            calls.append((name, args))
            return answers[name]

    monkeypatch.setattr(module, "get_client", lambda: Client())
    monkeypatch.setattr(cache, "current_data_version", lambda: "coverage-test")
    module.get_price_coverage.clear()
    try:
        assert module.get_price_coverage("cn") == {
            "stock": {"XSHG": {"start": "2000-01-04", "end": "2026-09-08", "raw_end": "2026-09-10",
                               "adjust_cutoff": "2026-09-08"}},
            "index": {"XSHG": {"start": "2005-01-04", "end": "2026-09-10", "raw_end": "2026-09-10"}},
        }
        assert calls == [("daybar.coverage", {"type": None}), ("exfactor.coverage", {"market": "CN"})]
    finally:
        module.get_price_coverage.clear()


def test_instruments_resolve_mixed_codes_in_input_order(monkeypatch):
    from libfinance.api import instrument

    calls = []

    class Client:
        def instruments(self, **kwargs):
            calls.append(kwargs)
            return [{"order_book_id": "600000.XSHG", "type": "stock", "market": "CN",
                     "name": "浦发银行", "exchange": "XSHG", "source": "XSHG"},
                    {"order_book_id": "AAPL.US", "type": "stock", "market": "US",
                     "name": "Apple", "exchange": "XNAS", "source": "XNAS"}]

    monkeypatch.setattr(instrument, "get_client", lambda: Client())
    assert "market" not in inspect.signature(instrument.instruments).parameters
    ids = ["AAPL.US", "MISSING.US", "600000.XSHG", "AAPL.US"]
    result = instrument.instruments(ids, as_of="2022-04-15", last_known=True)
    assert [item.order_book_id for item in result] == [ids[0], ids[2], ids[3]]
    assert [item.name for item in result] == ["Apple", "浦发银行", "Apple"]
    assert calls == [{"order_book_ids": ids, "as_of": "2022-04-15", "last_known": True}]
    assert instrument.instruments("600000.XSHG").name == "浦发银行"


def test_all_instruments_takes_the_backend_types_and_sources(monkeypatch):
    from libfinance.api import instrument

    calls = []

    class Client:
        def all_instruments(self, **kwargs):
            calls.append(kwargs)
            import pandas as pd
            return pd.DataFrame([{"type": "index", "order_book_id": "000300.XSHG"}])

    monkeypatch.setattr(instrument, "get_client", lambda: Client())
    out = instrument.all_instruments(type=["Index", "theme"], market="cn", source="CSI")
    assert calls == [{"type": ["index", "theme"], "market": "cn", "source": ["CSI"], "as_of": None}]
    assert list(out.columns)[0] == "order_book_id"
    with pytest.raises(ValueError, match="invalid type"):
        instrument.all_instruments(type="CS")


@pytest.mark.parametrize("name,kwargs,expected", [
    ("get_dividends", {"order_book_ids": ["600000.XSHG", "AAPL.US"], "as_of": "2024-07-01"},
     {"order_book_ids": ["600000.XSHG", "AAPL.US"], "as_of": "2024-07-01"}),
    ("get_splits", {"order_book_ids": "NVDA.US"}, {"order_book_ids": ["NVDA.US"]}),
    ("get_allotments", {"order_book_ids": "600000.XSHG"}, {"order_book_ids": ["600000.XSHG"]}),
    ("get_spinoffs", {"order_book_ids": "MMM.US"}, {"order_book_ids": ["MMM.US"]}),
    ("get_pit_financials_ex", {"order_book_ids": "600000.XSHG", "fields": ["net_income_parent"],
      "start_quarter": "2024q1", "end_quarter": "2024q3", "as_of": "2024-11-01"},
     {"order_book_ids": ["600000.XSHG"], "fields": ["net_income_parent"], "as_of": "2024-11-01"}),
    ("get_financial_metrics", {"order_book_ids": "600000.XSHG", "fields": "roe_lf",
      "start_date": "2024-11-01", "end_date": 20241105},
     {"order_book_ids": ["600000.XSHG"], "fields": ["roe_lf"], "start_date": "2024-11-01", "end_date": "2024-11-05"}),
    ("get_factor_exposure", {"order_book_ids": "600000.XSHG", "factor_names": "system/barra-cne5",
      "start_date": "2026-09-01", "end_date": 20260910},
     {"order_book_ids": ["600000.XSHG"], "factor_names": ["system/barra-cne5"], "start_date": "2026-09-01",
      "end_date": "2026-09-10", "universe": None}),
    ("get_instrument_industry", {"order_book_ids": ["600000.XSHG"], "level": 3, "as_of": "2024-06-28"},
     {"order_book_ids": ["600000.XSHG"], "level": 3, "as_of": "2024-06-28"}),
    ("get_instrument_indices", {"order_book_ids": "600000.XSHG", "source": "CSI"},
     {"order_book_ids": "600000.XSHG", "source": "CSI"}),
    ("get_instrument_themes", {"order_book_ids": ["600000.XSHG"], "as_of": "2024-06-28"},
     {"order_book_ids": ["600000.XSHG"], "as_of": "2024-06-28"}),
    ("get_index_weights", {"order_book_id": "000300.XSHG", "as_of": "2024-06-28"},
     {"order_book_id": "000300.XSHG", "as_of": "2024-06-28"}),
    ("get_theme_weights", {"order_book_id": "300900.THS"}, {"order_book_id": "300900.THS", "as_of": None}),
])
def test_code_queries_send_codes_without_market(monkeypatch, name, kwargs, expected):
    import importlib
    import libfinance
    import pandas as pd

    fn = getattr(libfinance, name)
    calls = []

    class Client:
        def __getattr__(self, method):
            def call(**arguments):
                assert method == name
                assert "market" not in arguments
                calls.append(arguments)
                return pd.DataFrame()
            return call

    module = importlib.import_module(fn.__module__)
    monkeypatch.setattr(module, "get_client", lambda: Client())
    assert "market" not in inspect.signature(fn).parameters
    fn(**kwargs)
    assert len(calls) == 1
    for key, value in expected.items():
        assert calls[0][key] == value
    with pytest.raises(TypeError):
        fn(**kwargs, market="cn")


@pytest.mark.parametrize("cached,market", [(True, None), (False, None), (True, "cn")])
def test_all_instruments_as_of_reaches_server_and_separates_snapshots(monkeypatch, cached, market):
    from datetime import date
    from libfinance.api import instrument
    from libfinance.utils import cache
    import pandas as pd

    calls = []

    class Client:
        def all_instruments(self, **kwargs):
            calls.append(kwargs)
            return pd.DataFrame([{"order_book_id": kwargs["as_of"] or "CURRENT"}])

    monkeypatch.setattr(instrument, "get_client", lambda: Client())
    monkeypatch.setattr(cache, "current_data_version", lambda: "pit-contract-test")
    instrument._all_instruments_cached.clear()
    try:
        for day in (date(2022, 4, 15), date(2024, 6, 28), None):
            result = instrument.all_instruments(as_of=day, market=market, cached=cached)
            expected = day.isoformat() if day else None
            assert calls[-1]["as_of"] == expected
            assert "date" not in calls[-1]
            assert result.iloc[0]["order_book_id"] == (expected or "CURRENT")
        assert len(calls) == 3
    finally:
        instrument._all_instruments_cached.clear()


def test_instrument_queries_expose_as_of_and_reject_retired_date():
    from libfinance.api import instrument

    for fn, args in [(instrument.all_instruments, ()), (instrument.instruments, ("AAPL.US",))]:
        assert "as_of" in inspect.signature(fn).parameters
        assert "date" not in inspect.signature(fn).parameters
        with pytest.raises(TypeError, match="date"):
            fn(*args, date="2022-04-15")


def test_exfactor_normalizes_dates_and_preserves_factor_table(monkeypatch):
    from datetime import date
    from libfinance.api import exfactor
    import pandas as pd

    calls = []
    expected = pd.DataFrame(
        {"order_book_id": ["AAPL.US"], "ex_factor": [1.01], "ex_cum_factor": [2.02]},
        index=pd.DatetimeIndex(["2023-08-11"], name="ex_date"))

    class Client:
        def get_ex_factor(self, **kwargs):
            calls.append(kwargs)
            return expected

    monkeypatch.setattr(exfactor, "get_client", lambda: Client())
    assert exfactor.get_ex_factor("AAPL.US", date(2023, 1, 1), date(2023, 12, 31)) is expected
    assert calls == [{"order_book_ids": ["AAPL.US"], "start_date": "2023-01-01", "end_date": "2023-12-31"}]
    with pytest.raises(ValueError):
        exfactor.get_ex_factor([])
    with pytest.raises(ValueError):
        exfactor.get_ex_factor("AAPL.US", "2024-01-01", "2023-01-01")
    with pytest.raises(TypeError):
        exfactor.get_ex_factor("AAPL.US", market="us")
    assert len(calls) == 1


def test_get_shares_takes_the_unified_fields_and_as_of(monkeypatch):
    """The backend publishes the unified fields for every market; the panel comes back flat and is
    indexed by (order_book_id, date) here."""
    from datetime import date
    import pandas as pd
    from libfinance.api import shares

    calls = []

    class Client:
        def get_shares(self, **kwargs):
            calls.append(kwargs)
            return pd.DataFrame([{"order_book_id": "600000.XSHG", "date": "2025-06-03", "issued_shares": 2.9e10}])

    monkeypatch.setattr(shares, "get_client", lambda: Client())
    out = shares.get_shares("600000.XSHG", "2025-06-01", "2025-06-30", fields="issued_shares", as_of=date(2025, 6, 30))
    assert calls == [{"order_book_ids": ["600000.XSHG"], "start_date": "2025-06-01", "end_date": "2025-06-30",
                      "fields": ["issued_shares"], "as_of": "2025-06-30"}]
    assert list(out.index.names) == ["order_book_id", "date"] and list(out.columns) == ["issued_shares"]
    with pytest.raises(ValueError):
        shares.get_shares("600000.XSHG", fields=["total"])


def test_as_of_keeps_a_timestamp(monkeypatch):
    import datetime
    from libfinance.utils.utils import as_of_text

    assert as_of_text(None) is None and as_of_text("2025-06-30") == "2025-06-30"
    assert as_of_text(datetime.date(2025, 6, 30)) == "2025-06-30"
    assert as_of_text(datetime.datetime(2025, 6, 30, 15, 0, tzinfo=datetime.timezone.utc)) == "2025-06-30T15:00:00+00:00"



def test_financial_frames_are_indexed_whichever_server_answers(monkeypatch):
    """The C++ server answers flat tables; the client indexes them by (order_book_id, date | quarter)."""
    import pandas as pd
    from libfinance.api import financials

    class Client:
        def get_financial_metrics(self, **kwargs):
            return pd.DataFrame([{"order_book_id": "B", "date": "2024-11-05", "roe_lf": 0.2},
                                 {"order_book_id": "A", "date": "2024-11-05", "roe_lf": 0.1}])

        def get_pit_financials_ex(self, **kwargs):
            return pd.DataFrame([{"order_book_id": "A", "quarter": "2024q1", "info_date": "2024-04-30",
                                  "assets": 1.0, "if_adjusted": 0}])

    monkeypatch.setattr(financials, "get_client", lambda: Client())
    metrics = financials.get_financial_metrics(["A", "B"], "roe_lf")
    assert metrics.index.names == ["order_book_id", "date"] and list(metrics.roe_lf) == [0.1, 0.2]
    pit = financials.get_pit_financials_ex("A", "assets", "2024q1", "2024q1")
    assert pit.index.names == ["order_book_id", "quarter"] and list(pit.columns) == ["info_date", "assets", "if_adjusted"]


def test_factor_exposure_is_indexed_and_says_when_the_tier_cuts_it(monkeypatch):
    """服务端回扁平表；客户端按 (order_book_id, date) 建索引、保持服务端的行序。免费层夹日期窗口、截断代码数时
    服务端不报错，客户端各给一句警告——否则"没数据"和"档位不够"分不出来。"""
    import pandas as pd
    from libfinance.api import factors
    from libfinance.utils import cache

    calls = []

    class Client:
        def get_factor_exposure(self, **kwargs):
            calls.append(kwargs)
            return pd.DataFrame([{"order_book_id": "B", "date": "2026-09-10", "system/barra-cne5/SIZE": 1.4},
                                 {"order_book_id": "A", "date": "2026-09-10", "system/barra-cne5/SIZE": 1.5}])

    monkeypatch.setattr(factors, "get_client", lambda: Client())
    monkeypatch.setattr(cache, "limits_for", lambda api: {"clamp_date_window": {"years": 1},
                                                          "clamp_instrument_count": {"max_count": 2}})
    with pytest.warns(UserWarning) as caught:
        frame = factors.get_factor_exposure(["B", "A", "C"], ["system/barra-cne5"], "2000-01-04", "2026-09-10",
                                            universe=["A", "B", "C"])
    messages = [str(w.message) for w in caught]
    assert any("可查区间的起点" in m for m in messages) and any("最多 2 个代码" in m for m in messages)
    assert calls[0]["universe"] == ["A", "B", "C"]
    assert frame.index.names == ["order_book_id", "date"]
    assert list(frame.index.get_level_values(0)) == ["B", "A"]
    assert list(frame.columns) == ["system/barra-cne5/SIZE"]
    with pytest.raises(ValueError, match="after end_date"):
        factors.get_factor_exposure("A", "system/qlib", "2026-09-10", "2026-09-01")
    with pytest.raises(ValueError, match="factor_names"):
        factors.get_factor_exposure("A", [], "2026-09-10", "2026-09-10")


def test_factor_listings(monkeypatch):
    from libfinance.api import factors

    class Client:
        def list_factor_libraries(self):
            return [{"name": "system/barra-cne5", "version": "v2.0.0", "factors": 42, "description": ""}]

        def list_factors(self, library=None):
            return ["system/barra-cne5/SIZE"] if library == "system/barra-cne5" else []

    monkeypatch.setattr(factors, "get_client", lambda: Client())
    libraries = factors.list_factor_libraries()
    assert list(libraries.columns) == ["name", "version", "factors", "description"]
    assert libraries.factors.tolist() == [42]
    assert factors.list_factors("system/barra-cne5") == ["system/barra-cne5/SIZE"]
