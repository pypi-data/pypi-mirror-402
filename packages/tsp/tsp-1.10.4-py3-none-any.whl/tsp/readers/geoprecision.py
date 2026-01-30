import numpy as np

from tsp.dataloggers.Geoprecision import detect_geoprecision_type

from tsp.core import  IndexedTSP
from .csv import read_csv


def read_geoprecision(filepath: str) -> IndexedTSP:
    """Read a Geoprecision datalogger export (text file)

    Reads GP5W- and FG2-style files from geoprecision.

    Parameters
    ----------
    filepath : str
        Path to file.

    Returns
    -------
    IndexedTSP
        An IndexedTSP
    """
    Reader = detect_geoprecision_type(filepath)
    
    if Reader is None:
        raise RuntimeError("Could not detect type of geoprecision file (GP5W or FG2 missing from header")
    reader = Reader()
    
    data = reader.read(filepath)
    metadata = reader.META
    metadata['_source_file'] = filepath
    t = IndexedTSP(times=np.array(data['TIME'].dt.to_pydatetime()),
                     values=data.drop("TIME", axis=1).values,
                     metadata=metadata)

    return t