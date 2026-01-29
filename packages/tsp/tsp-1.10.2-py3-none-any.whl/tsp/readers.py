import datetime
import numpy as np
import pandas as pd
import datetime as dt
import re
import warnings

try:
    import netCDF4 as nc
except ModuleNotFoundError:
    warnings.warn("Missing netCDF4 library. Some functionality will be limited.")

from pathlib import Path
from typing import Union, Optional, Callable

from tsp.dataloggers.Geoprecision import detect_geoprecision_type
from tsp.dataloggers.HOBO import HOBO, HOBOProperties
from tsp.dataloggers.logr import LogR, guessed_depths_ok
from tsp.dataloggers.RBRXL800 import RBRXL800
from tsp.dataloggers.RBRXR420 import RBRXR420
from tsp.dataloggers.Vemco import Vemco
import tsp.tspwarnings as tw

from tsp.core import TSP, IndexedTSP
from tsp.misc import _is_depth_column
from tsp.gtnp import GtnpMetadata


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


def read_csv(filepath: str,
              datecol: "Union[str, int]",
              datefmt: str = "%Y-%m-%d %H:%M:%S",
              depth_pattern: "Union[str, dict]" = r"^(-?[0-9\.]+)$",
              na_values:list = [],
              **kwargs) -> TSP:
    r"""Read an arbitrary CSV file 
   
    Date and time must be in a single column, and the csv must be in the
    'wide' data format (each depth is a separate column)

    Parameters
    ----------
    filepath : str
        Path to csv file
    datecol : Union[str, int]
        Either the numeric index (starting at 0) of date column (if int) or name of date column or regular expression (if str)
    datefmt : str, optional
        The format of the datetime values. Use `python strftime format codes <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes>`_, 
        by default ``"%Y-%m-%d %H:%M:%S"``
    depth_pattern : str or dict
        If string: A regular expression that matches the column names with depths. The regular expression must
        have a single capture group that extracts just the numeric part of the column header, by default r"^(-?[0-9\.]+)$".
        If column names were in the form ``"+/-1.0_m"`` (i.e. included 'm' to denote units), you could use the regular expression ``r"^(-?[0-9\.]+)_m$"``
        If a dictionary is passed, the keys must be the column names and the values are the depths. This is useful if the column names are not numeric.
    na_values : list, optional
        Additional strings to recognize as NA. Passed to pandas.read_csv, by default []

    Returns
    -------
    TSP
        A TSP
    """
    raw = pd.read_csv(filepath, na_values=na_values, **kwargs)
    
    if not datecol in raw.columns and isinstance(datecol, str):
        datecol = [re.search(datecol, c).group(1) for c in raw.columns if re.search(datecol, c)][0]
    
    if isinstance(datecol, int):
        datecol = raw.columns[datecol]

    time = pd.to_datetime(raw[datecol], format=datefmt).to_numpy()

    if isinstance(depth_pattern, str):
        depth = [re.search(depth_pattern, c).group(1) for c in raw.columns if _is_depth_column(c, depth_pattern)]
        depth_numeric = np.array([float(d) for d in depth])
    
    elif isinstance(depth_pattern, dict):
        depth = [c for c in raw.columns if c in depth_pattern.keys()]
        depth_numeric = [depth_pattern[c] for c in raw.columns if c in depth_pattern.keys()]
    
    else:
        raise ValueError("depth_pattern must be a string or dictionary")

    values = raw.loc[:, depth].to_numpy()

    t = TSP(time,
            depth_numeric,
            values,
            metadata={"source_file": filepath})

    return t


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


