因子：哪些"当前状态"能预测未来收益
============================================================

学术界和业界一直关心同一个问题：股票之间的\ **异象**\ （anomaly），或者说公司自身的\ **属性**\ （firm
characteristic），能在多大程度上解释股票收益在\ **截面**\ 上的差异。换一种说法：既然股票的未来收益可以看成
当前\ **状态变量**\ 的函数，我们想知道的就是——哪些状态变量能预测股票的未来收益。这些状态变量在不同的地方有不同
的名字：特征（feature）、预测变量（predictor）、因子（factor）、alpha、指标（indicator）、决定因素
（determinant）。它们说的是同一件事。

用一个式子写出来：

..  math::

    \mathbb{E}\left[\, r_{i,t+1} \mid \mathcal{F}_t \,\right] = f\left(x_{i,t}^{(1)},\ x_{i,t}^{(2)},\ \dots,\ x_{i,t}^{(K)}\right)

:math:`r_{i,t+1}` 是股票 :math:`i` 下一期的收益，\ :math:`x_{i,t}^{(k)}` 是它在 :math:`t` 时刻\ **已经知道**\ 的第
:math:`k` 个状态变量——市值、估值、过去一个月的涨幅、波动率……:math:`\mathcal{F}_t` 是 :math:`t` 时刻能看到的全部
信息。因子研究做两件事：找到有用的 :math:`x`\ ，再找到合适的 :math:`f`\ 。传统方法里 :math:`f` 是线性回归，
机器学习方法里 :math:`f` 是树模型或神经网络；但两者共享同一个前提——:math:`x` 必须在 :math:`t` 时刻可知。
这一章的大部分篇幅，都在讲这个前提为什么容易被打破。

同一个东西，很多名字
--------------------------------

名字不同，往往只是因为说话的人来自不同的领域，关注点不同：

..  list-table::
    :header-rows: 1
    :widths: 22 26 52

    *   - 叫法
        - 常见于
        - 侧重点
    *   - 异象 anomaly
        - 学术，资产定价
        - CAPM 解释不了的收益规律。"异"是相对于理论而言的
    *   - 公司属性 firm characteristic
        - 学术，实证金融
        - 变量来自公司本身：规模、账面市值比、盈利能力、投资……
    *   - 因子 factor
        - 资产定价，风险模型
        - 一组股票共同的收益来源；严格说指\ **因子收益**\ ，口语里常指暴露（见下一节）
    *   - alpha
        - 业界，量化投资
        - 能带来\ **超额**\ 收益的信号，即风险因子解释不了的那部分
    *   - 特征 feature
        - 机器学习
        - 模型的输入，不预设经济含义
    *   - 预测变量 predictor
        - 计量经济学
        - 回归右边的变量
    *   - 指标 indicator
        - 技术分析
        - 由价量算出的量：均线、RSI、MACD……
    *   - 决定因素 determinant
        - 经济学，会计学
        - 强调因果：是什么\ **决定**\ 了收益

读论文、读研报、和同事讨论时，先确认对方说的"因子"是哪一种意思，可以省掉很多误会。

要分清的四对概念
--------------------------------

**暴露与因子收益。**\ 这是最常被混用的一对。暴露（exposure，也叫载荷 loading）是\ **每只股票、每一天**\ 一个数，
描述这只股票"有多像"某个因子，例如 600000.XSHG 在某日的 SIZE 暴露是 1.46。因子收益是\ **每一天**\ 一个数，描述
这个因子当天"赚了多少"，由全部股票的收益对暴露做截面回归得到：

..  math::

    r_{i,t+1} = \sum_{k} x_{i,t}^{(k)}\, f_{t+1}^{(k)} + \varepsilon_{i,t+1}

:math:`x` 是暴露，\ :math:`f` 是因子收益，\ :math:`\varepsilon` 是个股特有的部分。
:func:`~libfinance.get_factor_exposure` 返回的是 :math:`x`\ ，不是 :math:`f`\ 。

