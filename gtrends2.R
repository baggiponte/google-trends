library(gtrendsR)
library(glue)
library(tidyverse)

make_timespan <- function(start_date, end_date) {
  # ----------------------------------------------------------------
  # returns a timespan like "%Y-%m-%d %Y-%m-%d" to give to gtrends()
  # ----------------------------------------------------------------
  
  glue::glue("{start_date} {end_date}")
}

retrieve_data <- function(keyword, timespan, loop_number) {
  # ------------------------------------------------
  # retrieves interest over time from google trends,
  # retains only three columns: date, hits, keywords
  # adds a column for the iteration number
  # turns values smaller than one into ones
  # ------------------------------------------------
  
  gtrends(keyword, time = timespan)$interest_over_time %>%
    as_tibble() %>% 
    # only select columns we need
    select(1:3) %>% 
    mutate(
      # keep track of the fetch
      loop = loop_number,
      # convert strings into integers
      hits = case_when(
        hits == "<1" ~ "1",
        TRUE ~ hits %>% as.character()
      ) %>% as.integer() + 1
    )
}

scale_series <- function(older_chunk, newer_chunk) {
  # ---------------------------------------------------------------------------------
  # Two consecutive google trend series are retrieved with one observation of overlap
  # This function computes the ratio between the two overlapping values and 
  # scales the values of the second series by this ratio, so that later it can 
  # be concatenated with the previous one
  # ---------------------------------------------------------------------------------
  
  # safety measure: if there is no overlap, exit
  if (!older_chunk$date %>% tail(1) == newer_chunk$date %>% head(1)) {
    stop(
      "The last date of the older chunk does not correspond to the first date of the newer chunk",
      call. = FALSE
    )
  } 
  
  # compute the ratio used to scale the newest series
  ratio <- newer_chunk$hits %>% head(1) / older_chunk$hits %>% tail(1)
  
  newer_chunk %>% 
    mutate(hits = (hits / ratio) %>% round())
}

concatenate_series <- function(older_chunk, newer_chunk) {
  # ---------------------------------------------------------------------------------
  # Concatenates two consecutive google trend series.
  # Scales the second series relative to the first one, then drops all observations
  # in the first one prior to the split date (i.e., the first row of the new series).
  # Finally, scales the resulting series back to the range 1-100
  # ---------------------------------------------------------------------------------
  
  # define the split date to drop the observation of the older chunk
  split_date <- older_chunk$date %>% tail(1)
  
  newer_chunk <- newer_chunk %>%
    # scale newer chunk relative to the older one
    scale_series(older_chunk, .)
  
  older_chunk %>%
    # take out the last row
    filter(date < split_date) %>% 
    # append rows
    bind_rows(newer_chunk) %>% 
    # scale the whole series
    mutate(hits = (hits / max(hits) * 100) %>% round())
}

retrieve_daily_data <- function(start, end, keyword, verbose = FALSE) {
  # -----------------------------------------------------
  # Retrieves daily data for any keyword in Google Trends
  # -----------------------------------------------------
  
  # **********************************
  # 1. setup and retrieve first series
  # **********************************
  
  # parse them as datetime objects - needed for adding days
  start_date <- start %>% lubridate::ymd()
  end_date <- end %>% lubridate::ymd()
  
  # create window for sliding
  window <- lubridate::days(269)
  
  # create chunk starting and ending dates
  chunk_start <- start_date
  chunk_end <- start_date + window
  
  # define span
  chunk_span <- make_timespan(chunk_start, chunk_end)
  
  # define variable to count iterations
  loop <- 0
  
  # first retrieval
  print(glue::glue("Loop {loop}: retrieving data from {chunk_start} to {chunk_end}"))
  first_chunk <- retrieve_data(keyword, chunk_span, loop)
  
  # ********************************
  # 2. initialise loop to retrieve data
  # ********************************
  
  while (chunk_end < end_date) {
    
    loop <- loop + 1  
    
    # *************************
    # pause loop to prevent ban
    # *************************
    
    if (loop %% 15 == 0) {
      sleep_for <- 60 + runif(1,1,20) %>% round()
      print(glue::glue("Sleep for {sleep_for} seconds to prevent ban"))
      Sys.sleep(sleep_for)
    }
    
    # *****************
    # shift time window
    # *****************
    
    chunk_start <- chunk_start + window

    # if chunk_end > end_date, chunk_end = end_date
    if ( (chunk_start + window) > end_date ) {
      chunk_end <- end_date
    } else {
      chunk_end <- chunk_start + window
    }
    
    # define new span
    chunk_span <- make_timespan(chunk_start, chunk_end)
    
    # perform another retrieval
    print(glue::glue("Loop {loop}: retrieving data from {chunk_start} to {chunk_end}"))
    second_chunk <- retrieve_data(keyword, chunk_span, loop)
    
    first_chunk <- concatenate_series(first_chunk, second_chunk)

  }
  
  return(first_chunk)
  
}

test <- retrieve_daily_data(start = "2012-01-01", end = "2021-08-28", keyword="Mario Draghi")

test
