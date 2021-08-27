#!/usr/bin/env python
# coding: utf-8

# for function type stubs
from typing import List, Union

# for datetime
from datetime import datetime, timedelta
from time import sleep

# for storing data
import pandas as pd

# for scraping google trends
from pytrends.exceptions import ResponseError
from pytrends.request import TrendReq

# rich for colorful output
from rich.console import Console

# define rich console:
console = Console()


def _fetch_data(
        trendreq: TrendReq,
        kw_list: List[str],
        timeframe: str = "today 3-m",
        cat: int = 0,
        geo: str = "",
        gprop: str = "",
) -> pd.DataFrame:
    """Helper function: retrieves data from Google Trend given the keyword and the timeframe.

        Parameters
        ----------
        trendreq : TrendReq
            a pytrends TrendReq object
        kw_list: List[str]
            the keywords to retrieve
        timeframe: str
            a time window from with to retrieve data from.
        cat, geo, gprop:
            same as defined in pytrends
    """

    attempts, fetched = 0, False
    while not fetched:
        try:
            trendreq.build_payload(
                kw_list=kw_list, timeframe=timeframe, cat=cat, geo=geo, gprop=gprop
            )
        except ResponseError as err:
            console.print(err)
            console.print(f"Trying again in {60 + 5 * attempts} seconds.")
            sleep(60 + 5 * attempts)
            attempts += 1
            if attempts > 3:
                console.print("Failed after 3 attemps, abort fetching.")
                break
        else:
            fetched = True
    return trendreq.interest_over_time()


