# libfinance

`libfinance` is python library for accessing financial data easily. The goal of `libfinance` is to provide HIGH quality financial data for scholars, researchers and developers in research and production environment.


# install

Install `libfinance` by `pip`

``` {.sourceCode .bash}
$ pip install libfinance
```

Install with a develop mode
~~~
git clone https://github.com/StateOfTheArt-quant/libfinance.git
cd libfinance
python setup.py develop
~~~

# quick-start

~~~
from libfinance import get_trading_dates, history_bars

trading_dates = get_trading_dates(start_date="2023-12-25", end_date="2024-01-11")
print(trading_dates)


DatetimeIndex(['2023-12-25', '2023-12-26', '2023-12-27', '2023-12-28',
               '2023-12-29', '2024-01-02', '2024-01-03', '2024-01-04',
               '2024-01-05', '2024-01-08', '2024-01-09', '2024-01-10',
               '2024-01-11'],
              dtype='datetime64[ns]', freq=None)
              



trading_data  = history_bars(order_book_ids=["000001.XSHE","600000.XSHG"], bar_count=6, frequency="1d", datetime="2024-01-11")
print(trading_data)


                          open  close  ...       volume  total_turnover
order_book_id datetime                 ...                             
000001.XSHE   2024-01-04  9.19   9.11  ...   86419399.0    7.874701e+08
              2024-01-05  9.10   9.27  ...  199162216.0    1.852660e+09
              2024-01-08  9.23   9.15  ...  112115619.0    1.029007e+09
              2024-01-09  9.16   9.18  ...   76619388.0    7.003757e+08
              2024-01-10  9.16   9.09  ...   85862091.0    7.837712e+08
              2024-01-11  9.08   9.17  ...   93468637.0    8.538902e+08
600000.XSHG   2024-01-04  6.64   6.62  ...   28885978.0    1.905806e+08
              2024-01-05  6.60   6.68  ...   44421387.0    2.969769e+08
              2024-01-08  6.68   6.59  ...   37520337.0    2.479778e+08
              2024-01-09  6.60   6.61  ...   30741897.0    2.026476e+08
              2024-01-10  6.61   6.57  ...   22240946.0    1.466959e+08
              2024-01-11  6.56   6.53  ...   35914708.0    2.353121e+08
~~~

# Documentation