**风险因子与 alpha 因子。**\ 风险因子用来解释股票为什么\ **一起涨跌**——它描述的是协方差，用来控制组合的风险，
未必带来正的平均收益，Barra 的行业因子就是典型。alpha 因子用来预测\ **平均收益**\ 的差异，并且要求这种差异不能
被风险因子解释掉。同一个变量可以两者兼是：动量既是 Barra 的风格因子，也是被研究最多的 alpha 之一。

**截面与时序。**\ 截面预测回答"**同一天**\ ，哪些股票会比另一些涨得多"，看的是相对排序；时序预测回答
"这只股票（或整个市场）\ **未来**\ 会不会涨"，看的是绝对水平。因子研究默认指截面——这也是为什么因子值通常要先在
截面上标准化。

**原始描述符与标准化因子。**\ 描述符（descriptor）是原始量，如总市值的对数 LNCAP，每只股票一条自己的时间序列，
不依赖其他股票。风格因子是把描述符在\ **某个股票池的截面上**\ 去极值、标准化（有时还合成多个描述符）后的结果，
于是它\ **依赖于股票池**\ ：同一只股票的 SIZE 在全 A 股里是 +1.46，放到几只大银行里重新标准化就变成负数。
:doc:`../reference/factors` 的 ``universe`` 示例展示的正是这件事。

一段简史
--------------------------------

因子研究的脉络大致是：一个因子 → 发现异象 → 多因子模型 → 因子太多。

- **单因子：CAPM**\ （Sharpe 1964 等）。股票的期望收益只由它对市场组合的 beta 决定。
- **异象**\ 。随后的实证发现 beta 解释不了的规律：小市值股票收益更高（Banz 1981）、低市盈率股票收益更高
  （Basu 1977）、过去 3–12 个月的赢家继续赢（Jegadeesh & Titman 1993）。
- **多因子模型**\ 。Fama & French（1992、1993）把市场、规模、价值放进一个三因子模型；Carhart（1997）加入动量；
  Fama & French（2015）又加入盈利与投资，成为五因子模型。业界在同一时期发展出商业风险模型：Barr Rosenberg
  在 1970 年代创立 Barra，用行业与风格因子解释股票的共同波动；CNE5 是它针对中国 A 股的版本。
- **因子动物园**\ 。到 2010 年代，发表过的"有效"因子已有数百个。Harvey, Liu & Zhu（2016）统计了 316 个，
  指出在这么多次检验下，t 值超过 2 已经不够，建议门槛提高到 3；Hou, Xue & Zhang（2020）重新检验了 452 个异象，
  大部分在更严格的处理下不再显著。
- **机器学习**\ 。Gu, Kelly & Xiu（2020）把近百个公司属性同时喂给树模型和神经网络，发现非线性的 :math:`f` 能
  显著提高预测力。微软的 qlib 把这一思路做成开源平台，Alpha158 是它内置的 158 个价量特征。

怎么检验一个因子
--------------------------------

最常用的三种做法，都在问同一个问题："今天的 :math:`x` 排序，和明天的 :math:`r` 排序，像不像？"

- **IC 与 Rank IC**\ 。每一天在截面上算因子值与下一期收益的相关系数；用秩相关（Spearman）的叫 Rank IC，对极端值
  更稳健。单期 IC 噪声很大，看的是它的\ **时间序列**\ ：均值是否稳定地不为零，均值除以标准差（IR）有多大。
- **分组组合**\ 。每期按因子值把股票分成 5 组或 10 组，看各组下一期的平均收益是否单调，以及"最高组减最低组"的
  多空组合收益。
- **Fama–MacBeth 回归**\ 。每一期做一次截面回归得到因子收益 :math:`f_t`\ ，再对 :math:`f_t` 的时间序列做
  t 检验。

