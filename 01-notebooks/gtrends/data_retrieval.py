from gtrends.get_daily_data import (
    og_get_daily_trend as get_daily_trend,
    _make_timeframe
)

# pytrends library
from pytrends.dailydata import get_daily_data
from pytrends.request import TrendReq

# for writing functions
from typing import List

# define TrendReq object
pytrend = TrendReq()

def get_monthly_data(keyword: List[str], start, end):

