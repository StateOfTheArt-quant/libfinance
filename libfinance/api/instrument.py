#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证券基础信息。

**字段命名在这里做了一次翻译，不是笔误。** 服务端的列名与本客户端的历史约定相反：

    服务端 symbol        = "000001.XSHE"  代码   -> 客户端 order_book_id
    服务端 display_name  = "平安银行"      名称   -> 客户端 symbol

客户端这套叫法是既有公开契约（example/application 里就有
``concept_weight.set_index('order_book_id')['symbol']`` 取名称的写法），所以翻译放在
这一层，不去动服务端，也不让用户承担这个差异。
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

#: 服务端列名 -> 客户端列名。只翻译有冲突的两个，其余原样透出。
_COLUMN_ALIASES = {"symbol": "order_book_id", "display_name": "symbol"}

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
    """把服务端列名翻译成客户端约定，并把 order_book_id 放在第一列。"""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return frame
    renamed = frame.rename(columns=_COLUMN_ALIASES)
    if "order_book_id" in renamed.columns:
        ordered = ["order_book_id"] + [c for c in renamed.columns if c != "order_book_id"]
        renamed = renamed[ordered]
    return renamed


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
    """获取全部证券的基础信息。

    :param type: ``"CS"``（股票）或 ``"INDX"``（指数），也接受 ``"STOCK"`` / ``"INDEX"``
                 这两个别名；可以是列表。省略则返回全部。
    :param date: 以该日为准的快照（服务端参数名是 ``as_of``）。省略则取最新。
    :param market: 市场，省略则用服务端默认。
    :param cached: 是否使用本地 3 小时缓存。基础信息变动很慢，默认开。
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
    market: Optional[str] = None,
):
    """获取指定证券的详细信息。

    :param order_book_ids: 单个代码或代码列表，如 ``"000001.XSHE"``。
    :param date: 以该日为准的快照（服务端参数名是 ``as_of``）。
    :param market: 市场，省略则用服务端默认。
    :returns: 传入单个代码时返回一个 :class:`Instrument`（查不到则返回 ``None``）；
              传入列表时返回 :class:`Instrument` 列表，查不到的代码会被跳过。
    """
    single = isinstance(order_book_ids, str)
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")

    as_of = to_date_str(date) if date is not None else None
    frame = _rename(
        get_client().instruments(symbols=ids, as_of=as_of, market=market)
    )
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None if single else []

    found = [Instrument(row) for row in frame.to_dict("records")]
    if single:
        return found[0] if found else None
    # 按传入顺序返回，查不到的跳过 —— 与旧行为一致。
    by_id = {item.order_book_id: item for item in found}
    return [by_id[i] for i in ids if i in by_id]
