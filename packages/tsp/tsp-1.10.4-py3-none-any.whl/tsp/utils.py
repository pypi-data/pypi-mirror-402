import pandas as pd
import numpy as np
import warnings

import tsp
from tsp import TSP


def resolve_duplicate_times(t: TSP, keep="first") -> TSP:
    """Eliminate duplicate times in a TSP.
    
    Parameters
    ----------
    tsp : TSP
        TSP to resolve duplicate times in.
    keep : str, optional
        Method to resolve duplicate times. Chosen from "first", "average", "last", "strip"
        by default "first"
    
    Returns
    -------
    TSP
        TSP with no duplicated times."""
    resolver = _get_duplicate_resolver(keep)
    return resolver(t)
    

def _get_duplicate_resolver(keep: str):
    if keep == "first":
        return _first_duplicate_time
    elif keep == "average":
        return _average_duplicate_time
    elif keep == "last":
        return _last_duplicate_time
    elif keep == "strip":
        return _strip_duplicate_time
    else:
        raise ValueError(f"Unknown duplicate resolver method: {keep}")


def _first_duplicate_time(t: TSP):
    df = t.wide
    df = df[~df.index.duplicated(keep="first")]
    
    time = df.index
    values = df.drop(['time'], axis=1).values
    depths = df.drop(['time'], axis=1).columns
    
    t_new = TSP(times=time, values=values, depths=depths, 
                latitude=t.latitude, longitude=t.longitude,
                site_id=t.site_id, metadata=t.metadata)
    
    return t_new


def _last_duplicate_time(t: TSP):
    df = t.wide
    df = df[~df.index.duplicated(keep="last")]
    
    time = df.index
    values = df.drop(['time'], axis=1).values
    depths = df.drop(['time'], axis=1).columns
    
    t_new = TSP(times=time, values=values, depths=depths, 
                latitude=t.latitude, longitude=t.longitude,
                site_id=t.site_id, metadata=t.metadata)
    
    return t_new


def _strip_duplicate_time(t: TSP):
    df = t.wide
    df = df[~df.index.duplicated(keep=False)]

    time = df.index
    values = df.drop(['time'], axis=1).values
    depths = df.drop(['time'], axis=1).columns
    
    t_new = TSP(times=time, values=values, depths=depths, 
                latitude=t.latitude, longitude=t.longitude,
                site_id=t.site_id, metadata=t.metadata)
    
    return t_new


def _average_duplicate_time(t: TSP):
    singleton = t.wide[~t.wide.index.duplicated(keep=False)]
    duplicated = t.wide[t.wide.index.duplicated(keep=False)].drop(['time'], axis=1).reset_index()
    averaged = duplicated.groupby(duplicated['index']).apply(lambda x: x[~x.isna()].mean(numeric_only=True))  
    averaged.insert(0, 'time',averaged.index)

    df = pd.concat([singleton, averaged], ignore_index=False).sort_index()

    time = df.index
    values = df.drop(['time'], axis=1).values
    depths = df.drop(['time'], axis=1).columns

    t_new = TSP(times=time, values=values, depths=depths, 
                latitude=t.latitude, longitude=t.longitude,
                site_id=t.site_id, metadata=t.metadata)
    
    return t_new


def midnight_offset_24_hr(t: TSP, reverse: bool = False) -> TSP:
    """ (de-)increment any timestamps that are exactly at midnight by 24 hours.
    
    Description:
    -----------
    Some dataloggers misattribute data at midnight to the previous day 
    which can cause problems when plotting or analyzing data. This function
    corrects any timestamps that are exactly at midnight by adding/subtracting 24 hours.
    """
    
    values = t.values.copy()
    midnight_indices = np.where(t.times.hour==0)[0]
    times = t.times.to_numpy().copy()
    if len(midnight_indices) > 0:
        if reverse:
            times[midnight_indices] -= np.timedelta64(24, 'h')
        else:
            times[midnight_indices] += np.timedelta64(24, 'h')
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=tsp.tspwarnings.NonIncreasingTimesWarning)
        
    t_new = TSP(times=times, values=values, depths=t.depths,
                latitude=t.latitude, longitude=t.longitude,
                site_id=t.site_id, metadata=t.metadata)
    
    return t_new
