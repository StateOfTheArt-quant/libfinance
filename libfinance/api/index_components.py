import datetime
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, Iterable

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

@export_as_api
def get_instrument_industry(order_book_ids: list, date=None, source: str = "sw",
                            level: int = 1, market=None) -> pd.DataFrame:
    r"""
    获取股票合约的所属行业信息
    
    :param order_book_ids: 股票合约的id列表
    :param date: 以该日的分类为准；省略则取最新
    :param source: 分类来源。\ **当前服务端只支持 ``"sw"``\ （申万）** —— 用
                   ``get_industry_mapping()`` 看这一份分类表的全貌。

                   此前这里的默认值是 ``"010303"``\ ，那是旧数据源的申万分类编码，
                   服务端不认（\ ``unsupported source: 010303; available: sw``\ ），
                   所以这个接口用默认参数调一直是报错的。
    :param level: 行业层级，1/2/3，默认 1（一级行业）
    :param market: 市场，省略则用服务端默认
        
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
    return get_client().get_instrument_industry(
        order_book_ids=order_book_ids, source=source, level=level, date=date, market=market)

@export_as_api
def get_index_weights(
    index_code: str,
    date: Union[str, datetime.datetime] = None,
    market: str = None,
) -> pd.DataFrame:
    r"""
    获取指数在\ **任意交易日**\ 的成分股及其权重

    上游 index-weight 是月频锚点快照，只在锚点日有数据。非锚点日的权重由服务端取
    <= date 的最近一期锚点，按各成分从锚点日到 date 的\ **复权**\ 收益率重新加权并归一
    （用复权价是必须的：区间内有送转/拆股时，原始价的涨跌幅会把股本变动误读成收益）。

    :param index_code: 指数代码。旧参数名 ``index_id`` 已改名——服务端的能力声明用的是
        ``index_code``\ ，继续传 ``index_id`` 会被拒绝为"未知参数"。
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
       ``order_book_id`` / ``weight``\ ，不再带 ``index_name`` 与 ``order_book_name``\ 。
       名称属于证券主数据，用 ``instruments()`` 另取。
    """
    return get_client().get_index_weights(index_code=index_code, date=date, market=market)