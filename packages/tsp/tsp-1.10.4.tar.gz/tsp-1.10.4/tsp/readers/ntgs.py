
import numpy as np
import pandas as pd
import re

from pathlib import Path

from tsp.core import TSP


def read_ntgs_gtr(filename: str) -> TSP:
    """Read a file from the NTGS permafrost ground temperature report

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    TSP
        A TSP
    """
    if Path(filename).suffix == ".csv":
        try:
            raw = pd.read_csv(filename, 
                              keep_default_na=False,na_values=[''], 
                              parse_dates={"time": ["date_YYYY-MM-DD","time_HH:MM:SS"]})
        except IndexError:
            raise IndexError("There are insufficient columns, the file format is invalid.")
    elif Path(filename).suffix in [".xls", ".xlsx"]:
        try:
            raw = pd.read_excel(filename, 
                                sheet_name=1, parse_dates=False)
            # Avoid any excel date nonsense
            safe_date = raw.pop('date_YYYY-MM-DD').astype(str).str.extract(r"([0-9]{4}-[0-9]{2}-[0-9]{2})") 
            safe_time = raw.pop('time_HH:MM:SS').astype(str).str.extract(r"([0-9]{2}:[0-9]{2}:[0-9]{2})") 
            raw.insert(0, 'time', safe_date[0] + " " + safe_time[0])
            raw['time'] = pd.to_datetime(raw['time'], format="%Y-%m-%d %H:%M:%S")
        except IndexError:
            raise IndexError("There are insufficient columns, the file format is invalid.") 
    else:
        raise TypeError("Unsupported file extension.")
    
    metadata = {
                'project_name': raw['project_name'].values[0],
                '_site_id': raw['site_id'].values[0],
                '_latitude': raw['latitude'].values[0],
                '_longitude': raw['longitude'].values[0],
                '_source_file': filename
                }
    match_depths = [c for c in [re.search(r"(-?[0-9\.]+)_m$", C) for C in raw.columns] if c]
    values = raw.loc[:, [d.group(0) for d in match_depths]].values
    times = np.array(raw['time'].dt.to_pydatetime())
        
    t = TSP(times=times,
              depths=[float(d.group(1)) for d in match_depths],
              values=values,
              latitude=raw['latitude'].values[0],
              longitude=raw['longitude'].values[0],
              site_id=raw['site_id'].values[0],
              metadata=metadata)
    
    return t


def read_ntgs_db(filename:str) -> dict[str, TSP]:
    """Read a file from the NTGS permafrost database export

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    dict[str, TSP]
        A dictionary of TSPs, keyed by SITE_ID
    """
    df = pd.read_csv(filename, parse_dates=['MEASUREMENT_DATETIME'])
    grouped = df.groupby("SITE_ID")
    wide_dict = {name:__parse_ntgs_db_df(data, site_id=name) for name, data in grouped}
    
    for name, tsp_obj in wide_dict.items():
        tsp_obj.metadata['_source_file'] = filename
        tsp_obj.metadata['_site_id'] = name

    return wide_dict


def read_ntgs_db_single(filename:str, 
                        select = None, 
                        duplicate_depths='mean') -> TSP:
    """Read a file from the NTGS permafrost database export with a single TSP output
    Parameters
    ----------
    filename : str
        Path to file.
    select : str, int, optional
        How to handle multiple SITE_IDs in the file. If an integer, it is treated as the index of the SITE_ID to use (0-based). 
        If a string, treat it as the site ID to use. If None, an error is raised if multiple SITE_IDs are found.
    duplicate_depths : str, optional
        How to handle duplicate depth measurements. Options are 'mean' (default), 'error'
    Returns
    -------
    TSP
        A TSP
    """
    df = pd.read_csv(filename)
    
    if len(df['SITE_ID'].unique()) > 1 and select is None:
        raise ValueError("Multiple SITE_IDs found in file.")
    elif len(df['SITE_ID'].unique()) > 1 and isinstance(select, int):
        df = df[df['SITE_ID'] == df['SITE_ID'].unique()[select]]
    elif len(df['SITE_ID'].unique()) > 1 and isinstance(select, str):
        df = df[df['SITE_ID'] == select]
    
    metadata = {'_source_file': filename,
                '_site_id': df['SITE_ID'].unique()[0]}
    
    t = __parse_ntgs_db_df(df, duplicate_depths=duplicate_depths, site_id=metadata['_site_id'])
    t.metadata.update(metadata)
    return t


def __parse_ntgs_db_df(df:pd.DataFrame, site_id=None, duplicate_depths='mean') -> TSP:
    wide = df.pivot_table(index='MEASUREMENT_DATETIME',
                          columns='DEPTH_M',
                          values='TEMPERATURE_C',
                          aggfunc=duplicate_depths).reset_index()
    
    times = wide.pop('MEASUREMENT_DATETIME').to_numpy()
    depths = wide.columns.to_numpy().astype(float)
    values = wide.to_numpy()
    
    t = TSP(times=times,
            depths=depths,
            values=values,
            site_id=site_id)
    
    return t


def read_ntgs(filename: str, allow_multiple_sites=False) -> TSP | dict[str, TSP]:
    """Read a NTGS file. 

    Parameters
    ----------
    filename : str
        Path to file.
    
    Returns
    -------
    TSP | dict[str, TSP]
        A TSP or a dictionary of TSPs with SITE_ID as keys if multiple SITE_IDs are found and `allow_multiple_sites` is True.

    Description
    -----------
    Attempts to read the file as a ground temperature report file first. If that fails, attempts to read
    it as a database export. If multiple SITE_IDs are found in the database export, 
    a dictionary of TSPs is returned if `allow_multiple_sites` is True.
    """
    try:
        return read_ntgs_gtr(filename)
    except Exception:
        dict_t = read_ntgs_db(filename)
    
        if len(dict_t.keys()) == 1:
            return list(dict_t.values())[0]
        
        elif allow_multiple_sites:
            return dict_t
            
        else:
            raise ValueError(f"Found {len(dict_t.keys())} unique SITE_ID values in file. "
                              "Use read_ntgs_db() or set `allow_multiple_sites=True` to return all sites as a dictionary.")

