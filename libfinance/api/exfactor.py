"""按证券代码查询逐除权日的复权因子。"""
from typing import List, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_list_of_string


@export_as_api
def get_ex_factor(
    order_book_ids: Union[str, List[str]],
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    r"""获取逐除权日的复权因子，支持中美证券混合查询。

    :param order_book_ids: 单个完整证券代码或代码列表；由服务端推断市场
    :param start_date: 起始除权日，含当日；省略则从最早记录开始
    :param end_date: 结束除权日，含当日；省略则查询至数据截止日。
        代码按该日有效的身份解析，省略时按当前代码解析
    :returns: 以 ex_date 为 DatetimeIndex 的 DataFrame，包含 order_book_id、
        ex_factor、ex_cum_factor。ex_factor 是单个除权日因子，同日行动已合成；
        ex_cum_factor 是从数据版本内该证券首个事件前以 1 为基准的累计因子。
        已覆盖证券在窗口内无记录时返回保留索引和列结构的空表。

    ex_factor 采用前收盘价除以理论除权价的方向。
    累计值不随 start_date 重置，复权价格使用累计因子的基准比值。
    累计历史跨越未定价事件、数据越界或证券未知时保留服务端错误。
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    start = to_date_str(start_date) if start_date is not None else None
    end = to_date_str(end_date) if end_date is not None else None
    if start is not None and end is not None and start > end:
        raise ValueError("start_date must not be after end_date")
    return get_client().get_ex_factor(order_book_ids=ids, start_date=start, end_date=end)
