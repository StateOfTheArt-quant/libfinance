#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import pandas as pd
import json
import six
import warnings

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

from libfinance.utils.validators import (
    ensure_list_of_string,
    ensure_date_int,
    check_type,
    ensure_date_str,
    check_items_in_container,
    ensure_int,
    ensure_string,
    ensure_date_or_today_int,
    ensure_string_in,
)



VALID_TYPES = {"CS","INDX"}

class Instrument(object):
    def __init__(self, d):
        self.__dict__ = d

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                [
                    "{}={!r}".format(k.lstrip("_"), v)
                    for k, v in self.__dict__.items()
                    if v is not None
                ]
            ),
        )

    def has_citics_info(self):
        return self.type == "CS" and self.exchange in {"XSHE", "XSHG"}


def get_all_obid_to_type():
    obid_type_mapping = get_client().get_all_obid_to_type()
    return obid_type_mapping

@ttl_cache(3 * 3600)
def all_cached_obid_to_type_mapping():
    return get_all_obid_to_type()
    
def get_all_instrument_dict_list(types=["CS"]):
    all_instrument_dict_list = get_client().get_all_instrument_dict_list(types=types)
    return all_instrument_dict_list


def _all_instruments_list(type_):
    ins = [Instrument(i) for i in get_all_instrument_dict_list(type_)]
    ins.sort(key=lambda i: i.order_book_id)
    return ins

@ttl_cache(3 * 3600)
def _all_cached_instruments_list(type_):
    return _all_instruments_list(type_)

@ttl_cache(3 * 3600)
def _all_instruments_dict(type_):
    ins = _all_cached_instruments_list(type_)
    result = dict()
    for i in ins:
        result[i.order_book_id] = i
    try:
        result["沪深300"] = result["000300.XSHG"]
        result["中证500"] = result["000905.XSHG"]
        result[result["SSE180.INDX"].symbol] = result["000010.XSHG"]
    except KeyError:
        pass
    return result

def _get_instrument(type_, order_book_id):
    all_dict = _all_instruments_dict(type_)
    return all_dict[order_book_id]



@export_as_api
def instruments(order_book_ids):
    """获取证券详细信息

    :param order_book_ids: 证券ID列表, 如'000001.XSHE', 'AAPL.US'. 注意, 所有列表中的证券需要属于同一个国家。
    :param market: 证券所属国家, 如 cn, us, hk (Default value = "cn")
    :returns: 对应证券的列表

    """
    obid_to_type = all_cached_obid_to_type_mapping()
    
    if isinstance(order_book_ids, six.string_types):
        if order_book_ids not in obid_to_type:
            warnings.warn('unknown order_book_id: {}'.format(order_book_ids))
            return
        ob_type = obid_to_type[order_book_ids]
        return _get_instrument(ob_type, order_book_ids)
    result = []
    for ob in order_book_ids:
        if ob not in obid_to_type:
            continue
        ob_type = obid_to_type[ob]
        result.append(_get_instrument(ob_type, ob))
    return result

@export_as_api
def all_instruments(type=None, date=None, **kwargs):
    """获得某个国家的全部证券信息

    :param type:  (Default value = None)
    :param date:  (Default value = None)
    :param market: cn, hk (Default value = "cn")
    :kwargs
        trading_market: [hk, all] (Default value = "hk")
            hk: 港交所可购买的股票。对应返回stock_connect = null、sh、sz 的记录
            all: 包括港交所、上交所、深交所可购买的港股。（对沪深港通支持股票均展示一条独立的unique_id捆绑的信息）,对应返回全部列表，即stock_connect = null、sz_and_sh、sh、sz、sz_connect、sh_connect
    """

    if type is not None:
        type = ensure_list_of_string(type)
        itype = set()
        for t in type:
            if t.upper() == "STOCK":
                itype.add("CS")
            elif t.upper() == "FUND":
                itype = itype.union({"ETF", "LOF", "FUND"})
            elif t.upper() == "INDEX":
                itype.add("INDX")
            elif t not in VALID_TYPES:
                raise ValueError("invalid type: {}, chose any in {}".format(type, VALID_TYPES))
            else:
                itype.add(t)
    else:
        itype = VALID_TYPES

    if date:
        date = ensure_date_str(date)
        cond = lambda x: (  # noqa: E731
                (itype is None or x.type in itype)
                and (x.listed_date <= date or x.listed_date == "0000-00-00")
                and (
                        x.de_listed_date == "0000-00-00"
                        or (
                                x.de_listed_date >= date
                                and x.type in ("Future", "Option")
                                or (x.de_listed_date > date and x.type not in ("Future", "Option"))
                        )
                )
        )
    else:
        cond = lambda x: itype is None or x.type in itype  # noqa: E731
    cached = kwargs.pop("cached", True)

    if cached:
        get_instrument_list = _all_cached_instruments_list
    else:
        get_instrument_list = _all_instruments_list

    ins_ret = []
    for t in itype:
        ins_ret.extend(filter(cond, get_instrument_list(t)))
    if itype is not None and len(itype) == 1:
        df = pd.DataFrame([v.__dict__ for v in ins_ret])
        internal_fields = [f for f in df.columns if f.startswith('_')]
        for f in internal_fields:
            del df[f]
    else:
        df = pd.DataFrame(
            [
                (
                    v.order_book_id,
                    v.symbol,
                    getattr(v, "abbrev_symbol", None),
                    v.type,
                    v.listed_date,
                    v.de_listed_date,
                )
                for v in ins_ret
            ],
            columns=[
                "order_book_id",
                "symbol",
                "abbrev_symbol",
                "type",
                "listed_date",
                "de_listed_date",
            ],
        )
    return df


if __name__ == "__main__":
    #all_instrument_dict_list = get_all_instrument_dict_list(types="CS")
    #all_instrument_dict_list1 = get_all_instrument_dict_list(types=["CS"])
    #all_instrument_dict_list2 = get_all_instrument_dict_list(types=["INDX"])
    #all_instrument_dict_list2 = get_all_instrument_dict_list(types=["CS","INDX"])
    
    #instrument_df = all_instruments()
    stock_instrument_df = all_instruments(type="CS")
    #obid_type_mapping = get_all_obid_to_type()
    
    
    instrument_list = instruments(order_book_ids=["000001.XSHE","000300.XSHG"])
    
    
    
    