def read_geotop(file: str) -> TSP:
    """Read a GEOtop soil temperature output file

    Parameters
    ----------
    file : str
        Path to file.

    Returns
    -------
    TSP
        A TSP

    Description
    -----------
    Only the last run of the last simulation period is returned. This is because GEOtop outputs
    all runs of all simulation periods in the same file. This function will only return the last
    run of the last simulation period.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=tw.DuplicateTimesWarning)

        t = read_csv(file,
                    na_values=[-9999.0],
                    datecol="^(Date.*)",
                    datefmt=r"%d/%m/%Y %H:%M",
                    depth_pattern=r"^(-?[0-9\.]+\s*)$")
    
    t._depths *= 0.001  # Convert to [m]

    # Only use last simulation period 
    # TODO: this could be improved
    raw = pd.read_csv(file)

    is_max_sim_period = raw['Simulation_Period'] == max( raw['Simulation_Period'])
    is_last_run_in_max_sim_period = raw['Run'] = raw['Run'][is_max_sim_period].max()
    last_run = np.logical_and(is_max_sim_period, is_last_run_in_max_sim_period)
    
    last = TSP(times = t.times[last_run],
               depths = t.depths,
               values = t.values[last_run, :],
               metadata={"_source_file": file,
                         "Simulation_Period": max(raw['Simulation_Period']),
                         "Run": max( raw['Run'] )
                         }
    )

    return last
    


def read_gtnp(filename: str,
              metadata_filepath=None,
              autodetect_metadata=True) -> TSP:
    """Read test file from GTN-P database export

    Parameters
    ----------
    filename : str
        Path to file.
    metadata_file : str, optional
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


def read_hoboware(filepath: str, hoboware_config: Optional[HOBOProperties]=None) -> IndexedTSP:
    """Read Onset HoboWare datalogger exports

    Parameters
    ----------
    filepath : str
        Path to a file
    hoboware_config : HOBOProperties, optional
        A HOBOProperties object with information about how the file is configured. If not 
        provided, the configuration will be automatically detected if possible, by default None

    Returns
    -------
    IndexedTSP
        An IndexedTSP. Use the `set_depths` method to provide depth information
    """
    reader = HOBO(properties=hoboware_config)
    data = reader.read(filepath)

    metadata = reader.META
    metadata['_source_file'] = filepath

    t = IndexedTSP(times=data['TIME'],
                    values=data.drop("TIME", axis=1).values,
                    metadata=metadata)

    return t


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


def read_ntgs_gtr(filename: str) -> TSP:
    """Read a file from the NTGS permafrost ground temperature report

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    TSP
        A TSP
    """
    if Path(filename).suffix == ".csv":
        try:
            raw = pd.read_csv(filename, 
                              keep_default_na=False,na_values=[''], 
                              parse_dates={"time": ["date_YYYY-MM-DD","time_HH:MM:SS"]})
        except IndexError:
            raise IndexError("There are insufficient columns, the file format is invalid.")
    elif Path(filename).suffix in [".xls", ".xlsx"]:
        try:
            raw = pd.read_excel(filename, 
                                sheet_name=1, parse_dates=False)
            # Avoid any excel date nonsense
            safe_date = raw.pop('date_YYYY-MM-DD').astype(str).str.extract(r"([0-9]{4}-[0-9]{2}-[0-9]{2})") 
            safe_time = raw.pop('time_HH:MM:SS').astype(str).str.extract(r"([0-9]{2}:[0-9]{2}:[0-9]{2})") 
            raw.insert(0, 'time', safe_date[0] + " " + safe_time[0])
            raw['time'] = pd.to_datetime(raw['time'], format="%Y-%m-%d %H:%M:%S")
        except IndexError:
            raise IndexError("There are insufficient columns, the file format is invalid.") 
    else:
        raise TypeError("Unsupported file extension.")
    
    metadata = {
                'project_name': raw['project_name'].values[0],
                '_site_id': raw['site_id'].values[0],
                '_latitude': raw['latitude'].values[0],
                '_longitude': raw['longitude'].values[0],
                '_source_file': filename
                }
    match_depths = [c for c in [re.search(r"(-?[0-9\.]+)_m$", C) for C in raw.columns] if c]
    values = raw.loc[:, [d.group(0) for d in match_depths]].values
    times = np.array(raw['time'].dt.to_pydatetime())
        
    t = TSP(times=times,
              depths=[float(d.group(1)) for d in match_depths],
              values=values,
              latitude=raw['latitude'].values[0],
              longitude=raw['longitude'].values[0],
              site_id=raw['site_id'].values[0],
              metadata=metadata)
    
    return t