下面用 libfinance 算一次 Rank IC：2026-07-31 当天的沪深 300 成分，Barra 风格因子暴露与之后 20 个交易日收益的
秩相关。

..  code-block:: python

    import libfinance as lf

    day = "2026-07-31"
    members = lf.get_index_constituents("000300.XSHG", as_of=day)    # 那一天的沪深 300，不是今天的
    x = lf.get_factor_exposure(members, "system/barra-cne5", day, day).droplevel("date")
    x = x[[c for c in x.columns if c.rsplit("/", 1)[1] in ("SIZE", "BTOP", "MOMENTUM", "RESVOL")]]

    end = lf.get_next_trading_date(day, n=20)                          # 未来 20 个交易日
    close = lf.get_price(members, day, end, fields="close")["close"].unstack("order_book_id")
    fwd = close.iloc[-1] / close.iloc[0] - 1                           # 复权价算的未来收益

    rank_ic = x.corrwith(fwd, method="spearman")
    print(rank_ic.rename(lambda c: c.rsplit("/", 1)[1]).round(3))

..  code-block:: text

    SIZE        0.103
    MOMENTUM    0.475
    RESVOL      0.082
    BTOP       -0.144

MOMENTUM 的 0.475 看起来很高，但这只是\ **一期**——它说明这 20 个交易日里强者恒强，不说明动量因子有效。
要下结论，需要把这段代码放进循环，得到几十上百期 IC 的序列再看均值和 IR。

最容易犯的错
--------------------------------

因子回测的结果"好得不像真的"时，原因几乎总在下面几条里。它们的共同点是：代码能跑，数字是错的。

..  list-table::
    :header-rows: 1
    :widths: 24 40 36

    *   - 错误
        - 表现
        - 在 libfinance 里怎么避免
    *   - 用了 :math:`t` 时刻还不知道的信息
        - 用报告期对齐财报（2023 年报在 2024 年 4 月才披露）；用了事后修订的财务数字
        - 财务数据传 ``as_of``\ ，见 :doc:`point_in_time`
    *   - 幸存者偏差
        - 用今天的成分股或今天还在上市的股票回测过去
        - 股票池用 ``all_instruments(as_of=...)`` 或 ``get_index_constituents(..., as_of=...)``
    *   - 收益被除权污染
        - 用未复权价算收益，分红日变成虚假的下跌
        - 收益用复权价，见 :doc:`exfactor`
    *   - 暴露其实是行业或市值
        - 一个"新因子"的收益，大部分来自它偏好某几个行业或小盘股
        - 对行业哑变量与 SIZE 回归取残差（中性化），行业见 :doc:`classification`
    *   - 标准化的范围不一致
        - 研究在全 A 股上标准化，交易却只在沪深 300 里选股
        - ``get_factor_exposure(..., universe=...)`` 与你的股票池保持一致
    *   - 多重检验
        - 试了 100 个因子，挑出 t 值最高的 5 个
        - 提高门槛（t > 3）、留出样本外区间；这一条没有工具能替你做

在 libfinance 里
--------------------------------

:doc:`../reference/factors` 提供的几个库，对应上面不同的概念（各库的口径见 :doc:`../data/factors`\ ，每个因子的公式见 :doc:`../reference/factor_dictionary`\ ）：

..  list-table::
    :header-rows: 1
    :widths: 30 30 40

    *   - 库
        - 是什么
        - 典型用途
    *   - ``system/alpha158``\ 、\ ``system/qlib``
        - 价量特征（feature）
        - 机器学习模型的输入，挖掘 alpha
    *   - ``system/barra-cne5``\ 、\ ``system/barra-cne6``
        - 风险模型的风格与行业\ **暴露**
        - 风险归因、组合约束、因子中性化
    *   - ``system/barra-cne5-descriptor``\ 、\ ``system/barra-cne6-descriptor``
        - 原始描述符
        - 自己定义标准化方式，或作为公司属性直接研究

参考文献
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
