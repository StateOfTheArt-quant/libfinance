# API 场景示例

与文档的六类 API 对照阅读。每份脚本先列接口与参数，再通过参数变化说明用途。
运行前应已配置服务连接；历史日期需落在当前服务的数据覆盖内。脚本打印实际结果，不依赖固定行数或价格。

| 分类 | 脚本 | 重点比较 |
| --- | --- | --- |
| 1 合约信息和交易日历 | [0a_instrument.py](0a_instrument.py)、[0b_trading_calendar.py](0b_trading_calendar.py) | 市场与类型、最新与历史、单个与列表、交易日偏移 |
| 2 行情信息 | [1_get_price.py](1_get_price.py) | 字段、多证券面板、原始价与复权价、最近交易日窗口 |
| 3 基本面信息 | [2_financials.py](2_financials.py)、[4a_shares.py](4a_shares.py) | 报告季度与知识截止日、修订版本、股本字段 |
| 4 行业和概念信息 | [3a_industry.py](3a_industry.py)、[3b_concept_components.py](3b_concept_components.py)、[index_component.py](index_component.py) | 分类层级、双向查询、概念目录、历史成分权重 |
| 5 公司行动信息 | [corporate_actions.py](corporate_actions.py) | 分红、拆股、配股、分拆，事件日期与信息可见性 |
| 6 实时行情 | [last_quote.py](last_quote.py)、[订阅示例](subscription/python/live_subscribe_example.py) | 单次快照、批量快照、自动选源与定向订阅 |

中文 API 参考通过 `literalinclude` 直接展示这些脚本中的片段。修改示例时保留 `# [函数名]` 和 `# [/函数名]` 标记，让页面与代码同步。
