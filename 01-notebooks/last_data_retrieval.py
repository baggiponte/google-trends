from pytrends.request import TrendReq
from gtrends import og_get_daily_trend as get_daily_trend

start_date = "2012-01-01"
end_date = "2021-08-31"

pytrend = TrendReq()

print("retrieve data for keyword 'euro'")
euro = get_daily_trend(pytrend, "Euro", start_date, end_date, sleep_for=5)

print("retrieve data for keyword 'european central bank'")
ecb = get_daily_trend(
    pytrend, "European Central Bank", start_date, end_date, sleep_for=5
)

print("saving data to csv")
euro.to_csv("./overlapping-daily-euro.csv")
ecb.to_csv("./overlapping-daily-ecb.csv")
