import warnings
import datetime

from dateutil.relativedelta import relativedelta
from six import string_types, binary_type, text_type
from libfinance.utils.utils import listify, to_date, is_panel_removed, to_date_int, to_date_str

def ensure_list_of_string(s, name=""):
    if isinstance(s, string_types):
        return [s]
    # list(600000) 会抛出 "'int' object is not iterable"，说不清是哪个参数、要的是什么
    if s is None or isinstance(s, (bytes, int, float)) or not hasattr(s, "__iter__"):
        raise ValueError("{}: expect string or list of string, got {!r}".format(name, s))

    result = list(s)
    for v in result:
        if not isinstance(v, string_types):
            raise ValueError("{}: expect string or list of string, got {!r}".format(name, v))
    return result


def ensure_codes(s, name="order_book_ids"):
    """一个代码或代码列表，原样返回（单个字符串仍是字符串）；None、空列表、非字符串元素报 ValueError。

    给把代码原样转给服务端的接口用：不改变线上形状，只拦住"没给代码"——否则服务端答一张空表，
    看起来像"没有数据"。
    """
    codes = ensure_list_of_string(s, name)
    if not codes:
        raise ValueError("{}: at least one order book id expected".format(name))
    return s if isinstance(s, string_types) else codes


def ensure_list(s, expect_type, name=""):
    if isinstance(s, expect_type):
        return [s]    
    result = list(s)
    for v in result:
        if not isinstance(v, expect_type):
            raise ValueError("{}: expect {!r}, got {!r}".format(name, expect_type, v))
    return result


def ensure_string(s, name="", decoding="utf-8"):
    if isinstance(s, binary_type):
        return s.decode(decoding)
    if not isinstance(s, text_type):
        raise ValueError("{}: expect a string, got {!r}".format(name, s))
    return s


def ensure_string_in(s, should_in, name="", decoding="utf-8"):
    s = ensure_string(s, name, decoding)
    if s not in should_in:
        raise TypeError("{}: expect value in {!r}".format(name, should_in))
    return s


def check_type(s, t, name=""):
    if not isinstance(s, t):
        raise ValueError("{}: expect value in type {}, got {!r}.".format(name, t, s))


def ensure_int(s, name=""):
    try:
        return int(s)
    except TypeError:
        raise ValueError("{}: expect int value, got {!r}.".format(name, s))


def check_items_in_container(items, should_in, name):
    items = listify(items)
    for item in items:
        if item not in should_in:
            raise ValueError(
                "{}: got invalided value {}, choose any in {}".format(name, item, should_in)
            )


def ensure_order(items, ordered):
    # type: (list, iter) -> list
    items = set(items)
    return [i for i in ordered if i in items]


def ensure_date_str(date):
    # type: (...) -> str
    date = to_date(date)
    return "%04d-%02d-%02d" % (date.year, date.month, date.day)


def ensure_date_int(date):
    date = to_date(date)
    return date.year * 10000 + date.month * 100 + date.day


def ensure_date_or_today_int(date):
    if date:
        return ensure_date_int(date)
    return _to_date_int(datetime.datetime.today())

def _to_date_int(date):
    # type: (datetime.datetime or datetime.date) -> int
    return date.year * 10000 + date.month * 100 + date.day


def ensure_date_range(start_date, end_date, delta=relativedelta(months=3)):
    if start_date is None and end_date is None:
        return to_date_str(datetime.date.today() - delta), to_date_str(datetime.date.today())

    if start_date is None:
        end_date = to_date(end_date)
        return to_date_str(end_date - delta), to_date_str(end_date)

    if end_date is None:
        start_date = to_date(start_date)
        return to_date_str(start_date), to_date_str(start_date + delta)

    s, e = ensure_date_str(start_date), ensure_date_str(end_date)
    if s > e:
        raise ValueError("invalid date range: [{!r}, {!r}]".format(start_date, end_date))
    return s, e
