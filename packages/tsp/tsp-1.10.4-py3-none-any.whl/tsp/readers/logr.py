import numpy as np
import pandas as pd
import warnings

from typing import Union
from tsp.dataloggers.logr import LogR, guessed_depths_ok

from tsp.core import TSP, IndexedTSP


def read_logr(filepath: str, cfg_txt: str = None) -> "Union[IndexedTSP,TSP]":
    """Read a LogR datalogger export (text file)

    Reads LogR ULogC16-32 files.

    Parameters
    ----------
    filepath : str
        Path to file.
    cfg_txt : str, optional
        Path of the config text file containing of the logger. Required if raw is True.

    Returns
    -------
    IndexedTSP, TSP
        An IndexedTSP or TSP, depending on whether the depth labels are sensible
    """
    r = LogR()
    data = r.read(file=filepath, cfg_txt=cfg_txt)
    times = np.array(np.array(data['TIME'].dt.to_pydatetime()))
    channels = pd.Series(data.columns).str.match("^CH")
    values = data.loc[:, channels.to_numpy()]
    metadata = r.META
    metadata['_source_file'] = filepath

    if guessed_depths_ok(metadata['guessed_depths'], sum(channels)):
        t = TSP(times=times,
                depths=metadata['guessed_depths'][-sum(channels):],
                values=values.values,)

    else:
        warnings.warn(f"Could not convert all channel labels into numeric depths."
                      "Use the set_depths() method to specify observation depths."
                      "Guessed depths can be accessed from .metadata['guessed_depths'].")
                      
        t = IndexedTSP(times=times,
                       values=values.values,
                       metadata = metadata)

    return t
