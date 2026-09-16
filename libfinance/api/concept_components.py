import datetime
import warnings
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, Iterable

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.cache import versioned_cache
from libfinance.utils.compat import renamed
from libfinance.utils.decorators import export_as_api

@export_as_api
@versioned_cache
def get_concept_meta(source: str = "THS", fields=None, market=None) -> pd.DataFrame:
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
    return get_client().get_concept_meta(source=source, fields=fields, market=market)

@export_as_api
def get_concept_weights(concept_ids: list, as_of=None, source: str = "THS",
                        market=None, **kwargs) -> pd.DataFrame:
    """
    获取某一个概念的成分股及其权重数据
    :param concept_ids: 概念id的列表
    :param as_of: 以该时点**已知**的成分为准；省略则取最新。旧名 ``date`` 仍可用，
                  但会发 DeprecationWarning。
    :param source: 来源(当前仅支持的同花顺(THS)这一来源的概念分类)
    :param market: 市场，省略则用服务端默认
        
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
    kwargs = renamed("date", "as_of", dict(kwargs, as_of=as_of), "get_concept_weights")
    _warn_unknown_concepts(concept_ids, source)
    return get_client().get_concept_weights(
        concept_ids=concept_ids, source=source, market=market, **kwargs)


def _warn_unknown_concepts(concept_ids, source):
    """概念 id 不存在时给一句警告，而不是静默返回空表。

    服务端对没见过的 id 只是返回 0 行 —— 从调用方看，"这个概念今天没有成分"和"这个
    id 根本不存在"长得一模一样。example 里那个 886074 就是失效 id，一直静默返回空。

    元信息表是版本化缓存的（get_concept_meta），所以这次检查不额外产生网络往返。
    查不到元信息时直接放行 —— 校验不该让查询失败。
    """
    try:
        meta = get_concept_meta(source=source)
        known = set(meta["concept_id"].astype(str))
    except Exception:
        return
    if not known:
        return
    missing = [str(c) for c in concept_ids if str(c) not in known]
    if missing:
        warnings.warn(
            "未知的 concept_id: {}（source={!r}）。用 get_concept_meta() 查可用的概念。"
            .format(", ".join(missing[:5]), source),
            stacklevel=3,
        )