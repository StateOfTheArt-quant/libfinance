import datetime
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, Iterable

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm
from libfinance.utils.utils import to_date_str

@export_as_api
def get_instrument_industry(order_book_ids: list, source: Optional[str] = None, level: Optional[int] = None,
                            as_of=None) -> pd.DataFrame:
    r"""查询证券在指定日期所属的行业。

    :param order_book_ids: 证券代码列表（单个代码也可以），代码自己确定市场
    :param source: 分类体系，如 ``"SW"``\ （申万）、``"GICS"``\ ；省略则返回全部分类体系
    :param level: 分类层级（申万 1、2、3）；省略则返回全部层级
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: pandas.DataFrame，包含 order_book_id、related_order_book_id（行业代码，如 ``801780.SW``\ ）、
              source、market 和 level。
    """
    return get_client().get_instrument_industry(
        order_book_ids=order_book_ids, source=source, level=level,
        as_of=to_date_str(as_of) if as_of is not None else None)

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