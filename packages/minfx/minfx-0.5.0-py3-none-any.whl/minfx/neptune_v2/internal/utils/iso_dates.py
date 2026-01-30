from __future__ import annotations
__all__ = ['parse_iso_date']
import datetime
DATE_FORMAT_LONG = '%Y-%m-%dT%H:%M:%S.%fZ'
DATE_FORMAT_SHORT = '%Y-%m-%dT%H:%M:%SZ'

def parse_iso_date(date):
    if isinstance(date, datetime.datetime):
        return date
    date_format = DATE_FORMAT_LONG if _is_long_date_format(date) else DATE_FORMAT_SHORT
    return datetime.datetime.strptime(date, date_format)

def _is_long_date_format(date_string):
    return len(date_string.split('.')) == 2