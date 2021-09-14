from pytrends.request import TrendReq
from gtrends import og_get_daily_trend as get_daily_trend

start_date = "2012-01-01"
end_date = "2021-08-31"

pytrend = TrendReq()

print("retrieve data for keyword 'euro', overlapping window 30")
euro_30 = get_daily_trend(pytrend, "Euro", start_date, end_date, overlap=30)

print("retrieve data for keyword 'euro', overlapping window 100")
euro_100 = get_daily_trend(pytrend, "Euro", start_date, end_date, overlap=100)

print("retrieve data for keyword 'european central bank', overlapping window 30")
ecb_30 = get_daily_trend(
    pytrend, "European Central Bank", start_date, end_date, overlap=30
)

print("retrieve data for keyword 'european central bank', overlapping window 100")
ecb_100 = get_daily_trend(
    pytrend, "European Central Bank", start_date, end_date, overlap=100
)

print("saving data to csv")
euro_30.to_csv("./overlapping-daily-euro_30.csv")
euro_100.to_csv("./overlapping-daily-euro_100.csv")

ecb_30.to_csv("./overlapping-daily-ecb_30.csv")
ecb_100.to_csv("./overlapping-daily-ecb_100.csv")
