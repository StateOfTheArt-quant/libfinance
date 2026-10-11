"""证券目录：股票、指数、行业、主题在同一个目录里；先确定范围，再按代码查询。"""
import libfinance as lf

# [all_instruments.1] 目录全貌：按类型与市场计数
catalog = lf.all_instruments()
print(catalog.groupby(["type", "market"]).size())
# [/all_instruments.1]

# [all_instruments.2] A 股股票：source 是上市交易所
print(lf.all_instruments(type="stock", market="cn").head())
# [/all_instruments.2]

# [all_instruments.3] 中证指数公司（CSI）发布的指数
print(lf.all_instruments(type="index", source="CSI").head())
# [/all_instruments.3]

# [all_instruments.4] 申万（SW）行业：source 是分类体系
print(lf.all_instruments(type="industry", source="SW").head())
# [/all_instruments.4]

# [all_instruments.5] THS 主题，仅 A 股
print(lf.all_instruments(type="theme").head())
# [/all_instruments.5]

# [all_instruments.6] 一次取几种类型：type 给列表
both = lf.all_instruments(type=["index", "industry"], market="cn")
print(both.groupby(["type", "source"]).size())
# [/all_instruments.6]

# [all_instruments.7] 历史时点：申万 2021 年改版前后的行业数
before = lf.all_instruments(type="industry", source="SW", as_of="2020-01-02")
after = lf.all_instruments(type="industry", source="SW", as_of="2022-04-15")
print(len(before), len(after))
# [/all_instruments.7]

# [instruments.1] 单个代码：返回一个证券，查不到为 None
stock = lf.instruments("000001.XSHE")
print(stock.order_book_id, stock.name, stock.type, stock.market)
# [/instruments.1]

# [instruments.2] 一个列表混合四种类型、两个市场：类型由代码决定
for item in lf.instruments(["000001.XSHE", "000300.XSHG", "480000.SW", "300008.THS", "AAPL.US", "45.GICS"]):
    print(item.order_book_id, item.type, item.market, item.name)
# [/instruments.2]

# [instruments.3] as_of：按当日有效的身份解析（Meta 在 2022 年仍叫 FB.US）
for item in lf.instruments(["FB.US", "000300.XSHG"], as_of="2022-04-15"):
    print(item.order_book_id, item.name)
# [/instruments.3]

# [instruments.4] last_known：已退市的代码按最后一次的身份解析
print(lf.instruments("ATVI.US"))
print(lf.instruments("ATVI.US", last_known=True).name)
# [/instruments.4]
