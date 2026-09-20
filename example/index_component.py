import pandas as pd
from libfinance import get_index_weights


index_weight = get_index_weights(index_code="000300.XSHG", date="2022-09-20")
print(index_weight)

    
index_weight = get_index_weights(index_code="000300.XSHG", date="2022-07-20")
print(index_weight)
