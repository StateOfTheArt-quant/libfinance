#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""证券目录：股票、指数、行业、主题在同一个 instrument 聚合包后面。

签名与列名取自后端 instrument 数据族（\ ``instrument.all_instruments`` /
``instrument.instruments``\ ），本模块只做参数检查、按数据版本缓存与结果的形状。

* ``order_book_id`` 是代码（\ ``600000.XSHG``\ 、\ ``000300.XSHG``\ 、\ ``AAPL.US``\ ），也是客户端唯一的证券标识；
  ``name`` 是名称。
* ``type`` 取 ``stock`` / ``index`` / ``industry`` / ``theme``\ 。
* ``source`` 是定义并编号证券的机构：股票的交易所（XSHG、XNAS）、指数的发布机构
  （CSI、SPDJI）、行业的分类体系（SW、GICS）、主题的 THS；\ ``exchange`` 只有股票有。
"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.cache import versioned_cache
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_list_of_string

#: 后端 instrument 认得的类型。
VALID_TYPES = ("stock", "index", "industry", "theme")

#: all_instruments 的列，按后端的顺序。
COLUMNS = ("order_book_id", "type", "market", "name", "exchange", "source")


class Instrument(object):
    """一只证券。属性名就是 :func:`~libfinance.all_instruments` 的列名。"""

    def __init__(self, d):
        self.__dict__ = dict(d)

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                "{}={!r}".format(k, v)
                for k, v in self.__dict__.items()
                if v is not None and not (isinstance(v, float) and pd.isna(v))
            ),
        )


def _normalize_types(type_):
    if type_ is None:
        return None
    out = []
    for item in ensure_list_of_string(type_, "type"):
        value = item.lower()
        if value not in VALID_TYPES:
            raise ValueError("invalid type: {!r}, choose any in {}".format(item, list(VALID_TYPES)))
        out.append(value)
    return out


def _optional_strings(value, name):
    return None if value is None else ensure_list_of_string(value, name)


def _order_book_id_first(frame):
    if not isinstance(frame, pd.DataFrame) or frame.empty or "order_book_id" not in frame.columns:
        return frame
    return frame[["order_book_id"] + [c for c in frame.columns if c != "order_book_id"]]


@versioned_cache
def _all_instruments_cached(types, sources, as_of):
    r"""全表，按\ **数据版本**\ 缓存（见 utils/cache.py）：数据版本不变，答案就不变。"""
    return _order_book_id_first(get_client().all_instruments(
        type=list(types) if types else None, source=list(sources) if sources else None, as_of=as_of))


@export_as_api
def all_instruments(
    type: Optional[Union[str, List[str]]] = None,
    market: Optional[str] = None,
    source: Optional[Union[str, List[str]]] = None,
    as_of=None,
    cached: bool = True,
) -> pd.DataFrame:
    r"""获取证券目录：全部类型，或指定类型、市场、编号机构的证券。

    :param type: ``"stock"`` / ``"index"`` / ``"industry"`` / ``"theme"``\ ，或它们的列表；省略为全部类型。
    :param market: 市场，如 ``"cn"`` / ``"us"``\ ；省略为全部市场。
    :param source: 编号机构，如 ``"XSHG"``\ 、\ ``"CSI"``\ 、\ ``"SW"``\ ，或它们的列表；省略为全部。
    :param as_of: 给出则为该日的历史视图；省略时各类型取各自的当前状态。某类型不覆盖的日期
        报 CoverageError 并写明类型，缩小 ``type`` 或 ``source`` 即可。
    :param cached: 是否使用按服务端数据版本更新的缓存；显式指定市场时直接查询。
    :returns: DataFrame，列为 ``order_book_id, type, market, name, exchange, source``\ 。
    """
    types = _normalize_types(type)
    sources = _optional_strings(source, "source")
    as_of = to_date_str(as_of) if as_of is not None else None
    if cached and market is None:
        return _all_instruments_cached(tuple(types) if types else None,
                                       tuple(sources) if sources else None, as_of)
    return _order_book_id_first(get_client().all_instruments(type=types, market=market, source=sources,
                                                             as_of=as_of))


@export_as_api
def instruments(
    order_book_ids: Union[str, List[str]],
    as_of=None,
    last_known: bool = False,
):
    r"""按代码解析证券，类型由代码本身决定。

    :param order_book_ids: 单个代码或跨市场、跨类型的代码列表，如 ``"000001.XSHE"``\ 、\ ``"000300.XSHG"``\ 。
    :param as_of: 按该日有效的代码解析；省略时各类型取各自的当前状态。
    :param last_known: 为 True 时，\ ``as_of`` 当日已终止上市的股票或指数代码按它最后一次的证券解析
        （行业、主题节点没有上市可回退）。
    :returns: 传入单个代码时返回一个 :class:`~libfinance.api.instrument.Instrument`\ （查不到则返回 ``None``\ ）；
              传入列表时按传入顺序返回 :class:`~libfinance.api.instrument.Instrument` 列表，查不到的代码会被跳过。
              两种类型同一天都认这个代码时报 AmbiguousInstrumentError。
    """
    single = isinstance(order_book_ids, str)
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    if not isinstance(last_known, bool):
        raise ValueError("last_known: a bool expected, got {!r}".format(last_known))
    as_of = to_date_str(as_of) if as_of is not None else None
    found = get_client().instruments(order_book_ids=ids, as_of=as_of, last_known=last_known) or []
    by_id = {item["order_book_id"]: Instrument(item) for item in found}
    if single:
        return by_id.get(ids[0])
    return [by_id[i] for i in ids if i in by_id]
