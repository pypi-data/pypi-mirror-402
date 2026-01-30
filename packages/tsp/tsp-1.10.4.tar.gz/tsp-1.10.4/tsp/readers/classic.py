import datetime
import numpy as np
import warnings

from typing import  Optional

try:
    import netCDF4 as nc
except ModuleNotFoundError:
    warnings.warn("Missing netCDF4 library. Some functionality will be limited.")

from tsp.core import TSP, IndexedTSP


def read_classic(filepath: str, init_file: "Optional[str]"=None) -> TSP:
    """Read output from CLASSIC land surface model

    Depth values, if provided, represent the midpoint of the model cells.

    Parameters
    ----------
    filepath : str
        Path to an output file
    init_file : str
        Path to a classic init file. If provided, depth values will be calculated. Otherwise an :py:class:`~tsp.core.IndexedTSP` is returned
    
    Returns
    -------
    TSP
        An IndexedTSP. Use :py:meth:`~tsp.core.IndexedTSP.set_depths` to provide depth information if init_file is not provided.
    """
    try:
        nc
    except NameError:
        warnings.warn("netCDF4 library must be installed.")

    # tbaracc_d / tbaracc_m / tbaracc_y
    with nc.Dataset(filepath, 'r') as ncdf:
        lat = ncdf['lat'][:]
        lon = ncdf['lon'][:]
        temp = ncdf['tsl'][:]  # t, z
        
        try:
            time = nc.num2date(ncdf['time'][:], ncdf['time'].units, ncdf['time'].calendar,
                            only_use_cftime_datetimes=False,
                            only_use_python_datetimes=True)
        except ValueError:
            cf_time = nc.num2date(ncdf['time'][:], ncdf['time'].units, ncdf['time'].calendar)
            time = np.array([datetime.datetime.fromisoformat(t.isoformat()) for t in cf_time])
    
    if init_file:
        with nc.Dataset(init_file, 'r') as init:
            delz = init["DELZ"][:]
        depths = np.round(np.cumsum(delz) - np.multiply(delz, 0.5), 7)  # delz precision is lower so we get some very small offsets

    if len(lat) > 1:
        warnings.warn("Multiple points in file. Returning the first one found.")
        # TODO: return Ensemble if multiple points
        lat = lat[0]
        lon = lon[0]
        temp = temp[:,:,0,0]
    else:
        temp = temp[:,:,0,0]
    
    t = IndexedTSP(times=time,
                   values=temp,
                   latitude=lat,
                   longitude=lon,
                   metadata={"source_file": filepath})
    
    if init_file:
        t.set_depths(depths)

    return t

