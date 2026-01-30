import numpy as np
import pandas as pd
import warnings


from pathlib import Path

from tsp.dataloggers.Vemco import Vemco
from tsp.core import IndexedTSP


def read_vemco(file_path: str) -> IndexedTSP:
    """

    Parameters
    ----------
    file_path : str

    Returns
    -------

    """
    file_extention = Path(file_path).suffix.lower()
    if file_extention in [".000", ".csv"]:
        r = Vemco()
        data = r.read(file_path)
    else:
        raise IOError("File is not .000, .csv")

    times = np.array(data['TIME'].dt.to_pydatetime())
    channels = pd.Series(data.columns).str.match("^TEMP")
    values = data.loc[:, channels.to_numpy()]

    metadata = r.META
    metadata['_source_file'] = file_path

    t = IndexedTSP(times=times, values=values.values, metadata=metadata)
    if "utc_offset" in list(r.META.keys()):
        t.set_utc_offset(r.META["utc_offset"].seconds)
    return t

