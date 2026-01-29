# Teaspoon

## See the full documentation on the [ReadTheDocs Pages](https://permafrostnet.gitlab.io/teaspoon/source/about.html)

## [What is it?](https://permafrostnet.gitlab.io/teaspoon/source/about.html)
`tsp` ('teaspoon') is a python library designed to make working with permafrost ground temperature time series data more straightforward, efficient, and reproduceable. Some of the features include:

* Read a variety of common published data formats, datalogger outputs, and model results into a common data structure
    * GEOtop model output
    * GTN-P database export csv
    * NTGS ground temperature report csv
    * Geoprecision datalogger export
    * HoboWare datalogger export
* Export data in a variety of common formats
    * TSP-recommended csv format
    * netcdf
    * 'GTN-P'-style csv
    * 'NTGS'-style csv
* Perform common data transformations
    * Calculate daily, monthly, or yearly means, ignoring averaging periods with missing data
    * Switch between "long" and "wide" dataframes
* Visualize and explore your data with commonly used plots
    * Trumpet curves
    * Temperature-time graphs
    * Colour-contour profiles

## [Installation](https://permafrostnet.gitlab.io/teaspoon/source/install.html)

## [Usage Examples](https://permafrostnet.gitlab.io/teaspoon/source/examples.html)

## [How to contribute](https://permafrostnet.gitlab.io/teaspoon/source/contributions.html)

## Data Standard
TSP also defines a recommended csv format for ground temperature data (which can also be extended to many other kinds of permafrost data). It is described in the [DATA_STANDARD.md](./DATA_STANDARD.md) file in this directory. Files can be read (using the `TSP.to_csv` method) and written (using `read_tsp`) using the teaspoon software package. 

## Citation
If you find this software helpful, please consider using the following citation:

> Brown, N., (2022). tsp ("Teaspoon"): A library for ground temperature data. Journal of Open Source Software, 7(77), 4704, [https://doi.org/10.21105/joss.04704](https://doi.org/10.21105/joss.04704)
