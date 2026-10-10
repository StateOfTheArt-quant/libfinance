"""因子：alpha158 与 Barra CNE5 的日频因子暴露，因子名写全名。"""
import libfinance as lf

# alpha158：库名展开为它的 158 个因子，每个因子一列
f = lf.get_factor_exposure(["600000.XSHG", "000001.XSHE"], ["system/alpha158"], "2026-08-27", "2026-09-10")
print(f.shape)
print(f.iloc[:, :6].rename(columns=lambda c: c.rsplit("/", 1)[1]).round(4))  # 列名只留因子名

# Barra CNE5：42 列（10 个风格、31 个行业、COUNTRY）；风格因子在当天全部 A 股上标准化
f = lf.get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/barra-cne5", "2026-09-01", "2026-09-10")
print(f.shape)
print(f.iloc[:, :6].rename(columns=lambda c: c.rsplit("/", 1)[1]).round(3))
