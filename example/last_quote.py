import pandas as pd
from libfinance import get_last_quotes

quotes = get_last_quotes(order_book_ids=["600000.XSHG"])
print(quotes)