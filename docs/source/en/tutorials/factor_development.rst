Factors: development and evaluation
=======================================

Will stocks that traded actively over the past month perform better next?

We can split this question into two steps: describe trading activity with a number, then examine its relationship with future returns. The first step is factor development; the second is factor evaluation.

This tutorial uses the average turnover rate over the past 20 trading days to measure trading activity, then compares it with forward returns over 1, 3, 5, 10 and 20 trading days. We retrieve prices and turnover rates through libfinance and perform the calculations with pandas.

1. What is a factor?
------------------------

Academics and practitioners have long asked why different stocks earn different returns over the same period. Can characteristics such as size, valuation, profitability, recent price changes and trading activity help us predict those differences?

Factor research starts with these characteristics and looks for variables related to future returns. In this tutorial, **a factor is a numerical value computed for each stock from information available at the time, used to test whether it can predict differences in future returns.** For example, using the average turnover rate over the past 20 trading days to describe trading activity gives us a candidate factor that we can evaluate.

These variables are often called features, predictors, factors or indicators in different research settings. Their specific meanings differ, but here they share a goal: finding clues in currently observable information that help predict future returns. WorldQuant's description of an alpha as a mathematical model that attempts to predict future price movements reflects this approach: first turn an idea into a computable expression, then test its predictive value against historical data. See `WorldQuant: How we work <https://www.worldquant.com/how-we-work/>`__.

We can write this tutorial's definition of a factor as:

.. math::

   x_{i,t}=g(\mathcal{D}_{i,\le t})

Here, :math:`\mathcal{D}_{i,\le t}` denotes the data available for stock i at or before time t, and g is the method used to compute the factor.

For example, the average turnover rate over the past 20 days describes trading activity, while the return over the past 20 days describes recent price changes. For a given stock, factor values change over time; on a given date, the values across stocks form a cross section. We focus on the latter: do stocks with higher factor values on the same date subsequently outperform stocks with lower values?

Computing a number only gives us a candidate factor. Its predictive value still needs to be evaluated.

The per-stock, per-day values studied here are also called factor exposures. Factor returns describe a factor's return performance over a period; the two should be distinguished.

2. Turn the idea into a formula
-----------------------------------

Our candidate is **Turn20: the average turnover rate over the past 20 trading days**.

.. math::

   \operatorname{Turn20}_{i,t}=\frac{1}{20}\sum_{k=0}^{19}\operatorname{TurnoverRate}_{i,t-k}

Days are trading days, including the current day. Higher values indicate more active recent trading.

We begin with a hypothesis: stocks with overheated trading may have lower subsequent returns. We therefore expect Turn20 to correlate negatively with forward returns. Stating the direction before examining the results helps avoid explanations invented after seeing the data.

We first evaluate raw Turn20 without market-capitalization neutralization. The universe, data conventions and processing choices affect the results; all evaluation figures below were computed using this tutorial's setup.

3. Retrieve the research data in batches
--------------------------------------------

The research period is 2024, with an evaluation on every trading day. The universe consists of the CSI 300 constituents as of each date. The factor window is 20 trading days, and the forward-return horizons are 1, 3, 5, 10 and 20 trading days.

First take the union of the daily constituent lists, then retrieve turnover rates and prices for the whole interval. Extend the interval by 19 trading days before the first evaluation date and 20 trading days after the last. The union is only used for data retrieval; evaluation still uses each day's actual constituents.

.. code:: bash

   pip install libfinance pandas scipy

.. code:: python

   import pandas as pd
   import libfinance as lf


   # 1. Research dates and the daily universe
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

   # 2. One query each for turnover rates and prices
   rates = lf.get_turnover_rate(stocks, start, dates[-1])
   rates = rates["turnover_rate"].unstack("order_book_id")
   rates = rates.reindex(index=calendar, columns=stocks)

   bars = lf.get_price(
       stocks, start, end, fields=["close", "volume"], adjust_type="pre",
   )
   close = bars["close"].unstack("order_book_id").reindex(index=calendar, columns=stocks)
   volume = bars["volume"].unstack("order_book_id").reindex(index=calendar, columns=stocks)

``in_pool`` is a boolean table with dates as rows and stocks as columns, marking whether each stock belongs to the universe on that date. Historical constituents require daily queries, while turnover rates and prices each require only one query; the calculations do not retrieve data again.

Turnover rates are fractions: ``0.01`` means 1%. The rate uses unadjusted trading volume divided by the A-share free-float share count effective on that date, falling back to the A-share circulating share count when free-float data is unavailable. The price field ``turnover`` is traded value, not a turnover rate.

4. Use rolling for the factor and shift for forward returns
---------------------------------------------------------------

Arrange the data into tables with dates as rows and one stock per column. Calculating along the date axis processes all stocks together:

.. math::

   x_{i,t}=\frac{1}{20}\sum_{k=0}^{19}\operatorname{TurnoverRate}_{i,t-k},
   \qquad
   r^{(n)}_{i,t}=\frac{P_{i,t+n}}{P_{i,t}}-1

``rolling(20)`` uses the current row and the preceding 19 rows. ``shift(-n)`` moves the closing price n trading days ahead onto the current date, aligning factor values and forward returns on the same date.

.. code:: python

   # 3. Compute rolling and shift along trading days for each stock
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

Align dates to the complete trading calendar first. Otherwise, missing rows during suspensions would make ``rolling(20)`` refer to the latest 20 recorded observations, and ``shift(-n)`` might no longer mean the market's nth subsequent trading day. We require 20 valid turnover-rate observations and do not fill missing rates with zero.

