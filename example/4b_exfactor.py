"""复权因子：查询单个证券、限定除权窗口、合并中美结果。"""
from libfinance import get_ex_factor

# [get_ex_factor.1]
# 1. 看哪些除权日存在已定价因子，ex_factor 是单次值，ex_cum_factor 是累计值。
print(get_ex_factor("600000.XSHG").head())
# [/get_ex_factor.1]

# [get_ex_factor.2]
# 2. 限定事件窗口，起止边界均包含；累计值不会从窗口起点重置。
print(get_ex_factor("600000.XSHG", "2023-07-01", "2023-07-31"))
# [/get_ex_factor.2]

# [get_ex_factor.3]
# 3. 混合市场代码，不需要 market，输出按 order_book_id 区分。
print(get_ex_factor(["600000.XSHG", "AAPL.US"], "2023-01-01", "2023-12-31"))
# [/get_ex_factor.3]
