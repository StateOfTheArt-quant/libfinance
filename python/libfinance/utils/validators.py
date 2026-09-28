import warnings
import datetime

from dateutil.relativedelta import relativedelta
from six import string_types, binary_type, text_type
from libfinance.utils.utils import listify, to_date, is_panel_removed, to_date_int, to_date_str

def ensure_list_of_string(s, name=""):
    if isinstance(s, string_types):
        return [s]

    result = list(s)
    for v in result:
        if not isinstance(v, string_types):
            raise ValueError("{}: expect string or list of string, got {!r}".format(name, v))
    return result


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


def ensure_instruments(order_book_ids, type=None, as_of=None):
    r"""代码 -> Instrument 列表。

    ``as_of`` 是\ **数据时间**\ （要哪一段的数据），按它解析代码表 —— 与服务端
    ``compose/price.py`` 同口径。不传就按今天的表解析。

    不带 as_of 时，已退市的证券在今天的表里不存在，这里会把它当成"无效代码"整个丢掉，
    于是 ``get_price(['600837.XSHG'], '2022-09-01', '2022-09-20')`` 在\ **客户端**\ 就被
    拒了 —— 哪怕服务端已经能按 2022 年的表解析它。
    """
    order_book_ids = ensure_list_of_string(order_book_ids)
    from libfinance.api.instrument import all_cached_obid_to_type_mapping, _get_instrument

    obid_to_type = all_cached_obid_to_type_mapping(as_of=as_of)
    result = []
    obid_set = set()
    for ob in order_book_ids:
        if ob not in obid_to_type:
            warnings.warn("invalid order_book_id: {}".format(ob), stacklevel=0)
            continue
        ob_type = obid_to_type[ob]
        if ob in obid_set:
            continue
        obid_set.add(ob)
        if type is not None and ob_type != type:
            warnings.warn(
                "expect {} instrument, got {}({}), ignored".format(type, ob_type, ob), stacklevel=0
            )
            continue
        instrument = _get_instrument(ob_type, ob, as_of=as_of)
        result.append(instrument)
    if not result:
        raise ValueError("order_book_ids: at least one valid instrument expected, got none")
    return result

if __name__ == "__main__":
    order_book_ids = ["000001.XSHE","000300.XSHG"]
    
    instrument_list = ensure_instruments(order_book_ids)
    
    
    