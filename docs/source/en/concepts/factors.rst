Factors: which current states predict future returns
============================================================

Academics and practitioners are keenly interested in exploring **anomalies** (or **firm
characteristics**) and analysing their ability to explain the **cross-section** of stock returns. In other
words, considering that future stock returns are a function of current **state variables**, we are
interested in which state variables can predict future stock returns. These variables go by many names:
feature, predictor, factor, alpha, indicator, determinant. They describe the same thing.

Written as an equation:

.. math::

    \mathbb{E}\left[\, r_{i,t+1} \mid \mathcal{F}_t \,\right] = f\left(x_{i,t}^{(1)},\ x_{i,t}^{(2)},\ \dots,\ x_{i,t}^{(K)}\right)

:math:`r_{i,t+1}` is stock :math:`i`'s return over the next period, and :math:`x_{i,t}^{(k)}` is the
:math:`k`-th state variable **already known** at time :math:`t`: market cap, valuation, last month's return,
volatility, ... :math:`\mathcal{F}_t` is everything observable at :math:`t`. Factor research does two things:
find useful :math:`x`, and find a good :math:`f`. In classical work :math:`f` is a linear regression; in
machine learning it is a tree ensemble or a neural network. Both rest on the same premise, that :math:`x`
is knowable at :math:`t`. Most of this page is about why that premise is easy to break.

One thing, many names
--------------------------------

The names differ mostly because the people using them come from different fields:

.. list-table::
    :header-rows: 1
    :widths: 22 26 52

    *   - Name
        - Common in
        - Emphasis
    *   - anomaly
        - academia, asset pricing
        - A return pattern CAPM cannot explain; "anomalous" relative to theory
    *   - firm characteristic
        - academia, empirical finance
        - A variable of the firm itself: size, book-to-market, profitability, investment, ...
    *   - factor
        - asset pricing, risk models
        - A return source shared by many stocks; strictly the **factor return**, loosely the exposure (next section)
    *   - alpha
        - industry, quant investing
        - A signal that earns **excess** return, i.e. the part risk factors cannot explain
    *   - feature
        - machine learning
        - A model input, with no economic meaning assumed
    *   - predictor
        - econometrics
        - A right-hand-side variable in a regression
    *   - indicator
        - technical analysis
        - A quantity computed from price and volume: moving averages, RSI, MACD, ...
    *   - determinant
        - economics, accounting
        - Stresses causality: what **determines** returns

When you read a paper, a broker note, or talk with a colleague, check which sense of "factor" is meant.
It saves a lot of confusion.

Four distinctions worth keeping
--------------------------------

**Exposure versus factor return.** The pair most often confused. An exposure (or loading) is one number
**per stock per day**, describing how much a stock "looks like" the factor: 600000.XSHG's SIZE exposure is
1.46 on some day. A factor return is one number **per day**, describing what the factor earned; it comes
from a cross-sectional regression of all stocks' returns on their exposures:

.. math::

    r_{i,t+1} = \sum_{k} x_{i,t}^{(k)}\, f_{t+1}^{(k)} + \varepsilon_{i,t+1}

:math:`x` is the exposure, :math:`f` the factor return, :math:`\varepsilon` the stock-specific part.
:func:`~libfinance.get_factor_exposure` returns :math:`x`, not :math:`f`.

**Risk factor versus alpha factor.** A risk factor explains why stocks **move together**. It describes
covariance and is used to control portfolio risk; it need not earn a positive average return. Barra's
industry factors are the textbook case. An alpha factor predicts differences in **average** returns that
risk factors cannot explain away. One variable can be both: momentum is a Barra style factor and one of
the most studied alphas.

**Cross-section versus time series.** A cross-sectional prediction answers "on **the same day**, which stocks
will do better than others" and cares about ranking. A time-series prediction answers "will this stock (or
the market) go up" and cares about level. Factor research means cross-section by default, which is why
factor values are usually standardized across the cross-section first.

**Raw descriptor versus standardized factor.** A descriptor is a raw quantity, such as LNCAP, the log of
market cap: each stock has its own time series, independent of other stocks. A style factor is a
descriptor winsorized and standardized **over the cross-section of some universe** (sometimes several
descriptors combined), so it **depends on the universe**: a stock's SIZE is +1.46 across all A-shares and
negative once restandardized among a few large banks. The ``universe`` example in
:doc:`../reference/factors` shows exactly this.

A short history
--------------------------------

Roughly: one factor, then anomalies, then multi-factor models, then too many factors.

- **One factor: CAPM** (Sharpe 1964 and others). A stock's expected return depends only on its beta to the
  market portfolio.
- **Anomalies.** Empirical work then found patterns beta could not explain: small stocks earn more (Banz
  1981), low P/E stocks earn more (Basu 1977), winners over the past 3–12 months keep winning (Jegadeesh &
  Titman 1993).
- **Multi-factor models.** Fama & French (1992, 1993) put market, size and value into a three-factor model;
  Carhart (1997) added momentum; Fama & French (2015) added profitability and investment for five factors.
  In the industry, commercial risk models grew up alongside: Barr Rosenberg founded Barra in the 1970s,
  explaining co-movement with industry and style factors; CNE5 is its China A-share model.
- **The factor zoo.** By the 2010s hundreds of "significant" factors had been published. Harvey, Liu & Zhu
  (2016) counted 316 and argued that with so many tests a t-statistic above 2 is no longer enough,
  suggesting 3; Hou, Xue & Zhang (2020) re-tested 452 anomalies and found most lose significance under
  stricter treatment.
