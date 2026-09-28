import datetime
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, Iterable

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

@export_as_api
def get_instrument_industry(order_book_ids: list, date=None, source: str = "sw",
                            level: int = 1) -> pd.DataFrame:
    r"""查询股票在指定日期的行业归属。

    :param order_book_ids: 股票代码列表
    :param date: 分类日期；省略取最新
    :param source: 行业分类来源，当前支持 ``"sw"``\ （申万）
    :param level: 分类层级，1、2 或 3；默认 1
    :returns: 股票与行业归属的 DataFrame。
    """
    return get_client().get_instrument_industry(
        order_book_ids=order_book_ids, source=source, level=level, date=date)

@export_as_api
def get_index_weights(
    index_code: str,
    date: Union[str, datetime.datetime] = None,
) -> pd.DataFrame:
    r"""获取指数在\ **任意交易日**\ 的成分股及其权重

    上游 index-weight 是月频锚点快照，只在锚点日有数据。非锚点日的权重由服务端取
    <= date 的最近一期锚点，按各成分从锚点日到 date 的\ **复权**\ 收益率重新加权并归一
    （用复权价是必须的：区间内有送转/拆股时，原始价的涨跌幅会把股本变动误读成收益）。

    :param index_code: 指数代码。旧参数名 ``index_id`` 已改名——服务端的能力声明用的是
        ``index_code``\ ，继续传 ``index_id`` 会被拒绝为"未知参数"。
    :param date: 日期；省略则取最新一期锚点

    :returns: pandas.DataFrame，包含 index_code、date、order_book_id 和 weight；weight 为比例。
    """
    return get_client().get_index_weights(index_code=index_code, date=date)