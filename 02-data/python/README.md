# Files Descriptors

Each file in this folder contains the output of Python code. Every filename contains data and metadata.

## Filename Format

`source-frequency-keyword-dates/other.format`

* `source` can either be `gtrends`, i.e. retrieved without interpolation, straight from Google Trends; or `retrieved` with manipulation/harmonisation/rescaling.
* `frequency` can be `daily`, `weekly` or `monthly`.
* `keyword` is the keyword searched for, in snakecase.
* `dates/other` are some indications such as the last year for which data is retrieved, or which algorithm was used to retrieve them (e.g., `pytrends` or `overlap`).
* `.format` will aways be `.csv`.