import numpy as np
import pandas as pd
import re

from typing import Union

from tsp.core import TSP
from tsp.misc import _is_depth_column


def read_csv(filepath: str,
              datecol: "Union[str, int]",
              datefmt: str = "%Y-%m-%d %H:%M:%S",
              depth_pattern: "Union[str, dict]" = r"^(-?[0-9\.]+)$",
              na_values:list = [],
              **kwargs) -> TSP:
    r"""Read an arbitrary CSV file 
   
    Date and time must be in a single column, and the csv must be in the
    'wide' data format (each depth is a separate column)

    Parameters
    ----------
    filepath : str
        Path to csv file
    datecol : Union[str, int]
        Either the numeric index (starting at 0) of date column (if int) or name of date column or regular expression (if str)
    datefmt : str, optional
        The format of the datetime values. Use `python strftime format codes <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes>`_, 
        by default ``"%Y-%m-%d %H:%M:%S"``
    depth_pattern : str or dict
        If string: A regular expression that matches the column names with depths. The regular expression must
        have a single capture group that extracts just the numeric part of the column header, by default r"^(-?[0-9\.]+)$".
        If column names were in the form ``"+/-1.0_m"`` (i.e. included 'm' to denote units), you could use the regular expression ``r"^(-?[0-9\.]+)_m$"``
        If a dictionary is passed, the keys must be the column names and the values are the depths. This is useful if the column names are not numeric.
    na_values : list, optional
        Additional strings to recognize as NA. Passed to pandas.read_csv, by default []

    Returns
    -------
    TSP
        A TSP
    """
    raw = pd.read_csv(filepath, na_values=na_values, **kwargs)
    
    if not datecol in raw.columns and isinstance(datecol, str):
        datecol = [re.search(datecol, c).group(1) for c in raw.columns if re.search(datecol, c)][0]
    
    if isinstance(datecol, int):
        datecol = raw.columns[datecol]

    time = pd.to_datetime(raw[datecol], format=datefmt).to_numpy()

    if isinstance(depth_pattern, str):
        depth = [re.search(depth_pattern, c).group(1) for c in raw.columns if _is_depth_column(c, depth_pattern)]
        depth_numeric = np.array([float(d) for d in depth])
    
    elif isinstance(depth_pattern, dict):
        depth = [c for c in raw.columns if c in depth_pattern.keys()]
        depth_numeric = [depth_pattern[c] for c in raw.columns if c in depth_pattern.keys()]
    
    else:
        raise ValueError("depth_pattern must be a string or dictionary")

    values = raw.loc[:, depth].to_numpy()

    t = TSP(time,
            depth_numeric,
            values,
            metadata={"source_file": filepath})

    return t