"""因子：qlib、alpha158 与 Barra CNE5（factors-daybar），因子名写全名。"""
import libfinance as lf

# [list_factor_libraries.1] 因子库一览
print(lf.list_factor_libraries())
# [/list_factor_libraries.1]

# [list_factors.1] 一个库里的因子全名
print(lf.list_factors("system/barra-cne5")[:12])
# [/list_factors.1]

# [get_factor_exposure.1] Barra CNE5 风格因子：库名展开为 42 列（10 个风格、31 个行业、COUNTRY）
f = lf.get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/barra-cne5", "2026-09-07", "2026-09-10")
print(f.shape)
print(f.iloc[:, :10].rename(columns=lambda c: c.rsplit("/", 1)[1]).round(3))
# [/get_factor_exposure.1]

# [get_factor_exposure.2] 原始描述符与标准化后的风格因子混在一次请求里
print(lf.get_factor_exposure(["600000.XSHG", "600519.XSHG"],
                             ["system/barra-cne5-descriptor/LNCAP", "system/barra-cne5/SIZE", "system/barra-cne5/BANKS"],
                             "2026-09-10", "2026-09-10"))
# [/get_factor_exposure.2]

# [get_factor_exposure.3] universe：截面因子在给定的代码上重新标准化，时序因子不变
banks = ["600000.XSHG", "000001.XSHE", "601398.XSHG", "601288.XSHG", "600036.XSHG"]
print(lf.get_factor_exposure(["600000.XSHG", "000001.XSHE"], ["system/barra-cne5/SIZE", "system/barra-cne5-descriptor/LNCAP"],
                             "2026-09-10", "2026-09-10", universe=banks))
# [/get_factor_exposure.3]

# [get_factor_exposure.4] alpha158：当天的截面
print(lf.get_factor_exposure(["600000.XSHG", "000001.XSHE", "600519.XSHG"],
                             ["system/alpha158/KMID", "system/alpha158/ROC5", "system/alpha158/STD20"], "2026-09-10", "2026-09-10"))
# [/get_factor_exposure.4]
