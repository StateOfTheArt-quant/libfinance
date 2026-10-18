因子，因子开发和评价
====================

最近一个月交易活跃的股票，接下来会表现得更好吗？

这个问题可以拆成两步：先用一个数字描述交易有多活跃，再检查这个数字与未来收益的关系。前一步是因子开发，后一步是因子评价。

下面用过去 20 个交易日的平均换手率描述交易活跃程度，再检查它与未来 1、3、5、10、20 日收益的关系。行情和换手率通过 libfinance 读取，计算使用 pandas。

1. 因子是什么
-------------

学术界和业界一直关心同一个问题：股票之间的异象（anomaly），或者说公司自身的属性（firm characteristic），能在多大程度上解释股票收益在截面上的差异。

换一种说法：既然股票的未来收益可以看成当前状态变量的函数，我们想知道的就是——哪些状态变量能预测股票的未来收益。这些状态变量在不同的地方有不同的名字：特征（feature）、预测变量（predictor）、因子（factor）、alpha、指标（indicator）、决定因素（determinant）。它们说的是同一件事。

WorldQuant 将 alpha 定义为“尝试预测金融工具未来价格变动的数学模型”。这里借鉴的是它的研究思路：把一个想法写成可计算的表达式，再用历史数据检验。\ `WorldQuant：How we work <https://www.worldquant.com/how-we-work/>`__

在本文中，\ **因子是根据当时可获得的信息，为每只股票计算出的一个数值，用来检验它能否预测未来收益的差异。**

可以写成：

.. math::

   x_{i,t}=g(\mathcal{D}_{i,\le t})

其中，\ :math:`\mathcal{D}_{i,\le t}` 表示股票 i 在 t 时刻及之前可获得的数据，g 表示计算因子的方法。

例如，过去 20 日的平均换手率描述交易活跃程度，过去 20 日的收益率描述近期涨跌。固定一只股票，因子值随时间变化；固定一个日期，不同股票的因子值组成一个截面。本文关心后者：同一天因子值较高的股票，之后是否比因子值较低的股票表现更好？

算出一个数，只意味着有了一个候选因子。它是否有预测力，需要评价。

这里研究的是每只股票、每一天的因子值，也常称为因子暴露。“因子收益”则描述某个因子在一期内的收益表现，两者需要区分。

2. 把想法写成公式
-----------------

研究对象是 **Turn20：过去 20 个交易日的平均换手率**\ 。

.. math::

   \operatorname{Turn20}_{i,t}=\frac{1}{20}\sum_{k=0}^{19}\operatorname{TurnoverRate}_{i,t-k}

这里的日子按交易日计数，包含当天。因子值越大，表示近期交易越活跃。

我们先提出一个待检验的假设：交易过热的股票，后续收益可能较低。因此，预期 Turn20 与未来收益负相关。方向先写下来，再看数据，避免看到结果后才补解释。

本次研究先评价原始 Turn20，不做市值中性化。股票池、数据口径和处理方式会影响结果，下面的评价数字均按本文的设定重新计算。

3. 一次取出研究区间的数据
-------------------------

研究区间为 2024 年，评价日期是这一年的每一个交易日。股票池使用各日的沪深 300 成分，因子窗口为 20 个交易日，未来收益分别取 1、3、5、10、20 个交易日。

先把各日成分取并集，再一次读取整个区间的换手率和行情。为了覆盖窗口，向前多取 19 个交易日，向后多取 20 个交易日。成分的并集只用于下载数据；评价时仍按每日的成分筛选。

.. code:: bash

   pip install libfinance pandas scipy

.. code:: python

   import pandas as pd
   import libfinance as lf


   # 1. 研究日期与每日股票池
   horizons = [1, 3, 5, 10, 20]
   dates = lf.get_trading_dates("2024-01-01", "2024-12-31")
   members = {
       day: lf.get_index_constituents("000300.XSHG", as_of=day)
       for day in dates
   }
   stocks = sorted({stock for ids in members.values() for stock in ids})
   start = lf.get_n_trading_dates_until(dates[0], n=20)[0]
   end = lf.get_next_trading_date(dates[-1], n=max(horizons))
   calendar = lf.get_trading_dates(start, end)

   in_pool = pd.DataFrame(False, index=dates, columns=stocks)
   for day, ids in members.items():
       in_pool.loc[day, ids] = True

   # 2. 换手率与行情分别只查询一次
   rates = lf.get_turnover_rate(stocks, start, dates[-1])
   rates = rates["turnover_rate"].unstack("order_book_id")
   rates = rates.reindex(index=calendar, columns=stocks)

   bars = lf.get_price(
       stocks, start, end, fields=["close", "volume"], adjust_type="pre",
   )
   close = bars["close"].unstack("order_book_id").reindex(index=calendar, columns=stocks)
   volume = bars["volume"].unstack("order_book_id").reindex(index=calendar, columns=stocks)

