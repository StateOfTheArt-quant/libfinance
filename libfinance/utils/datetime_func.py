#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import six
import datetime
import pandas as pd

def convert_datetime_to_str(dt):
    if dt is None:
        return None
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if isinstance(dt, six.string_types):
        return dt
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(dt, datetime.date):
        return dt.strftime("%Y-%m-%d")


def convert_dateteime_to_timestamp(dt):
    if isinstance(dt, pd.Timestamp):
        return dt
    
    if isinstance(dt, ((str, datetime.date, datetime.datetime))):
        return pd.Timestamp(dt)
    return dt