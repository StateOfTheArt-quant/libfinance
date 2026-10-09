"""主题：证券所属主题、主题成分与主题权重（THS 主题）。"""
import libfinance as lf

# [get_instrument_themes.1] 证券当前所属的主题
print(lf.get_instrument_themes(["600000.XSHG", "000001.XSHE"], source="THS").head(10))
# [/get_instrument_themes.1]

# [get_theme_constituents.1] 一个主题的成分
members = lf.get_theme_constituents("300008.THS")
print(len(members), members[:5])
# [/get_theme_constituents.1]

# [get_theme_weights.1] 主题权重：由成分名单推出的等权
print(lf.get_theme_weights("300008.THS").head())
# [/get_theme_weights.1]
