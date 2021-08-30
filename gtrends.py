#!/usr/bin/env python
# coding: utf-8

# for exiting loops
import sys

# for function type stubs
from typing import List

# for datetime objects
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
    Returns a DataFrame ranging from 1 to 101.

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

    return trendreq.interest_over_time() + 1


def _make_timeframe(start_date: datetime, end_date: datetime) -> str:
    """Returns a string that represents a time span delimited by the input start and end dates.

        Parameters
        ----------
        start_date: datetime
            start date for the timeframe
        end_date: datetime
            end date for the timeframe
    """
    return start_date.strftime("%Y-%m-%d") + " " + end_date.strftime("%Y-%m-%d")


def _compute_ratio(older_df: pd.DataFrame, recent_df: pd.DataFrame) -> int:
    """Takes the last row of the older dataframe and the first of the recent one and computes the ratio
    between the volume of the searches.

        Parameters
        ----------
        older_df: pd.DataFrame
            the older DataFrame with Google Trends Data
        recent_df: pd.DataFrame
            the newly fetched Google Trends DataFrame
    """

    return older_df.iloc[-1, 0] / recent_df.iloc[0, 0]


def _concat_chunk(older_df: pd.DataFrame, recent_df: pd.DataFrame) -> pd.DataFrame:
    """Scales the recent dataframe relative to the older one and concatenates the two, dropping the overlapping row

            Parameters
            ----------
            older_df: pd.DataFrame
                the older DataFrame with Google Trends Data
            recent_df: pd.DataFrame
                the newly fetched Google Trends DataFrame
    """

    ratio = _compute_ratio(older_df, recent_df)

    # scale the recent df by the ratio
    older_df /= ratio

    return pd.concat([older_df[:-1], recent_df])


def get_daily_trend(
        trendreq,
        keyword: str,
        start: str,
        end: str,
        cat: int = 0,
        geo: str = "",
        gprop: str = "",
        window: int = 90,
        verbose: bool = False,
) -> pd.DataFrame:
    """Stitch and scale consecutive daily trends data between start and end date.
    This function will first download piece-wise google trends data and then
    scale each piece using the overlapped period.

        Parameters
        ----------
        trendreq: TrendReq
            a pytrends TrendReq object
        keyword: str
            currently only support single keyword, without bracket
        start: str
            starting date in string format:YYYY-MM-DD (e.g.2017-02-19)
        end: str
            ending date in string format:YYYY-MM-DD (e.g.2017-02-19)
        cat, geo, gprop
            same as defined in pytrends
        window: int
            The length(days) of each timespan fragment for fetching google trends data,
            need to be <269 in order to obtain daily data.
        verbose: bool
            Print verbose output. Defaults to False.

    """

    # define the format for parsing
    date_format: str = "%Y-%m-%d"

    # try to convert the strings into datetime.date objects, warn if the format is wrong
    try:
        start_date: datetime.date = datetime.strptime(start, date_format).date()
        end_date: datetime.date = datetime.strptime(end, date_format).date()
    except SystemExit:
        sys.exit(f"Please provide start_date and start_time as {date_format}")

    # turn delta and overlap into a timedelta
    window: timedelta = timedelta(days=window)

    # define first chunk start and end dates, from the start of the overall time span
    chunk_start: datetime.date = start_date
    chunk_end: datetime.date = start_date + window

    # define the DataFrame to store our results
    retrieved_data: pd.DataFrame = pd.DataFrame()

    # loop until the chunk starting date is bigger than the end date
    while chunk_start < end_date:

        # create the timeframe for searches
        timespan: str = _make_timeframe(start_date=chunk_start, end_date=chunk_end)

        if verbose:
            console.print(f"Fetching '{keyword}' for period: {timespan}")

        # retrieve the first chunk of data
        chunk: pd.DataFrame = _fetch_data(
            trendreq, [keyword], timeframe=timespan, cat=cat, geo=geo, gprop=gprop
        ).drop(columns=["isPartial"], axis=1)

        # combine the chunk with the dataframe to retrieve
        # if we are in the first iteration, simply concatenate, else scale the values of the more recent chunk
        if chunk_start == start_date:
            retrieved_data = pd.concat([retrieved_data, chunk])
        else:
            retrieved_data = _concat_chunk(retrieved_data, chunk)

        # redefine chunk start and chunk end:
        # take the last index of the retrieved data and cast it to datetime.date
        chunk_start = retrieved_data.index[-1].date()
        chunk_end = chunk_start + window
        if chunk_end > end_date:
            chunk_end = end_date

    return retrieved_data


