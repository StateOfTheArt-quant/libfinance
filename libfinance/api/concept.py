#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, Iterable

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

@export_as_api
def get_concept_meta(source:str="THS") -> pd.DataFrame:
    """
    获取某个数据源的概念分类的元信息
    
    :param source: 来源(当前仅支持的同花顺(THS)这一来源的概念分类)
        
    :example:
    
    ..  code-block:: python3
    
        from libfinance import get_concept_meta
    
        >>> concept_meta = get_concept_meta(source="THS")
        >>> print(>>>)
        
             datetime        concept_name     component_number    concept_id source
        0    2024-03-25         AI语料            25.0             309126    THS
        1    2024-03-20       铜缆高速连接        24.0             309125    THS
        2    2024-03-12        高股息精选         327.0            309124    THS
        3    2024-03-04        AI PC              13.0             309121    THS
        4    2024-03-04         AI手机            19.0             309120    THS
        ..          ...          ...               ...               ...    ...
        402  2000-01-01       京津冀一体化        NaN              300061    THS
        403  2000-01-01           流感            NaN              300038    THS
        404  2000-01-01         苹果概念          NaN              300309    THS
        405  2000-01-01        PM2.5              NaN              300134    THS
        406  2000-01-01          石墨烯           NaN              300337    THS
    """   
    return get_client().get_concept_meta(source=source)

@export_as_api
def get_concept_weights(concept_ids:list, source:str="THS") -> pd.DataFrame:
    """
    获取某一个概念的成分股及其权重数据
    :param concept_ids: 概念id的列表
    :param source: 来源(当前仅支持的同花顺(THS)这一来源的概念分类)
        
    :example:
        
    .. code-block:: python
    
        from libfinance import get_concept_weights
    
        >>> concept_weight = get_concept_weights(concept_ids=["309126"], source="THS")
        >>> print(concept_weight)
       
            order_book_id instrument_name  weight  ... source update_date concept_name
        0    002908.XSHE            德生科技    0.04  ...    THS  2024-04-01         AI语料
        1    300133.XSHE            华策影视    0.04  ...    THS  2024-04-01         AI语料
        2    002226.XSHE            江南化工    0.04  ...    THS  2024-04-01         AI语料
        3    300766.XSHE            每日互动    0.04  ...    THS  2024-04-01         AI语料
        4    002649.XSHE            博彦科技    0.04  ...    THS  2024-04-01         AI语料
        5    600728.XSHG            佳都科技    0.04  ...    THS  2024-04-01         AI语料
        6    600100.XSHG            同方股份    0.04  ...    THS  2024-04-01         AI语料
        7    000710.XSHE            贝瑞基因    0.04  ...    THS  2024-04-01         AI语料
        8    688590.XSHG            新致软件    0.04  ...    THS  2024-04-01         AI语料
        9    603000.XSHG             人民网    0.04  ...    THS  2024-04-01         AI语料
        10   300033.XSHE             同花顺    0.04  ...    THS  2024-04-01         AI语料
        11   002362.XSHE            汉王科技    0.04  ...    THS  2024-04-01         AI语料
        12   000681.XSHE            视觉中国    0.04  ...    THS  2024-04-01         AI语料
        13   300166.XSHE            东方国信    0.04  ...    THS  2024-04-01         AI语料
        14   002230.XSHE            科大讯飞    0.04  ...    THS  2024-04-01         AI语料
        15   300182.XSHE            捷成股份    0.04  ...    THS  2024-04-01         AI语料
        16   300418.XSHE            昆仑万维    0.04  ...    THS  2024-04-01         AI语料
        17   688787.XSHG            海天瑞声    0.04  ...    THS  2024-04-01         AI语料
        18   300229.XSHE             拓尔思    0.04  ...    THS  2024-04-01         AI语料
        19   601858.XSHG            中国科传    0.04  ...    THS  2024-04-01         AI语料
        20   300785.XSHE             值得买    0.04  ...    THS  2024-04-01         AI语料
        21   300654.XSHE            世纪天鸿    0.04  ...    THS  2024-04-01         AI语料
        22   300364.XSHE            中文在线    0.04  ...    THS  2024-04-01         AI语料
        23   603721.XSHG            中广天择    0.04  ...    THS  2024-04-01         AI语料
        24   603533.XSHG            掌阅科技    0.04  ...    THS  2024-04-01         AI语料
        
        [25 rows x 7 columns]
    """
    return get_client().get_concept_weights(concept_ids=concept_ids, source = source)
    
