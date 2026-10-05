"""复权因子：单次因子 ex_factor 与累计因子 ex_cum_factor。"""
import libfinance as lf

# [get_ex_factor.1] 一只股票的除权事件与因子
print(lf.get_ex_factor("600000.XSHG").head())
# [/get_ex_factor.1]

# [get_ex_factor.2] 限定窗口（含两端）：累计值不从窗口起点重置
print(lf.get_ex_factor("600000.XSHG", "2023-07-01", "2023-07-31"))
# [/get_ex_factor.2]

# [get_ex_factor.3] 混合市场：代码自带市场
print(lf.get_ex_factor(["600000.XSHG", "AAPL.US"], "2023-01-01", "2023-12-31"))
# [/get_ex_factor.3]
