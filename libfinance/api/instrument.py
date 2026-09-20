#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""证券基础信息。

对外契约：\ ``order_book_id`` 是代码（\ ``600000.XSHG``\ ），\ ``symbol`` 是名称（浦发银行）
—— 与 rqdata 一致。

翻译在\ **服务端的能力层**\ 做，不在这里：libfinanced 内部按 instrument spec 用
``symbol`` 表示代码、\ ``display_name`` 表示名称，那套三层身份模型不动；服务端在对外
边界上改名。这样直连 RPC 的人和用本客户端的人看到同一套名字。
"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.cache import versioned_cache
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_list_of_string

#: 服务端 all_instruments 认得的 type。传别的会被服务端拒绝。
VALID_TYPES = ("CS", "INDX")

#: 常用别名，历史上一直支持。
_TYPE_ALIASES = {"STOCK": "CS", "INDEX": "INDX"}


class Instrument(object):
    """一只证券的详细信息。属性名与 DataFrame 的列名一致。"""

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

    def has_citics_info(self):
        return self.type == "CS" and str(self.order_book_id).endswith((".XSHE", ".XSHG"))


def _normalize_types(type_):
    if type_ is None:
        return None
    values = ensure_list_of_string(type_, "type")
    out = []
    for item in values:
        upper = item.upper()
        upper = _TYPE_ALIASES.get(upper, upper)
        if upper not in VALID_TYPES:
            raise ValueError(
                "invalid type: {!r}, choose any in {}".format(item, list(VALID_TYPES))
            )
        out.append(upper)
    return out


def _rename(frame):
    """把 order_book_id 放在第一列。**列名不再在这里翻译。**

    服务端的能力层现在直接输出对外契约的列名（order_book_id = 代码，symbol = 名称），
    所以客户端退化成纯透传。此前这里有一份 {symbol: order_book_id,
    display_name: symbol} 的别名表 —— 那意味着直连 RPC 的人拿到的是另一套名字，
    而他们手上没有这张表。边界应该只有一处，在服务端。
    """
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return frame
    if "order_book_id" in frame.columns:
        ordered = ["order_book_id"] + [c for c in frame.columns if c != "order_book_id"]
        return frame[ordered]
    return frame


@versioned_cache
def _all_instruments_cached(type_key, as_of):
    """全表。按**数据版本**缓存，不是按时间 —— 见 utils/cache.py。

    这张表是 get_price 的前置：它要先知道每个代码是股票还是指数才能分流。实测一次
    75 ms / 14 rps，不缓存的话每次 get_price 都额外背一次重查询，而单个用户的限额
    （20 rps）就能把服务端打满。
    """
    types = list(type_key) if type_key else None
    return _rename(get_client().all_instruments(type=types, as_of=as_of))


@versioned_cache
def _obid_to_type(as_of=None):
    """``{order_book_id: type}``。get_price 分流标的时每次都要。

    建在 _all_instruments_cached 上，所以两者共享同一次网络往返。
    """
    frame = _all_instruments_cached(None, as_of)
    if frame is None or frame.empty:
        return {}
    return dict(zip(frame["order_book_id"], frame["type"]))


@versioned_cache
def _instrument_index(as_of=None):
    """``{order_book_id: Instrument}``。"""
    frame = _all_instruments_cached(None, as_of)
    if frame is None or frame.empty:
        return {}
    return {row["order_book_id"]: Instrument(row) for row in frame.to_dict("records")}


def all_cached_obid_to_type_mapping(as_of=None):
    """代码 → 类型。**validators.ensure_instruments 依赖这个名字。**

    它曾经是 get_all_obid_to_type() 这个 RPC 的薄封装，而服务端早已没有那个 handler
    （Function not found）。现在从 all_instruments 的全表推导，语义不变。
    """
    return _obid_to_type(to_date_str(as_of) if as_of else None)


def _get_instrument(type_, order_book_id, as_of=None):
    """**validators.ensure_instruments 依赖这个名字。**

    ``type_`` 保留在签名里只为兼容旧调用点；索引是按 order_book_id 建的，代码本身
    已经唯一，不需要先知道类型。
    """
    return _instrument_index(to_date_str(as_of) if as_of else None)[order_book_id]


@export_as_api
def all_instruments(
    type: Optional[Union[str, List[str]]] = None,
    date=None,
    market: Optional[str] = None,
    cached: bool = True,
) -> pd.DataFrame:
    r"""获取全部证券的基础信息。

    :param type: ``"CS"``\ （股票）或 ``"INDX"``\ （指数），也接受 ``"STOCK"`` / ``"INDEX"``
                 这两个别名；可以是列表。省略则返回全部。
    :param date: 以该日为准的快照（服务端参数名是 ``as_of``\ ）。省略则取最新。
    :param market: 市场，如 ``"cn"`` / ``"us"``；省略则合并服务端已绑定市场。
    :param cached: 是否使用按服务端数据版本更新的缓存；显式指定市场时直接查询。
    :returns: 以 ``order_book_id`` 打头的 DataFrame。
    """
    types = _normalize_types(type)
    as_of = to_date_str(date) if date is not None else None
    if cached and market is None:
        return _all_instruments_cached(tuple(types) if types else None, as_of)
    return _rename(get_client().all_instruments(type=types, as_of=as_of, market=market))


@export_as_api
def instruments(
    order_book_ids: Union[str, List[str]],
    date=None,
):
    r"""获取指定证券的详细信息。

    :param order_book_ids: 单个代码或跨市场代码列表，无需指定市场，如 ``"000001.XSHE"``\ 。
    :param date: 以该日为准的快照（服务端参数名是 ``as_of``\ ）。
    :returns: 传入单个代码时返回一个 :class:`~libfinance.api.instrument.Instrument`\ （查不到则返回 ``None``\ ）；
              传入列表时返回 :class:`~libfinance.api.instrument.Instrument` 列表，查不到的代码会被跳过。
    """
    single = isinstance(order_book_ids, str)
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")

    as_of = to_date_str(date) if date is not None else None
    frame = _rename(
        get_client().instruments(symbols=ids, as_of=as_of)
    )
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None if single else []

    found = [Instrument(row) for row in frame.to_dict("records")]
    if single:
        return found[0] if found else None
    # 按传入顺序返回，查不到的跳过 —— 与旧行为一致。
    by_id = {item.order_book_id: item for item in found}
    return [by_id[i] for i in ids if i in by_id]