``in_pool`` 是“日期 × 股票”的布尔表，标记股票当天是否在研究范围内。历史成分需要逐日查询，换手率和行情则各查询一次，计算过程中不再重复取数。

换手率的单位是小数，\ ``0.01`` 表示 1%。这里使用未复权成交量除以当日生效的 A 股自由流通股本，缺少自由流通股本时退回 A 股流通股本。行情字段 ``turnover`` 是成交额，不能当作换手率。

4. 用 rolling 计算因子，用 shift 计算未来收益
---------------------------------------------

把数据展开成“日期 × 股票”的表，每列对应一只股票。沿日期方向计算，便可以同时处理所有股票：

.. math::

   x_{i,t}=\frac{1}{20}\sum_{k=0}^{19}\operatorname{TurnoverRate}_{i,t-k},
   \qquad
   r^{(n)}_{i,t}=\frac{P_{i,t+n}}{P_{i,t}}-1

``rolling(20)`` 使用当天及之前的 20 行；\ ``shift(-n)`` 将第 n 个交易日后的收盘价移到当天。这样，因子和未来收益便在同一个日期上对齐。

.. code:: python

   # 3. 每列是一只股票，沿交易日计算 rolling 和 shift
   factor = rates.rolling(20, min_periods=20).mean().loc[dates].where(in_pool)
   future_returns = {}
   for n in horizons:
       returns = close.shift(-n) / close - 1
       active = (volume > 0) & (volume.shift(-n) > 0)
       future_returns[n] = returns.where(active).loc[dates].where(in_pool)

   coverage = pd.DataFrame({"pool": in_pool.sum(axis=1), "factor": factor.count(axis=1)})
   for n in horizons:
       coverage[f"valid_{n}d"] = (factor.notna() & future_returns[n].notna()).sum(axis=1)
   print(coverage.agg(["min", "max"]))

日期要先对齐到完整交易日历。否则停牌日缺行时，\ ``rolling(20)`` 会变成最近 20 个有记录的日子，\ ``shift(-n)`` 也未必对应市场的第 n 个交易日。这里要求因子窗口有完整的 20 个有效值，不把缺失换手率填为零。

收益使用同一次查询中的前复权价格比值，起止日无成交或缺失的收益标签不参与评价。每个期限分别筛选有效样本，缺少 20 日收益不会连带删除可计算的 1 日收益。

因子包含当天收盘后才确定的换手率，未来收益也从当天收盘开始。这与原 notebook 的统计评价口径一致，用于检查预测关系；若要模拟交易，应另设可执行的成交时点。

5. 逐日计算各期限的 IC
----------------------

IC（Information Coefficient，信息系数）衡量同一天各只股票的因子值与它们未来收益的相关程度，用来检查因子是否包含预测信息。本文每天在股票截面上计算一次相关系数：Pearson 相关系数记为 IC，Spearman 秩相关系数记为 Rank IC。前者使用数值，后者使用排序。

例如，若因子值较高的股票之后往往涨得更多，IC 通常为正；若它们之后往往表现更差，IC 通常为负。IC 的取值范围是 −1 到 1，越接近两端，相关关系越强；接近 0 表示线性相关较弱。IC 为 0.05 不代表收益率为 5%，也不代表预测正确率为 5%。

计算在列方向进行：\ ``axis=1`` 表示同一天的不同股票。各期限都得到一条逐日 IC 序列，再计算均值、标准差和均值除以标准差的 ICIR。这里的 ICIR 均不年化。

.. code:: python

   # 4. 每日截面 IC 与 Rank IC，再沿时间汇总
   ic = pd.DataFrame({
       n: factor.corrwith(future_returns[n], axis=1) for n in horizons
   })
   rank_ic = pd.DataFrame({
       n: factor.corrwith(future_returns[n], axis=1, method="spearman") for n in horizons
   })
   summary = pd.DataFrame({
       "days": ic.count(),
       "IC_mean": ic.mean(),
       "IC_std": ic.std(),
       "ICIR": ic.mean() / ic.std().replace(0, float("nan")),
       "RankIC_mean": rank_ic.mean(),
       "RankIC_std": rank_ic.std(),
       "RankICIR": rank_ic.mean() / rank_ic.std().replace(0, float("nan")),
   })
   summary.index.name = "horizon"
   print(summary.round(4).to_string())

