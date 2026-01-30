import datetime
import json
import numpy as np
import pandas as pd
import warnings

from pathlib import Path

from tsp.core import TSP
from tsp.gtnp import GtnpMetadata
from tsp.readers.csv import read_csv


def read_gtnp(filename: str, metadata_filepath:str=None, allow_multiple_sites=False) -> TSP | dict[str, TSP]:
    """Read GTN-P database export
    Parameters
    ----------
    filename : str
        Path to file.
    metadata_filepath : str, optional
        Path to GTN-P metadata file, by default None. If provided
    allow_multiple_sites : bool, optional
        Whether to allow multiple TSPs to be returned (for post-2026 GTN-P files), by default False. If true,
        the function will return a dictionary of TSPs keyed by dataset_id.
    
    Returns
    -------
    TSP | dict[str, TSP]
        A TSP or dictionary of TSPs keyed by dataset_id (if allow_multiple_sites=True). 
    """
    reader = _get_gtnp_reader(filename)
    result = reader(filename, metadata_filepath)

    if isinstance(result, dict):
        if allow_multiple_sites:
            return result
        elif not allow_multiple_sites and len(result.keys()) > 1:
            raise ValueError("Multiple TSPs found in file. Use allow_multiple_sites=True to return all TSPs as a list.")
        else:
            return list(result.values())[0]
    
    return result


def _get_gtnp_reader(filename: str):
    with open(filename, 'r') as f:
        first_line = f.readline()
        if "Date/Depth" in first_line:
            return read_gtnp_legacy
        elif "dataset_id" in first_line:
            return read_gtnp_v2
        else:
            raise ValueError("File is not a GTN-P export or metadata file.")
        

def read_gtnp_legacy(filename: str,
                     metadata_filepath=None,
                     autodetect_metadata=True) -> TSP:
    """Read file from GTN-P database export (pre-2026)

    Parameters
    ----------
    filename : str
        Path to file.
    metadata_filepath : str, optional
        Path to GTN-P metadata file (), by default None

    Returns
    -------
    TSP
        A TSP
    """

    t = read_csv(filename,
                   na_values=[-999.0],
                   datecol="Date/Depth",
                   datefmt="%Y-%m-%d %H:%M:%S",
                   depth_pattern=r"^(-?[0-9\.]+)$")

    # try to automatically detect metadata file
    if metadata_filepath is None and autodetect_metadata:
        partial_name = Path(filename).stem
       
        while partial_name:
            test_metadata = Path(Path(filename).parent, partial_name).with_suffix(".metadata.txt")
        
            if test_metadata.is_file():
                metadata_filepath = test_metadata
                break
            else:
                partial_name = partial_name[:-1]

    if metadata_filepath is not None:
        try:
            meta = GtnpMetadata(metadata_filepath)
        except Exception as e:
            warnings.warn(f"Failed to read metadata file: {e}")
            return t
        t.metadata['raw'] = meta.raw
        t.metadata['parsed'] = meta.parsed

        # set time zone
        tz = meta.get_timezone()
        if tz:
            t.set_utc_offset(int(tz.utcoffset(datetime.datetime.now()).total_seconds()))
        
        # set location
        t.latitude = meta.get_latitude() if meta.get_latitude() else None
        t.longitude = meta.get_longitude() if meta.get_longitude() else None

    t.metadata['_source_file'] = filename

    return t


def read_gtnp_v2(file: str, metadata_filepath: str=None) -> "dict[str:TSP]":
    """Read GTN-P v2 (2026) format file

    Parameters
    ----------
    file : str
        Path to file.
    metadata_filepath : str, optional
        Path to GTN-P 2026 metadata JSON file, by default None

    Returns
    -------
    dict[str:TSP]
        A dictionary of TSPs keyed by dataset_id
    """
    output = dict()
    raw = pd.read_csv(file)

    if 'date' in raw.columns:
        raw['timestamp'] = pd.to_datetime(raw['date'], format="%Y-%m-%d")
    elif 'utc_time' in raw.columns:
        raw['timestamp'] = pd.to_datetime(raw['utc_time'], format="%Y-%m-%d %H:%M:%S")
    else:
        raise ValueError("No date or utc_time column found in file")
    
    grouped = raw.groupby("dataset_id")  

    for id, group in grouped:
        times, depths, values = _parse_gtnp_subset(group)
        
        if metadata_filepath:
            all_metadata = _read_gtnp_v2_metadata_json(metadata_filepath)
            matching_meta = [m for m in all_metadata if m.get("id") == id]
        
            if matching_meta:
                metadata = matching_meta[0]
            else:
                raise ValueError(f"No matching metadata found for dataset_id {id}")

            essential = _parse_gtnp_v2_essential_metadata(metadata)
        
        else:
            metadata = {"dataset_id": id}
            essential = {}
        
        t = TSP.from_tidy_format(times=times,
                                 depths=depths,
                                 values=values,
                                 latitude=essential.get('latitude', None),
                                 longitude=essential.get('longitude', None),
                                 site_id=essential.get('site_id', None),
                                 metadata=metadata)
        
        output[str(id)] = t

    return output


def _parse_gtnp_subset(group: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    depths = group['depth']
    times = group['timestamp']
    values = group['temperature']
    
    return times, depths.to_numpy(), values.to_numpy()


def _parse_gtnp_v2_essential_metadata(md: dict) -> dict:
    output = dict()
    
    bh = md.get('borehole', {})
    output['site_id'] = bh.get('site_id', None)

    loc = bh.get('location', {})
    output['elevation'] = loc.get('elevation', None)
    output['latitude'] = loc.get('latitude', None)
    output['longitude'] = loc.get('longitude', None)

    return output


def _read_gtnp_v2_metadata_json(file: str) -> list[dict]:
    with open(file, 'r') as f:
        metadata = json.load(f)
    
    return metadata