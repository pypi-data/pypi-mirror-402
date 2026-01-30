import numpy as np
import pandas as pd
import re

import tsp.labels as lbl


def _is_depth_column(col_name, pattern) -> bool:
    return bool(re.search(pattern, col_name))


def completeness(df: pd.DataFrame, f1, f2) -> pd.DataFrame:
    """ Calculate completeness of an aggregated dataframe 
    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with temporal index and values equal to the number of observations
        in aggregation period
    f1 : str
        Aggregation period of data from which df is aggregated
    f2 : str
        Aggregation period of df

    Returns
    -------
    pd.DataFrame : Dataframe with completeness values as a decimal fraction [0,1]
    """
    # df must have temporal index
    C = None
    if f1 == lbl.HOURLY:
        if f2 == lbl.DAILY:
            C = df / 24
    
    elif f1 == lbl.DAILY:
        if f2 == lbl.MONTHLY:
            C = df / E_day_in_month(df)
        elif f2 == lbl.YEARLY:
            C = df / E_day_in_year(df)
    
    elif f1 == lbl.MONTHLY:
        if f2 == lbl.YEARLY:
            cnt = 12
    
    elif isinstance(f1, float) and isinstance(f1, float):
        R = f2 / f1
        C = df / R
    
    if C is None:
        raise ValueError(f"Unknown aggregation period {f1} or {f2}")
    
    return C


def df_has_period(f, *args, **kwargs):
    df = args[0] if args[0] else kwargs.get('df')
    if not isinstance(df.index, pd.PeriodIndex):
        raise ValueError("Index must be a PeriodIndex")
    return f(*args, **kwargs)


#@df_has_period
def E_day_in_year(df: "pd.DataFrame") -> "pd.DataFrame":
    """ Expected number of daily observations per year """
    leap = df.index.to_period().is_leap_year
    days = np.atleast_2d(np.where(leap, 366, 365)).transpose()
    result = pd.DataFrame(index=df.index,
                          columns=df.columns,
                          data=np.repeat(np.atleast_2d(days), df.shape[1], axis=1))
    return result


#@df_has_period
def E_month_in_year(df: "pd.DataFrame") -> "pd.DataFrame":
    """ Expected number of monthly observations per year """
    result = pd.DataFrame(index=df.index, 
                          columns=df.columns, 
                          data=12)
    return result


#@df_has_period
def E_day_in_month(df: "pd.DataFrame") -> "pd.DataFrame":
    """ Expected number of daily observations per month """
    nday = df.index.to_period().days_in_month
    result = pd.DataFrame(index=df.index, 
                          columns=df.columns, 
                          data=np.repeat(np.atleast_2d(nday).transpose(), df.shape[1], axis=1))
    return result


