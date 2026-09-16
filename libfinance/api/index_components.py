import datetime
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, Iterable

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

@export_as_api
def get_instrument_industry(order_book_ids: list, date: Union[str, datetime.datetime], source: str = "010303") -> pd.DataFrame:
    """
    获取股票合约的所属行业信息
    
    :param order_book_ids: 股票合约的id列表
    :param date: 日期
    :param source: 来源(010303-申万行业分类, 010314-中证行业分类（2016版),010321-申万行业分类（2021版), 010317-中信行业分类)
        
    :example:
    
    ..  code-block:: python3
    
        from libfinance import get_instrument_industry
    
        >>> order_book_ids = ["000001.XSHE","600000.XSHG"]
        >>> instrument_industry = get_instrument_industry(order_book_ids=order_book_ids, date="2022-09-20")        
        >>> print(instrument_industry)
        
                          industry      industryID1     industryName1  industryID2 industryName2
        order_book_id                                                               
        000001.XSHE     申万行业分类      1030321            银行    103032101            银行
        600000.XSHG     申万行业分类      1030321            银行    103032101            银行

    """
    return get_client().get_instrument_industry(order_book_ids=order_book_ids, date=date, source=source)

@export_as_api
def get_index_weights(
    index_code: str = "000300.XSHG",
    date: Union[str, datetime.datetime] = None,
    market: str = "cn",
) -> pd.DataFrame:
    """
    获取指数在**任意交易日**的成分股及其权重

    上游 index-weight 是月频锚点快照，只在锚点日有数据。非锚点日的权重由服务端取
    <= date 的最近一期锚点，按各成分从锚点日到 date 的**复权**收益率重新加权并归一
    （用复权价是必须的：区间内有送转/拆股时，原始价的涨跌幅会把股本变动误读成收益）。

    :param index_code: 指数代码。旧参数名 ``index_id`` 已改名——服务端的能力声明用的是
        ``index_code``，继续传 ``index_id`` 会被拒绝为"未知参数"。
    :param date: 日期；省略则取最新一期锚点
    :param market: 市场，cn（默认）

    :example:

    ..  code-block:: python3

        from libfinance import get_index_weights

        >>> get_index_weights(index_code="000300.XSHG", date="2022-07-20")
            index_code       date order_book_id    weight
        0  000300.XSHG 2022-07-20   002241.XSHE  0.003813
        1  000300.XSHG 2022-07-20   601155.XSHG  0.000934
        ...

    .. note::
       返回形状与改造前不同：现在是四列 ``index_code`` / ``date`` /
       ``order_book_id`` / ``weight``，不再带 ``index_name`` 与 ``order_book_name``。
       名称属于证券主数据，用 ``instruments()`` 另取。
    """
    return get_client().get_index_weights(index_code=index_code, date=date, market=market)