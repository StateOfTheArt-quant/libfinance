"""行业：证券所属行业、行业成分与行业权重。"""
import libfinance as lf

# 申万一级行业
print(lf.get_instrument_industry(["000001.XSHE", "600000.XSHG"], source="SW", level=1, as_of="2024-06-28"))

# 省略 source 与 level：全部分类体系、全部层级
print(lf.get_instrument_industry("600000.XSHG", as_of="2024-06-28"))

# 申万银行业（480000.SW）的成分
members = lf.get_industry_constituents("480000.SW", as_of="2024-06-28")
print(len(members), members[:5])

# 行业成分的权重与 methodology
print(lf.get_industry_weights("480000.SW", as_of="2024-06-28").head())