def read_ntgs_db(filename:str) -> dict[str, TSP]:
    """Read a file from the NTGS permafrost database export

    Parameters
    ----------
    filename : str
        Path to file.

    Returns
    -------
    dict[str, TSP]
        A dictionary of TSPs, keyed by SITE_ID
    """
    df = pd.read_csv(filename, parse_dates=['MEASUREMENT_DATETIME'])
    grouped = df.groupby("SITE_ID")
    wide_dict = {name:__parse_ntgs_db_df(data, site_id=name) for name, data in grouped}
    
    for name, tsp_obj in wide_dict.items():
        tsp_obj.metadata['_source_file'] = filename
        tsp_obj.metadata['_site_id'] = name

    return wide_dict


def read_ntgs_db_single(filename:str, 
                        select = None, 
                        duplicate_depths='mean') -> TSP:
    """Read a file from the NTGS permafrost database export with a single TSP output
    Parameters
    ----------
    filename : str
        Path to file.
    select : str, int, optional
        How to handle multiple SITE_IDs in the file. If an integer, it is treated as the index of the SITE_ID to use (0-based). 
        If a string, treat it as the site ID to use. If None, an error is raised if multiple SITE_IDs are found.
    duplicate_depths : str, optional
        How to handle duplicate depth measurements. Options are 'mean' (default), 'error'
    Returns
    -------
    TSP
        A TSP
    """
    df = pd.read_csv(filename)
    
    if len(df['SITE_ID'].unique()) > 1 and select is None:
        raise ValueError("Multiple SITE_IDs found in file.")
    elif len(df['SITE_ID'].unique()) > 1 and isinstance(select, int):
        df = df[df['SITE_ID'] == df['SITE_ID'].unique()[select]]
    elif len(df['SITE_ID'].unique()) > 1 and isinstance(select, str):
        df = df[df['SITE_ID'] == select]
    
    metadata = {'_source_file': filename,
                '_site_id': df['SITE_ID'].unique()[0]}
    
    t = __parse_ntgs_db_df(df, duplicate_depths=duplicate_depths, site_id=metadata['_site_id'])
    t.metadata.update(metadata)
    return t


def __parse_ntgs_db_df(df:pd.DataFrame, site_id=None, duplicate_depths='mean') -> TSP:
    wide = df.pivot_table(index='MEASUREMENT_DATETIME',
                          columns='DEPTH_M',
                          values='TEMPERATURE_C',
                          aggfunc=duplicate_depths).reset_index()
    
    times = wide.pop('MEASUREMENT_DATETIME').to_numpy()
    depths = wide.columns.to_numpy().astype(float)
    values = wide.to_numpy()
    
    t = TSP(times=times,
            depths=depths,
            values=values,
            site_id=site_id)
    
    return t


def read_ntgs(filename: str, allow_multiple_sites=False) -> TSP | dict[str, TSP]:
    """Read a NTGS file. 

    Parameters
    ----------
    filename : str
        Path to file.
    
    Returns
    -------
    TSP | dict[str, TSP]
        A TSP or a dictionary of TSPs with SITE_ID as keys if multiple SITE_IDs are found and `allow_multiple_sites` is True.

    Description
    -----------
    Attempts to read the file as a ground temperature report file first. If that fails, attempts to read
    it as a database export. If multiple SITE_IDs are found in the database export, 
    a dictionary of TSPs is returned if `allow_multiple_sites` is True.
    """
    try:
        return read_ntgs_gtr(filename)
    except Exception:
        dict_t = read_ntgs_db(filename)
    
        if len(dict_t.keys()) == 1:
            return list(dict_t.values())[0]
        
        elif allow_multiple_sites:
            return dict_t
            
        else:
            raise ValueError(f"Found {len(dict_t.keys())} unique SITE_ID values in file. "
                              "Use read_ntgs_db() or set `allow_multiple_sites=True` to return all sites as a dictionary.")



def read_rbr(file_path: str) -> IndexedTSP:
    """

    Parameters
    ----------
    filepath

    Returns
    -------

    """
    file_extention = Path(file_path).suffix.lower()
    if file_extention in [".dat", ".hex"]:
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
    elif file_extention in [".xls", ".xlsx", ".rsk"]:
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


def read_vemco(file_path: str) -> IndexedTSP:
    """

    Parameters
    ----------
    filepath

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


def to_native_datetime(timestamp: pd.Timestamp) -> dt.datetime:
    return timestamp.to_pydatetime()


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