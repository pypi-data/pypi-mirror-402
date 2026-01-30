import numpy as np
import pandas as pd

from pathlib import Path

from tsp.dataloggers.RBRXL800 import RBRXL800
from tsp.dataloggers.RBRXR420 import RBRXR420
from tsp.core import IndexedTSP


def read_rbr(file_path: str) -> IndexedTSP:
    """

    Parameters
    ----------
    file_path : str

    Returns
    -------

    """
    file_extension = Path(file_path).suffix.lower()
    if file_extension in [".dat", ".hex"]:
        with open(file_path, "r") as f:
            first_line = f.readline()
            model = first_line.split()[1]
            if model == "XL-800":
                r = RBRXL800()
            elif model in ["XR-420", "XR-420-T8"]:
                r = RBRXR420()
            else:
                raise ValueError(f"logger model {model} unsupported")
            data = r.read(file_path)
    elif file_extension in [".xls", ".xlsx", ".rsk"]:
        r = RBRXR420()
        data = r.read(file_path)
    else:
        raise IOError("File is not .dat, .hex, .xls, .xlsx, or .rsk")

    times = np.array(data['TIME'].dt.to_pydatetime())
    channels = pd.Series(data.columns).str.match("^ch")
    values = data.loc[:, channels.to_numpy()]

    metadata = r.META
    metadata['_source_file'] = file_path

    t = IndexedTSP(times=times, values=values.values, metadata=metadata)
    if "utc_offset" in list(r.META.keys()):
        t.set_utc_offset(r.META["utc_offset"])

    return t

