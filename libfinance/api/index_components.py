#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
def get_index_weights(index_id: str = "000300.XSHG", date: Union[str, datetime.datetime] = None) -> pd.DataFrame:
    """
    获取特定日期,指数成分股及其权重数据
    
    :param index_id: 指数的id
    :param date: 日期(当前仅支持的同花顺(THS)这一来源的概念分类)
        
    :example:
    
    ..  code-block:: python3
    
        from libfinance import get_index_weights
    
        >>> index_weight = get_index_weights(index_id="000300.XSHG", date="2022-07-20")       
        >>> print(index_weight)
        
                       index_order_book_id index_name  ... order_book_name    weight
       datetime                                   ...                          
       2022-07-20         000300.XSHG      沪深300  ...            歌尔股份  0.003813
       2022-07-20         000300.XSHG      沪深300  ...            新城控股  0.000934
       2022-07-20         000300.XSHG      沪深300  ...             凯莱英  0.001957
       2022-07-20         000300.XSHG      沪深300  ...            华侨城A  0.001139
       2022-07-20         000300.XSHG      沪深300  ...            特变电工  0.005060
                           ...        ...  ...             ...       ...
       2022-07-20         000300.XSHG      沪深300  ...            晶盛机电  0.002218
       2022-07-20         000300.XSHG      沪深300  ...            华能国际  0.001589
       2022-07-20         000300.XSHG      沪深300  ...            京东方A  0.007253
       2022-07-20         000300.XSHG      沪深300  ...            海尔智家  0.004762
       2022-07-20         000300.XSHG      沪深300  ...            澜起科技  0.001217

       [300 rows x 5 columns]

    """
    return get_client().get_index_weights(index_id=index_id, date = date)
    

