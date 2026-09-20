from libfinance import get_shares

# 单只股票全历史股本结构（省略日期 → 从首个事件到最后一个事件）
shares = get_shares(order_book_ids="600000.XSHG")
print(shares)

# 多只 + 指定日期范围 + 字段子集
shares = get_shares(
    order_book_ids=["000001.XSHE", "600000.XSHG"],
    start_date="2024-01-01",
    end_date="2024-06-30",
    fields=["total", "circulation_a"],
)
print(shares)
