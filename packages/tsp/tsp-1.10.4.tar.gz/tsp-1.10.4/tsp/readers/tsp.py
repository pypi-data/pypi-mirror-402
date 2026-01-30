import pandas as pd

from typing import  Callable

from tsp.core import TSP
from tsp.readers.csv import read_csv


def read_tsp(filepath: str) -> TSP:
    """Read a TSP-style ground temperature file

    Parameters
    ----------
    filepath : str
        Path to file.

    Returns
    -------
    TSP
        A TSP
    """
    f, n, m = _tsp_format_parse(filepath)
    t = f(filepath, n)
    return t

def _read_tsp_wide(filepath: str, n_skip) -> TSP:
    """Read a wide-format TSP file

    Parameters
    ----------
    filepath : str
        Path to file.

    Returns
    -------
    TSP
        A TSP
    """
    t = read_csv(filepath, 
                 datecol="timestamp", 
                 datefmt=None, 
                 skiprows=n_skip, 
                 depth_pattern=r"^(-?[0-9\.]+)$")
    return t

def _read_tsp_long(filepath: str, n_skip) -> TSP:
    """Read a long-format TSP file

    Parameters
    ----------
    filepath : str
        Path to file.

    Returns
    -------
    TSP
        A TSP
    """
    df = pd.read_csv(filepath, skiprows=n_skip)
    time = pd.to_datetime(df['timestamp'], format=None).to_numpy()
    depth = df['depth'].to_numpy().astype(float)
    values = df['temperature'].to_numpy()
    
    t = TSP.from_tidy_format(time, 
                             depth, 
                             values, 
                             metadata={"_source_file": filepath})
    
    return t

def _tsp_format_parse(filepath:str) -> tuple[Callable, int, list[str]]:
    """Determine the format of a TSP file

    Parameters
    ----------
    filepath : str
        Path to file.

    Returns
    -------
    function
        The function to use to read the file
    int
        The number of header lines to skip
    """
    func = None
    n_skip = 0
    metadata_lines = []

    with open(filepath, 'r') as f:
        while func is None:
            line = f.readline()
            if line.startswith("#"):
                n_skip += 1
                metadata_lines.append(line)
            elif line.startswith("timestamp,depth"):
                func = _read_tsp_long
            elif line.startswith("timestamp,"):
                func = _read_tsp_wide
            else:
                raise ValueError("File is not a valid TSP file")
    
    return func, n_skip, metadata_lines