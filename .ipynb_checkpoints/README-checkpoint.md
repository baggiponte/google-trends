# Retrieve Google Trends Data

Google Trends data is freely available, but with some caveats:

* You cannot choose the granularity of the data you retrieve. In particular, you can only retrieve daily data if you choose a range smaller than nine months.
* Data is automatically scaled: 100 is assigned to the greatest value and 0 to the smallest. This makes comparing time ranges substantially more complicated.
* On top of this, Google does *not* provide an official API for retrieving data.

:warning: **Update 15/09/2021** :warning:

It turns out that there was one piece missing in the three points above. Google Trends' Search Volume Index is not an index of all queries across the timespan of interest. In fact, the index is calculated only out of a sample of searches. Google states the sample is representative; however the data is not consistent by design. Indeed, if we look at the notebook in [`01-notebooks/03-visualisations.ipynb`](https://github.com/baggiponte/google-trends/blob/main/01-notebooks/03-visualisations.ipynb), we see that three different monthly time series report substantially different values.

What we resorted to do, in the end, was to manually retrieve data in spans of three months and concatenate them, without any attempt to rescale them.

## Set up

Clone this repo:

```bash
git clone "https://github.com/baggiponte/google-trends.git"
```

Or, when using GitHub CLI:

```bash
gh repo clone baggiponte/google-trends
```

And clone the environment:

```bash
conda create -f environment.yml
```

:warning: `conda` does not export environments in a format compatible across different OSes, such as Microsoft Winows and macOS.

## Repo Structure

* `01-notebooks` contains the python notebooks for data exploration, data retrieval and visualisations.
* `02-data` contains the data, which was either retrieved manually or via other libraries, for different purposes (e.g., data exploration or visualisations)
* `03-figures` contains the output figures.
* `Jupyter/kernels/google-trends` contains the kernel specifications for adding the environment as a Jupyter Kernel. See [here](https://ipython.readthedocs.io/en/latest/install/kernel_install.html) as reference.

## References

The original article I took inspiration from for the "overlapping rescaling method" comes from [Towards Data Science](https://towardsdatascience.com/reconstruct-google-trends-daily-data-for-extended-period-75b6ca1d3420).The original code comes from the [repo](https://github.com/qztseng/google-trends-daily) that the author of the article made. Code for the `_fetch_data()` function comes from `pytrends.get_daily_data` module. [Google Trends FAQ](https://support.google.com/trends/answer/4365533?hl=en&ref_topic=6248052) are there too.