def og_get_daily_trend(trendreq, keyword: str, start: str, end: str, cat=0,
                       geo='', gprop='', delta=269, overlap=100, sleep_for=0,
                       tz=0, verbose=False) -> pd.DataFrame:
    """Stich and scale consecutive daily trends data between start and end date.
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
            The length(days) of each timeframe fragment for fetching google trends data,
            need to be <269 in order to obtain daily data.
        overlap: int
            The length(days) of the overlap period used for scaling/normalization
        tz: int
            The timezone shift in minute relative to the UTC+0 (google trends default).
            For example, correcting for UTC+8 is 480, and UTC-6 is -360
    """

    start_d = datetime.strptime(start, '%Y-%m-%d')
    init_end_d = end_d = datetime.strptime(end, '%Y-%m-%d')
    init_end_d.replace(hour=23, minute=59, second=59)
    delta = timedelta(days=delta)
    overlap = timedelta(days=overlap)

    itr_d = end_d - delta
    overlap_start = None

    df = pd.DataFrame()
    ol = pd.DataFrame()

    while end_d > start_d:
        tf = itr_d.strftime('%Y-%m-%d') + ' ' + end_d.strftime('%Y-%m-%d')
        if verbose: print('Fetching \'' + keyword + '\' for period:' + tf)
        temp = _fetch_data(trendreq, [keyword], timeframe=tf, cat=cat, geo=geo, gprop=gprop)
        temp.drop(columns=['isPartial'], inplace=True)
        temp.columns.values[0] = tf
        ol_temp = temp.copy()
        ol_temp.iloc[:, :] = None
        if overlap_start is not None:  # not first iteration
            if verbose: print('Normalize by overlapping period:' + overlap_start.strftime('%Y-%m-%d'),
                              end_d.strftime('%Y-%m-%d'))
            # normalize using the maximum value of the overlapped period
            y1 = temp.loc[overlap_start:end_d].iloc[:, 0].values.max()
            y2 = df.loc[overlap_start:end_d].iloc[:, -1].values.max()
            coef = y2 / y1
            temp = temp * coef
            ol_temp.loc[overlap_start:end_d, :] = 1

        df = pd.concat([df, temp], axis=1)
        ol = pd.concat([ol, ol_temp], axis=1)
        # shift the timeframe for next iteration
        overlap_start = itr_d
        end_d -= (delta - overlap)
        itr_d -= (delta - overlap)
        # in case of short query interval getting banned by server
        sleep(sleep_for)

    df.sort_index(inplace=True)
    ol.sort_index(inplace=True)
    # The daily trend data is missing the most recent 3-days data, need to complete with hourly data
    if df.index.max() < init_end_d:
        tf = 'now 7-d'
        hourly = _fetch_data(trendreq, [keyword], timeframe=tf, cat=cat, geo=geo, gprop=gprop)
        hourly.drop(columns=['isPartial'], inplace=True)

        # convert hourly data to daily data
        daily = hourly.groupby(hourly.index.date).sum()

        # check whether the first day data is complete (i.e. has 24 hours)
        daily['hours'] = hourly.groupby(hourly.index.date).count()
        if daily.iloc[0].loc['hours'] != 24: daily.drop(daily.index[0], inplace=True)
        daily.drop(columns='hours', inplace=True)

        daily.set_index(pd.DatetimeIndex(daily.index), inplace=True)
        daily.columns = [tf]

        ol_temp = daily.copy()
        ol_temp.iloc[:, :] = None
        # find the overlapping date
        intersect = df.index.intersection(daily.index)
        if verbose: print('Normalize by overlapping period:' + (intersect.min().strftime('%Y-%m-%d')) + ' ' + (
            intersect.max().strftime('%Y-%m-%d')))
        # scaling use the overlapped today-4 to today-7 data
        coef = df.loc[intersect].iloc[:, 0].max() / daily.loc[intersect].iloc[:, 0].max()
        daily = (daily * coef).round(decimals=0)
        ol_temp.loc[intersect, :] = 1

        df = pd.concat([daily, df], axis=1)
        ol = pd.concat([ol_temp, ol], axis=1)

    # taking averages for overlapped period
    df = df.mean(axis=1)
    ol = ol.max(axis=1)
    # merge the two dataframe (trend data and overlap flag)
    df = pd.concat([df, ol], axis=1)
    df.columns = [keyword, 'overlap']
    # Correct the timezone difference
    df.index = df.index + timedelta(minutes=tz)
    df = df[start_d:init_end_d]
    # re-normalized to the overall maximum value to have max =100
    df[keyword] = (100 * df[keyword] / df[keyword].max()).round(decimals=0)

    return df