本次于 2026-10-15 使用 libfinance 0.1.3 运行。共 242 个交易日，每日股票池为 300 只，可计算因子数量均为 298；各期限的有效样本数量由 ``coverage`` 分别记录。结果如下：

+----------+--------+---------+-----------+---------+--------------+----------------+-----------+
| 未来收益 | 期数   | IC 均值 | IC 标准差 | ICIR    | Rank IC 均值 | Rank IC 标准差 | Rank ICIR |
+==========+========+=========+===========+=========+==============+================+===========+
| 1d       | 242    | -0.0238 | 0.2117    | -0.1125 | -0.0466      | 0.2267         | -0.2055   |
+----------+--------+---------+-----------+---------+--------------+----------------+-----------+
| 3d       | 242    | -0.0366 | 0.1958    | -0.1872 | -0.0562      | 0.2162         | -0.2598   |
+----------+--------+---------+-----------+---------+--------------+----------------+-----------+
| 5d       | 242    | -0.0425 | 0.1908    | -0.2229 | -0.0611      | 0.2141         | -0.2853   |
+----------+--------+---------+-----------+---------+--------------+----------------+-----------+
| 10d      | 242    | -0.0526 | 0.1861    | -0.2825 | -0.0683      | 0.2055         | -0.3324   |
+----------+--------+---------+-----------+---------+--------------+----------------+-----------+
| 20d      | 242    | -0.0594 | 0.1837    | -0.3231 | -0.0880      | 0.2008         | -0.4384   |
+----------+--------+---------+-----------+---------+--------------+----------------+-----------+

正 IC 表示因子值较高的股票通常对应较高的未来收益，负 IC 则对应较低的未来收益。低换手率假设预期得到负值。本次五个期限的 IC 和 Rank IC 均值均为负；20 日 Rank IC 均值为 −0.0880，标准差为 0.2008。平均方向符合假设，但逐日波动仍然较大。

逐日评价增加了观测日期，但多日未来收益窗口会重叠，IC 序列并不独立。因此 ICIR 不能直接当作显著性检验结果，长期限也不能因为均值更大就判定更有效。

6. 用分组收益补充检查
---------------------

以 20 日收益为例，每天按 Turn20 从低到高分成五组，组内等权，先计算每日的组内未来收益，再沿日期取算术平均。

.. code:: python

   # 5. 以 20 日收益检查分组关系

   groups = factor.apply(
       lambda row: pd.qcut(row, q=5, labels=False, duplicates="drop") + 1, axis=1,
   )
   if not groups.nunique(axis=1).eq(5).all():
       raise ValueError("部分日期无法形成五组，请检查样本量和因子取值")
   group_returns = pd.DataFrame({
       g: future_returns[20].where(groups == g).mean(axis=1) for g in range(1, 6)
   })
   print(group_returns.mean().rename("各组平均20日收益").round(4))
   print("低组减高组：", round((group_returns[1] - group_returns[5]).mean(), 4))

====================== ==============
分组（换手率从低到高） 平均 20 日收益
====================== ==============
第 1 组                2.01%
第 2 组                1.58%
第 3 组                0.97%
第 4 组                1.66%
第 5 组                1.42%
====================== ==============

低换手率组减高换手率组的平均收益差为 0.58 个百分点。这也是未来收益的截面统计，重叠的 20 日收益不能直接连乘为组合净值。

本次最低换手率组收益较高，但五组收益没有呈现单调递减：第 3 组最低，第 4 组又回升。IC 和分组收益提供了一些支持低换手率假设的证据，尚不能据此判断关系稳定。还需要检查逐日序列，以及结果是否主要来自少数行情阶段。

本次使用原始 Turn20，没有控制市值和行业暴露；换手率中的股本也未按知识截止时点查询。结论只适用于这里的样本和数据口径。进一步研究可以延长区间、留出样本外数据，再检查市值与行业中性化后的结果。交易费用、停牌和退市持仓处理，则需要在组合回测中另行定义。

完整代码见 `完整 Python 脚本 <https://github.com/StateOfTheArt-quant/libfinance/blob/976ec305408280b7ae4be5c8c1853f82dff8418d/example/python/14_factor_evaluation.py>`__\ ，打开后可查看源码或下载文件。
