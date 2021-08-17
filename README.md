# Retrieve Google Trends Data

Google Trends data is freely available, but with some caveats:

* You cannot choose the granularity of the data you retrieve. In particular, you can only retrieve daily data if you choose a monthly range.
* Data is automatically scaled: 100 is assigned to the greatest value and 0 to the smallest. This makes comparing time ranges substantially more complicated.
* On top of this, Google does *not* provide an API for retrieving data.

## Set up

Clone this repo:

```bash
git clone ""
```

And clone the environment:

```bash
conda create -f environment.yml
```

:warning: `conda` does not export environments in a format compatible across different OSes, such as Microsoft Winows and macOS.

## Project Roadmap

* Get started with PyTrends
* Retrieve monthly data:
    * From start to end of the month
    * From the 15th of one month to the 15th of the other
* Deal with 0 (add 1 to each value?)
* Use overlapping months data to scale values

## To Do

- [ ] Set up Project page in GitHub Repo? 
