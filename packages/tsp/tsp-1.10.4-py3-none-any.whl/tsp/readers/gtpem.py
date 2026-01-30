import warnings

try:
    import netCDF4 as nc
except ModuleNotFoundError:
    warnings.warn("Missing netCDF4 library. Some functionality will be limited.")

from tsp.core import TSP


def read_gtpem(file: str) -> "list[TSP]":
    output = list()
    try:
        with nc.Dataset(file) as ncdf:
            n_sim = len(ncdf['geotop']['sitename'][:])
            time = 1
            for i, name in enumerate(ncdf['geotop']['sitename'][:]):
                pass
                #t = TSP()
    except NameError:
        warnings.warn("netCDF4 library must be installed.")
    
    return output