def get_daily_trend(
        trendreq,
        keyword: str,
        start: str,
        end: str,
        cat: int = 0,
        geo: str = "",
        gprop: str = "",
        delta: int = 269,
        overlap: int = 100,
        sleep_for: int = 0,
        tz: int = 0,
        verbose: bool = False,
) -> pd.DataFrame:
    """Stitch and scale consecutive daily trends data between start and end date.
    This function will first download piece-wise google trends data and then
    scale each piece using the overlapped period.

        Parameters
        ----------
        trendreq : TrendReq
            a pytrends TrendReq object
        keyword: str
            currently only support single keyword, without bracket
        start: str
            starting date in string format:YYYY-MM-DD (e.g.2017-02-19)
        end: str
            ending date in string format:YYYY-MM-DD (e.g.2017-02-19)
        cat, geo, gprop, sleep_for:
            same as defined in pytrends
        delta: int
            The length(days) of each timespan fragment for fetching google trends data,
            need to be <269 in order to obtain daily data.
        overlap: int
            The length(days) of the overlap period used for scaling/normalization
        tz: int
            The timezone shift in minute relative to the UTC+0 (google trends default).
            For example, correcting for UTC+8 is 480, and UTC-6 is -360
        verbose: bool
            Print verbose output. Defaults to False.

    """

    # define start and end date, plus the timedelta to perform the subsequent retrievals
    start_date: datetime = datetime.strptime(start, "%Y-%m-%d")
    end_date: datetime = datetime.strptime(end, "%Y-%m-%d")
    initial_end_date: datetime = datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    delta: timedelta = timedelta(days=delta)
    overlap: timedelta = timedelta(days=overlap)

    # defines the start date for the chunk to retrieve
    iteration_start_date: datetime = end_date - delta
    overlap_start = None

    # define dataframes to store the results and intermediate passages
    retrieved_data: pd.DataFrame = pd.DataFrame()
    overlay_col: pd.DataFrame = pd.DataFrame()  # a dummy col with 1/0 to indicate an overlapping period

    # start the loop to perform the data retrieval
    while end_date > start_date:
        # define time frame from iteration_start_date to iteration_end_date
        timespan = iteration_start_date.strftime("%Y-%m-%d") + " " + end_date.strftime("%Y-%m-%d")

        if verbose:
            console.print(f"Fetching '{keyword}' for period: {timespan}")

        # retrieve the chunk of data
        retrieval_loop_chunk: pd.DataFrame = _fetch_data(
            trendreq, [keyword], timeframe=timespan, cat=cat, geo=geo, gprop=gprop
        )
        retrieval_loop_chunk.drop(columns=["isPartial"], inplace=True)
        # replaces the name of the first column with the timespan
        retrieval_loop_chunk.columns.values[0] = timespan

        # create a copy of the dataframe and empty it, to retain the datetime index only
        temp_overlay_col = retrieval_loop_chunk.copy()
        temp_overlay_col.iloc[:, :] = None

        if overlap_start is not None:  # not first iteration
            if verbose:
                console.print(
                    "Normalize by overlapping period:"
                    + overlap_start.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
            # normalize using the maximum value of the overlapped period
            y1 = retrieval_loop_chunk.loc[overlap_start:end_date].iloc[:, 0].values.max()
            y2 = retrieved_data.loc[overlap_start:end_date].iloc[:, -1].values.max()
            coef = y2 / y1
            retrieval_loop_chunk = retrieval_loop_chunk * coef
            temp_overlay_col.loc[overlap_start:end_date, :] = 1

        retrieved_data = pd.concat([retrieved_data, retrieval_loop_chunk], axis=1)
        overlay_col = pd.concat([overlay_col, temp_overlay_col], axis=1)
        # shift the timespan for next iteration
        overlap_start = iteration_start_date
        end_date -= delta - overlap
        iteration_start_date -= delta - overlap
        # in case of short query interval getting banned by server
        sleep(sleep_for)

    retrieved_data.sort_index(inplace=True)
    overlay_col.sort_index(inplace=True)
    # The daily trend data is missing the most recent 3-days data, need to complete with hourly data
    if retrieved_data.index.max() < initial_end_date:
        timespan = "now 7-d"
        hourly = _fetch_data(
            trendreq, [keyword], timeframe=timespan, cat=cat, geo=geo, gprop=gprop
        )
        hourly.drop(columns=["isPartial"], inplace=True)

        # convert hourly data to daily data
        daily = hourly.groupby(hourly.index.date).sum()

        # check whether the first day data is complete (i.e. has 24 hours)
        daily["hours"] = hourly.groupby(hourly.index.date).count()
        if daily.iloc[0].loc["hours"] != 24:
            daily.drop(daily.index[0], inplace=True)
        daily.drop(columns="hours", inplace=True)

        daily.set_index(pd.DatetimeIndex(daily.index), inplace=True)
        daily.columns = [timespan]

        temp_overlay_col = daily.copy()
        temp_overlay_col.iloc[:, :] = None
        # find the overlapping date
        intersect = retrieved_data.index.intersection(daily.index)
        if verbose:
            console.print(
                "Normalize by overlapping period:"
                + (intersect.min().strftime("%Y-%m-%d"))
                + " "
                + (intersect.max().strftime("%Y-%m-%d"))
            )
        # scaling use the overlapped today-4 to today-7 data
        coef = (
                retrieved_data.loc[intersect].iloc[:, 0].max() / daily.loc[intersect].iloc[:, 0].max()
        )
        daily = (daily * coef).round(decimals=0)
        temp_overlay_col.loc[intersect, :] = 1

        retrieved_data = pd.concat([daily, retrieved_data], axis=1)
        overlay_col = pd.concat([temp_overlay_col, overlay_col], axis=1)

    # taking averages for overlapped period
    retrieved_data = retrieved_data.mean(axis=1)
    overlay_col = overlay_col.max(axis=1)
    # merge the two dataframe (trend data and overlap flag)
    retrieved_data = pd.concat([retrieved_data, overlay_col], axis=1)
    retrieved_data.columns = [keyword, "overlap"]
    # Correct the timezone difference
    retrieved_data.index = retrieved_data.index + timedelta(minutes=tz)
    retrieved_data = retrieved_data[start_date:initial_end_date]
    # re-normalized to the overall maximum value to have max =100
    retrieved_data[keyword] = (100 * retrieved_data[keyword] / retrieved_data[keyword].max()).round(decimals=0)

    return retrieved_data
