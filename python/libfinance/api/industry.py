#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""行业分类。

``get_instrument_industry``\ （按证券查行业）在 index_components 里，这里是反向的两个：
按行业查成分、以及取整张分类表。
"""
from typing import Optional

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_string

DEFAULT_SOURCE = "sw"


@export_as_api
def get_industry(
    industry: str,
    source: str = DEFAULT_SOURCE,
    date=None,
    market: Optional[str] = None,
):
    r"""获取某个行业下的全部证券。

    :param industry: 行业代码或名称
    :param source: 分类来源，默认 ``"sw"``\ （申万）
    :param date: 以该日的分类为准，省略则取最新
    :param market: 市场，省略则用服务端默认

    :returns: list[str]，属于指定行业的证券代码列表。
    """
    industry = ensure_string(industry, "industry")
    return get_client().get_industry(
        industry=industry, source=source,
        date=to_date_str(date) if date is not None else None,
        market=market,
    )


@export_as_api
def get_industry_mapping(
    source: str = DEFAULT_SOURCE,
    date=None,
    market: Optional[str] = None,
) -> pd.DataFrame:
    r"""获取整张行业分类表（行业代码、名称、层级）。

    :param source: 分类来源，默认 ``"sw"``\ （申万）
    :param date: 以该日的分类为准，省略则取最新
    :param market: 市场，省略则用服务端默认

    :returns: pandas.DataFrame，包含行业代码、名称和层级。
    """
    return get_client().get_industry_mapping(
        source=source,
        date=to_date_str(date) if date is not None else None,
        market=market,
    )