- **Machine learning.** Gu, Kelly & Xiu (2020) fed close to a hundred firm characteristics into tree models
  and neural networks at once and found a nonlinear :math:`f` raises predictive power markedly. Microsoft's
  qlib turned the approach into an open platform; Alpha158 is its built-in set of 158 price-volume features.

How to test a factor
--------------------------------

The three common methods all ask one question: "does today's ranking by :math:`x` resemble tomorrow's
ranking by :math:`r`?"

- **IC and Rank IC.** Each day, correlate factor values with next-period returns across stocks; with
  Spearman (rank) correlation it is the Rank IC, which is robust to outliers. A single IC is very noisy;
  what matters is its **time series**: whether the mean is reliably non-zero, and the mean over the
  standard deviation (the IR).
- **Quantile portfolios.** Each period, sort stocks into 5 or 10 groups by factor value; check whether the
  groups' next-period returns are monotonic, and the return of the top-minus-bottom long-short portfolio.
- **Fama–MacBeth regression.** Run one cross-sectional regression per period to get the factor return
  :math:`f_t`, then t-test the time series of :math:`f_t`.

Here is one Rank IC computed with libfinance: the CSI 300 constituents on 2026-07-31, the rank correlation
between their Barra style exposures and their returns over the next 20 sessions.

.. code-block:: python

    import libfinance as lf

    day = "2026-07-31"
    members = lf.get_index_constituents("000300.XSHG", as_of=day)    # the CSI 300 of that day, not today's
    x = lf.get_factor_exposure(members, "system/barra-cne5", day, day).droplevel("date")
    x = x[[c for c in x.columns if c.rsplit("/", 1)[1] in ("SIZE", "BTOP", "MOMENTUM", "RESVOL")]]

    end = lf.get_next_trading_date(day, n=20)                          # the next 20 sessions
    close = lf.get_price(members, day, end, fields="close")["close"].unstack("order_book_id")
    fwd = close.iloc[-1] / close.iloc[0] - 1                           # forward return from adjusted prices

    rank_ic = x.corrwith(fwd, method="spearman")
    print(rank_ic.rename(lambda c: c.rsplit("/", 1)[1]).round(3))

.. code-block:: text

    SIZE        0.103
    MOMENTUM    0.475
    RESVOL      0.082
    BTOP       -0.144

MOMENTUM's 0.475 looks high, but it is **one period**: it says winners kept winning over these 20 sessions,
not that momentum works. To draw a conclusion, put this code in a loop, collect tens or hundreds of
periods of IC, and look at the mean and the IR.

The usual mistakes
--------------------------------

When a factor backtest looks too good to be true, the cause is almost always below. What they share: the
code runs and the numbers are wrong.

.. list-table::
    :header-rows: 1
    :widths: 24 40 36

    *   - Mistake
        - What it looks like
        - How to avoid it in libfinance
    *   - Using what was unknown at :math:`t`
        - Aligning financials by reporting period (a 2023 annual report is published in April 2024); using
          restated figures
        - Pass ``as_of`` for financial data; see :doc:`point_in_time`
    *   - Survivorship bias
        - Backtesting the past on today's index members or today's listed stocks
        - Build the universe with ``all_instruments(as_of=...)`` or ``get_index_constituents(..., as_of=...)``
    *   - Returns polluted by ex-dates
        - Returns from unadjusted prices turn dividends into fake drops
        - Use adjusted prices for returns; see :doc:`exfactor`
    *   - The exposure is really industry or size
        - Most of a "new factor"'s return comes from favouring a few industries or small caps
        - Regress on industry dummies and SIZE and keep the residual (neutralization); industries in
          :doc:`classification`
    *   - Inconsistent standardization
        - Research standardizes over all A-shares, trading picks only within the CSI 300
        - Keep ``get_factor_exposure(..., universe=...)`` consistent with your universe
    *   - Multiple testing
        - Trying 100 factors and keeping the 5 with the highest t-statistics
        - Raise the bar (t > 3) and keep an out-of-sample period; no tool can do this one for you

In libfinance
--------------------------------

The libraries in :doc:`../reference/factors` map onto the concepts above:

.. list-table::
    :header-rows: 1
    :widths: 30 30 40

    *   - Library
        - What it is
        - Typical use
    *   - ``system/alpha158``, ``system/qlib``
        - Price-volume features
        - Inputs to machine-learning models, alpha mining
    *   - ``system/barra-cne5``, ``system/barra-cne6``
        - Style and industry **exposures** of a risk model
        - Risk attribution, portfolio constraints, neutralization
    *   - ``system/barra-cne5-descriptor``, ``system/barra-cne6-descriptor``
        - Raw descriptors
        - Your own standardization, or direct study as firm characteristics

References
--------------------------------

- Banz, R. W. (1981). The relationship between return and market value of common stocks. *Journal of Financial Economics*.
- Basu, S. (1977). Investment performance of common stocks in relation to their price-earnings ratios. *Journal of Finance*.
- Carhart, M. M. (1997). On persistence in mutual fund performance. *Journal of Finance*.
- Fama, E. F., & French, K. R. (1992). The cross-section of expected stock returns. *Journal of Finance*.
- Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics*.
- Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*.
- Gu, S., Kelly, B., & Xiu, D. (2020). Empirical asset pricing via machine learning. *Review of Financial Studies*.
- Harvey, C. R., Liu, Y., & Zhu, H. (2016). … and the cross-section of expected returns. *Review of Financial Studies*.
- Hou, K., Xue, C., & Zhang, L. (2020). Replicating anomalies. *Review of Financial Studies*.
- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers. *Journal of Finance*.
- Sharpe, W. F. (1964). Capital asset prices: A theory of market equilibrium under conditions of risk. *Journal of Finance*.
