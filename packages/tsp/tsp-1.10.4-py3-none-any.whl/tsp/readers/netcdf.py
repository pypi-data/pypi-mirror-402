import numpy as np
import warnings

try:
    import netCDF4 as nc
except ModuleNotFoundError:
    warnings.warn("Missing netCDF4 library. Some functionality will be limited.")

from tsp.core import TSP


def read_netcdf(file:str, standard_name='temperature_in_ground') -> TSP:
    """Read a CF-compliant netCDF file

    Parameters
    ----------
    file : str
        Path to netCDF file.
    standard_name : str, optional
        The standard name of the data variable, by default 'temperature_in_ground'. 
        'soil_temperature' is also common.

    The file must represent data from a single location
    A single time variable (with attribute 'axis=T') must be present.
    A single depth variable (with attribute 'axis=Z') must be present.
    A single data variable (with 'temperature_in_ground' or '' 'standard name' either ) must be present.

    """
    try:
        with nc.Dataset(file) as ncdf:
            globals = {k: v for k, v in ncdf.__dict__.items() if not k.startswith("_")}
            
            # Checks - global attributes
            if not globals.get("featureType", "").lower() == "timeseriesprofile":
                warnings.warn("featureType is not a time series profile")
            
            # Checks - data
            time = ncdf.get_variables_by_attributes(axis='T')
            if len(time) == 0:
                raise ValueError("No time variable (with attribute 'axis=T') found")
            if len(time) > 1:
                raise ValueError("More than one time variable (with attribute 'axis=T') found")
            
            if not 'units' in time[0].ncattrs():
                raise ValueError("Time variable does not have a 'units' attribute")
            if not 'calendar' in time[0].ncattrs():
                raise ValueError("Time variable does not have a 'calendar' attribute")
            
            depth = ncdf.get_variables_by_attributes(axis='Z')
            if len(depth) == 0:
                raise ValueError("No depth variable (with attribute 'axis=Z') found")
            if len(depth) > 1:
                raise ValueError("More than one depth variable (with attribute 'axis=Z') found")
            
            temperature = ncdf.get_variables_by_attributes(standard_name=lambda x: x in ['temperature_in_ground', 'soil_temperature']) 
            if len(temperature) == 0:
                raise ValueError("No temperature variable (with standard name 'temperature_in_ground' or 'soil_temperature') found")
            if len(temperature) > 1:
                raise ValueError("More than one temperature variable (with standard name 'temperature_in_ground' or 'soil_temperature') found")
            
            #  Get data
            times = nc.num2date(time[0][:], 
                               units=time[0].units,
                               calendar=time[0].calendar,
                               only_use_cftime_datetimes=False,
                               only_use_python_datetimes=True)
            depths = np.round(np.array(depth[0][:], dtype='float64'), 5)
            values = temperature[0][:]
    
    except NameError:
        warnings.warn("netCDF4 library must be installed.")
        return None

    except ValueError as e:
        warnings.warn(f"File does not meet formatting requirements: ({e})")
        return None
    
    metadata = {"CF":globals,
                "_source_file": file}
    
    t = TSP(times=times, depths=depths, values=values, metadata=metadata)

    return t