Returns use ratios of forward-adjusted prices from the same query. Return labels with missing data or no trading at either endpoint are excluded. Valid samples are selected independently for each horizon: a missing 20-day return does not remove an available 1-day return.

The factor includes the current day's turnover rate, which is only known after the close, while forward returns also start from that day's close. This follows the statistical evaluation convention of the original notebook and tests predictive relationships. A trading simulation requires a separately defined executable entry time.

5. Compute daily IC for each horizon
----------------------------------------

IC (Information Coefficient) measures the cross-sectional correlation between stocks' factor values on a given date and their subsequent returns, helping assess whether the factor contains predictive information. Here we compute one correlation across stocks per day: Pearson correlation is called IC, and Spearman rank correlation is called Rank IC. The former uses values; the latter uses ranks.

For example, if stocks with higher factor values tend to rise more afterward, IC is usually positive; if they tend to perform worse, IC is usually negative. IC ranges from −1 to 1. Values closer to either extreme indicate stronger correlation; values near zero indicate weak linear correlation. An IC of 0.05 does not mean a 5% return or a 5% prediction accuracy.

The calculation runs across columns: ``axis=1`` means different stocks on the same date. Each horizon produces a daily IC series. We then calculate its mean, standard deviation and ICIR, defined as the mean divided by the standard deviation. All ICIR figures here are unannualized.

.. code:: python

   # 4. Daily cross-sectional IC and Rank IC, summarized over time
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

The example was run on 2026-10-15 using libfinance 0.1.3. It covers 242 trading days, with 300 stocks in the daily universe and 298 valid factor values each day. ``coverage`` records the valid sample counts separately for each horizon. The results are:

.. list-table::
   :header-rows: 1

   * - Horizon
     - Days
     - IC mean
     - IC std
     - ICIR
     - Rank IC mean
     - Rank IC std
     - Rank ICIR
   * - 1d
     - 242
     - -0.0238
     - 0.2117
     - -0.1125
     - -0.0466
     - 0.2267
     - -0.2055
   * - 3d
     - 242
     - -0.0366
     - 0.1958
     - -0.1872
     - -0.0562
     - 0.2162
     - -0.2598
   * - 5d
     - 242
     - -0.0425
     - 0.1908
     - -0.2229
     - -0.0611
     - 0.2141
     - -0.2853
   * - 10d
     - 242
     - -0.0526
     - 0.1861
     - -0.2825
     - -0.0683
     - 0.2055
     - -0.3324
   * - 20d
     - 242
     - -0.0594
     - 0.1837
     - -0.3231
     - -0.0880
     - 0.2008
     - -0.4384

Positive IC means higher factor values tend to correspond to higher forward returns; negative IC means they tend to correspond to lower forward returns. The low-turnover hypothesis predicts a negative sign. Mean IC and Rank IC are negative at all five horizons. The 20-day Rank IC has a mean of −0.0880 and a standard deviation of 0.2008. The average direction agrees with the hypothesis, but daily variation remains large.

Daily evaluation adds observation dates, but multi-day forward-return windows overlap, so the IC observations are not independent. ICIR is therefore not a significance test, and a larger mean magnitude alone does not establish that a longer horizon is more effective.

6. Check group returns as well
----------------------------------

For the 20-day horizon, divide stocks into five groups each day from lowest to highest Turn20. Compute equally weighted forward returns within each group on each date, then take their arithmetic mean across dates.

.. code:: python

   # 5. Examine group returns over the 20-day horizon
   groups = factor.apply(
       lambda row: pd.qcut(row, q=5, labels=False, duplicates="drop") + 1, axis=1,
   )
   if not groups.nunique(axis=1).eq(5).all():
       raise ValueError("Some dates cannot form five groups; check sample size and factor values")
   group_returns = pd.DataFrame({
       g: future_returns[20].where(groups == g).mean(axis=1) for g in range(1, 6)
   })
   print(group_returns.mean().rename("Mean 20-day return by group").round(4))
   print("Lowest minus highest:", round((group_returns[1] - group_returns[5]).mean(), 4))

.. list-table::
   :header-rows: 1

   * - Group (turnover from low to high)
     - Mean 20-day return
   * - 1
     - 2.01%
   * - 2
     - 1.58%
   * - 3
     - 0.97%
   * - 4
     - 1.66%
   * - 5
     - 1.42%

The average return spread between the lowest- and highest-turnover groups is 0.58 percentage points. This is also a cross-sectional forward-return statistic: overlapping 20-day returns cannot be compounded directly into a portfolio equity curve.

The lowest-turnover group has a higher return in this sample, but returns do not decrease monotonically across the five groups: group 3 is lowest, and group 4 rises again. IC and group returns offer some support for the low-turnover hypothesis, but do not establish a stable relationship. Further checks should examine the daily series and whether a few market regimes account for most of the result.

This example uses raw Turn20 without controlling for market capitalization or industry exposure, and the share counts used in turnover rates were not queried with a knowledge cutoff. The conclusions apply only to this sample and these data conventions. Further research could extend the period, reserve out-of-sample data, and examine results after market-capitalization and industry neutralization. Transaction costs, suspensions and delisted holdings require separate definitions in a portfolio backtest.

See the `complete Python script <https://github.com/StateOfTheArt-quant/libfinance/blob/976ec305408280b7ae4be5c8c1853f82dff8418d/example/python/14_factor_evaluation.py>`__ to view or download the source.
