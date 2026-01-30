import pandas as pd

from tsp.core import TSP


def read_permos(filepath:str) -> TSP:
    """Read file from PERMOS database export

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    TSP
        A TSP

    Used for data obtained from PERMOS (permos.ch/data-portal/permafrost-temperature-and-active-layer)
    """
    try:
        raw = pd.read_csv(filepath,
                          index_col=0,
                          parse_dates=True)
    except IndexError:
        raise IndexError("There are insufficient columns, the file format is invalid.")
    metadata = {
                '_source_file': filepath
    }
    t = TSP(times=raw.index,
            depths=[float(C) for C in raw.columns],
            values=raw.values,
            metadata=metadata)
    
    return t