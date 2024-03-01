#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from typing import Any, Union, Optional, Iterable, Dict, List, Sequence, Iterable

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

@export_as_api
def get_instrument_industry(order_book_ids: list, date: Union[str, datetime.datetime], source: str = "010303") -> pd.DataFrame():
    
    return get_client().get_instrument_industry(order_book_ids=order_book_ids, date=date, source=source)

@export_as_api
def get_index_weights(index_id: str = "000300.XSHG", date: Union[str, datetime.datetime] = None) -> pd.DataFrame:
    return get_client().get_index_weights(index_id=index_id, date = date)
    

