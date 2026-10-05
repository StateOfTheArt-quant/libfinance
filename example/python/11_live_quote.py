"""实时快照：一次查询多只证券的最新行情。"""
import libfinance as lf

# 一次查询多只证券；还没有快照的为 None
for code, quote in lf.get_last_quotes(["600000.XSHG", "000001.XSHE"]).items():
    print(code, None if quote is None else (quote.last_price, quote.volume))
