from dataclasses import dataclass

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm
from libfinance.subscribe.md_protocol import Quote

"""
Quote 的字段集与订阅路径统一（定义见 libfinance/subscribe/md_protocol.py，对齐 dynamics）：

    data_time: int
    instrument_id: str            exchange_id: str        # rqdata 风格，如 600000 / XSHG
    instrument_type: int          # InstrumentType 枚举
    pre_close_price / pre_settlement_price / last_price / volume / turnover
    pre_open_interest / open_interest
    open_price / high_price / low_price / upper_limit_price / lower_limit_price
    close_price / settlement_price / iopv
    total_bid_volume / total_ask_volume / total_trade_num
    bid_price / ask_price / bid_volume / ask_volume    # 均为 list[float]，10 档
    trading_phase_code: str
    order_book_id: str            # 只读属性 = f"{instrument_id}.{exchange_id}"

注意：本函数走 RPC（8080），与行情网关是两条独立通路，只是复用同一个 Quote 类型。
服务端返回体的字段名须与上面一致；下面用 __dict__ 注入，多余的键会原样带上，
缺失的键则在访问时才报 AttributeError。
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