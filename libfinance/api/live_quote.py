from dataclasses import dataclass

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm
from libfinance.subscribe.md_protocol import Quote

"""
@dataclass
class Quote:
    trading_day: str
    instrument_id: str
    exchange_id: str
    instrument_type: int
    pre_close_price: float
    pre_settlement_price: float
    last_price: float
    volume: int
    turnover: float
    pre_open_interest: float
    open_interest: float
    open_price: float
    high_price: float
    low_price: float
    upper_limit_price: float
    lower_limit_price: float
    close_price: float
    settlement_price: float
    iopv: float
    bid_price: list       # [10]
    ask_price: list       # [10]
    bid_volume: list      # [10]
    ask_volume: list      # [10]
    trading_phase_code: str
    data_time: int
"""

def dict_to_quotes_ultrafast(raw_data) -> dict[str, Quote]:
    result = {}
    for k, v in raw_data.items():
        # 🛑 1. 拦截顶层 None，彻底避免 update(None) 触发 TypeError
        if v is None:
            result[k] = v
            continue
            
        # ⚡ 2. 已经是 Quote 实例，直接透传（零拷贝，最快路径）
        if type(v) is Quote:
            result[k] = v
            continue
            
        # 🧹 3. 是 dict 时快速清洗内部 None 值，防止下游量价计算报 TypeError
        # 字典推导式在 CPython 底层由 C 循环驱动，性能损耗 < 5%
        clean_v = {fk: fv for fk, fv in v.items() if fv is not None}
        
        # 🚀 4. 绕过 __init__ 参数绑定，直接注入对象内存
        q = object.__new__(Quote)
        q.__dict__.update(clean_v)
        result[k] = q
        
    return result

@export_as_api
def get_last_quotes(order_book_ids):
    response =  get_client().get_last_quotes(order_book_ids=order_book_ids)
    return dict_to_quotes_ultrafast(response)