#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""指数的成分与权重。

指数以 ``order_book_id``\ （``000300.XSHG``、``SPX.US``）命名，规则与证券相同；指数目录是
``all_instruments(type="index")``\ 。按指数查成分与权重，按证券查所属指数。
"""
from typing import List, Optional

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_string


def _as_of(as_of):
    return to_date_str(as_of) if as_of is not None else None


@export_as_api
def get_index_constituents(order_book_id: str, as_of=None) -> Optional[List[str]]:
    r"""获取指数在指定日期的成分证券。

    :param order_book_id: 指数代码，如 ``"000300.XSHG"``\ （沪深300）、``"SPX.US"``
    :param as_of: 那一天的事实；省略则取指数已确认的最新日期
    :returns: list[str]，成分证券的 ``order_book_id``\ ；没有市场发布该指数时为 ``None``\ 。
    """
    order_book_id = ensure_string(order_book_id, "order_book_id")
    return get_client().get_index_constituents(order_book_id=order_book_id, as_of=_as_of(as_of))


@export_as_api
def get_instrument_indices(order_book_ids, source: Optional[str] = None, as_of=None) -> pd.DataFrame:
    r"""查询证券在指定日期所属的指数。

    :param order_book_ids: 证券代码列表（单个代码也可以），代码自己确定市场
    :param source: 指数发布机构，如 ``"CSI"``\ 、``"SPDJI"``\ ；省略则返回全部发布机构
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: pandas.DataFrame，包含 order_book_id、related_order_book_id（指数代码）、source、market 和 level。
    """
    return get_client().get_instrument_indices(
        order_book_ids=order_book_ids, source=source, as_of=_as_of(as_of))


@export_as_api
def get_index_weights(order_book_id: str, as_of=None) -> pd.DataFrame:
    r"""获取指数在指定日期的成分权重。

    :param order_book_id: 指数代码，如 ``"000300.XSHG"``
    :param as_of: 那一天的事实；省略则取指数已确认的最新日期
    :returns: pandas.DataFrame，包含 order_book_id（成分证券）、weight、methodology、source（指数发布机构）、
        basis（origin 数据源发布 / reconstructed 按编制方法重构）、date（权重所在的日子）、quality_flags。
        权重是月末快照：其余交易日取之前最近一期、按各成分的复权收益率漂移，date 为 as_of，quality_flags 带 DRIFTED。
    """
    order_book_id = ensure_string(order_book_id, "order_book_id")
    return get_client().get_index_weights(order_book_id=order_book_id, as_of=_as_of(as_of))
