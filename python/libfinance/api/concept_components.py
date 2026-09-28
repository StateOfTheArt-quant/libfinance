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
    r"""获取概念目录，用于发现概念名称与有效编号。

    :param source: 概念分类来源，当前使用 ``"THS"``\ （同花顺）
    :param fields: 返回字段列表；省略返回全部字段
    :param market: 市场，省略交由服务端选择
    :returns: DataFrame；常用列为 ``concept_id``\ 、``concept_name``\ 。
    """
    return get_client().get_concept_meta(source=source, fields=fields, market=market)

@export_as_api
def get_concept_weights(concept_ids: list, as_of=None, source: str = "THS",
                        market=None, **kwargs) -> pd.DataFrame:
    r"""获取一个或多个概念的成分股及权重。

    :param concept_ids: 概念编号列表，从 :func:`get_concept_meta` 的目录取得
    :param as_of: 只使用截至该时点已知的信息；省略取最新。
        旧参数名 ``date`` 仍兼容，但会发出 DeprecationWarning
    :param source: 概念分类来源，当前使用 ``"THS"``\ （同花顺）
    :param market: 市场，省略交由服务端选择
    :returns: 成分权重 DataFrame。用 ``concept_id`` 区分不同概念，
        ``order_book_id`` 标识成分证券，``weight`` 为权重比例。
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