from __future__ import annotations

import pandas as pd
import re
import inspect
import numpy as np
import functools
import warnings
import unicodedata

try:
    import netCDF4 as nc

    try:
        from pfit.pfnet_standard import make_temperature_base, calculate_extent_metadata as calc_ext_meta
    except ModuleNotFoundError:
        warnings.warn("Missing pfit library. Some functionality will be limited.", stacklevel=2)

except ModuleNotFoundError:
    warnings.warn("Missing netCDF4 library. Some functionality will be limited.", stacklevel=2)

from typing import Union, Optional
from numpy.typing import NDArray
from datetime import datetime, tzinfo, timezone, timedelta

import tsp
import tsp.labels as lbl
import tsp.tspwarnings as tw

from tsp.physics import analytical_fourier
from tsp.plots.static import trumpet_curve, colour_contour, time_series, profile_evolution, _plot_overlay
from tsp.time import format_utc_offset
from tsp.time import get_utc_offset
from tsp.misc import completeness
from tsp.standardization import metadata as mdf
from tsp.concatenation import _tsp_concat

from matplotlib.figure import Figure


class TSP:
    """ A Time Series Profile (a collection of time series data at different depths)
    
    A TSP can also be:
    Thermal State of Permafrost
    Temperature du Sol en Profondeur
    Temperatures, Secondes, Profondeurs

    Parameters
    ----------
    times : pandas.DatetimeIndex
        DatetimeIndex with optional UTC offset. List-like array of datetime objects can also be passed, 
        but will be converted to a DatetimeIndex with no UTC offset.
    depths : list-like
        d-length array of depths
    values : numpy.ndarray
        array with shape (t,d) containing values at (t)emperatures and (d)epths
    longitude : float, optional
        Longitude at which data were collected
    latitude : float, optional
        Latitude at which data were collected
    site_id : str, optional
        Name of location at which data were collected
    metadata : dict
        Additional metadata

    Attributes
    ----------
    values
    latitude : float
        Latitude at which data were collected
    longitude : float  
        Longitude at which data were collected
    metadata : dict
        Additional metadata provided at instantiation or by other methods
    """

    def __repr__(self) -> str:
        return repr(self.wide)

    def __str__(self) -> str:
        return str(self.wide)
    
    def __add__(self, other: TSP) -> TSP:
        """ Concatenate two TSP objects along the time axis. 
        The two TSP objects must have the same depths and the same UTC offset.

        Parameters
        ----------
        other : TSP
            Another TSP object to concatenate with this one

        Returns
        -------
        TSP
            A new TSP object with the concatenated data
        """
        if not isinstance(other, TSP):
            raise TypeError("Can only concatenate TSP objects.")
        
        if self.utc_offset != other.utc_offset:
            raise ValueError("UTC offsets must be the same to concatenate.")
        
        return tsp_concat([self, other])

    def __init__(self, times, depths, values, 
                 latitude: Optional[float]=None, 
                 longitude: Optional[float]=None,
                 site_id: Optional[str]=None,
                 metadata: dict={}):

        self._times = handle_incoming_times(times)
        if self._times.duplicated().any():
            warnings.warn(tw.DuplicateTimesWarning(self._times), stacklevel=2)
        
        if self.utc_offset:
            self._output_utc_offset = self.utc_offset
        else:
            self._output_utc_offset = None
        
        self._depths = np.atleast_1d(depths)
        self._values = np.atleast_2d(values)
        self._times, self._values = self.__enforce_increasing_times(self._times, self._values)
        self.__number_of_observations = np.ones_like(values, dtype=int)
        self.__number_of_observations[np.isnan(values)] = 0
        self.metadata = metadata
        self.latitude = latitude
        self.longitude = longitude
        self.site_id = site_id
        self._freq = None
        self._completeness = None

        self._export_precision = 3
    
    @property
    def site_id(self):
        return self._site_id
    
    @site_id.setter
    def site_id(self, value):
        if value is not None:
            if is_valid_site_name_unicode(str(value)):
                self._site_id = str(value)
                self.metadata['_site_id'] = self._site_id
            else:
                raise ValueError("site_id is not valid.")
        else:
            self._site_id = None
        

    @property
    def latitude(self):
        """ Latitude at which data were collected """
        return self._latitude
    
    @latitude.setter
    def latitude(self, value: Optional[float]):
        if value is not None:
            try:
                self._latitude = float(value)
                self.metadata['_latitude'] = self._latitude
            except ValueError:
                raise ValueError("Latitude must be a float or None.")
        else:
            self._latitude = None
        

    @property
    def longitude(self):
        """ Longitude at which data were collected """
        return self._longitude

    @longitude.setter
    def longitude(self, value: Optional[float]):
        if value is not None:
            try:
                self._longitude = float(value)
                self.metadata['_longitude'] = self._longitude
            except ValueError:
                raise ValueError("Longitude must be a float or None.")
        else:
            self._longitude = None
        

    @property
    def freq(self) -> Optional[int]:
        """ Measurement frequency [s] """
        return self._freq
    
    @freq.setter
    def freq(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Must be string, e.g. '1D', '3600s'")
        self._freq = value

    def __enforce_increasing_times(self, times, values):
        """ Ensure times are strictly increasing, reordering if necessary """
        diffs = times.diff()
        non_increasing = np.where(diffs <= np.timedelta64(0, 'ns'))[0]
        if len(non_increasing) > 0:
            warnings.warn(tw.NonIncreasingTimesWarning(times), stacklevel=2)
            warnings.warn(UserWarning("Attempting to reorder times."), stacklevel=2)
            order = np.argsort(times)
            times = times[order]
            values = values[order, :]
        return times, values

    @property
    def completeness(self) -> Optional[pd.DataFrame]:
        """ Data completeness """
        return self._completeness
    
    @completeness.setter
    def completeness(self, value):
        raise ValueError("You can't assign this variable.")

    @classmethod
    def from_tidy_format(cls, times, depths, values,
                        number_of_observations=None,
                        latitude: Optional[float]=None, 
                        longitude: Optional[float]=None,
                        site_id: Optional[str]=None,
                        metadata:dict={}):
        """ Create a TSP from data in a 'tidy' or 'long' format 

        Parameters
        ----------
        times : list-like
            n-length array of datetime objects
        depths : list-like
            n-length array of depths
        values : numpy.ndarray
            n-length array of (temperaure) values at associated time and depth
        number_of_observations : numpy.ndarray, optional
            n-length array of number of observations at associated time and 
            depth for aggregated values (default: 1)
        longitude : float, optional
            Longitude at which data were collected
        latitude : float, optional
            Latitude at which data were collected
        site_id : str, optional
            Name of location at which data were collected
        metadata : dict
            Additional metadata
        """
        times = np.atleast_1d(times)
        depths = np.atleast_1d(depths)
        values = np.atleast_1d(values)
        
        number_of_observations = number_of_observations if number_of_observations else np.ones_like(values)
        df = pd.DataFrame({"times": times, "depths": depths, "temperature_in_ground": values, "number_of_observations": number_of_observations})
        df.set_index(["times", "depths"], inplace=True)

        try:
            unstacked = df.unstack()
        except ValueError as e:
            if np.any(df.index.duplicated()):
                print(f"Duplicate data found at {df.iloc[np.where(df.index.duplicated())[0], :].index.get_level_values(0).unique()}")
            raise e

        temps = unstacked.get('temperature_in_ground') 
        
        this = cls(times=temps.index.values,
                   depths=temps.columns.values,
                   values=temps.values,
                   latitude=latitude, 
                   longitude=longitude,
                   site_id=site_id,
                   metadata=metadata)
        
        number_of_observations = unstacked.get('number_of_observations').values

        number_of_observations[np.isnan(number_of_observations)] = 0
        this.__number_of_observations = number_of_observations
        return this

    @classmethod
    def __from_tsp(cls, t:TSP, **kwargs) -> "TSP":
        """ Use an existing TSP object as a template, """
        kw = {}
        for arg in inspect.getfullargspec(TSP).args[1:]:
            if kwargs.get(arg) is not None:
                kw[arg] = kwargs.get(arg)
            else:
                kw[arg] = getattr(t, arg)
        
        t = TSP(**kw)

        return t

    @classmethod
    def from_json(cls, json_file) -> "TSP":
        """ Read data from a json file 

        Parameters
        ----------
        json_file : str
            Path to a json file from which to read
        """
        df = pd.read_json(json_file)
        depth_pattern = r"^(-?[0-9\.]+)$"

        times = pd.to_datetime(df['time']).values
        depths = [re.search(depth_pattern, c).group(1) for c in df.columns if tsp._is_depth_column(c, depth_pattern)]
        values = df.loc[:, depths].to_numpy()
        
        t = cls(times=times, depths=depths, values=values)
        
        return t

    @classmethod
    def synthetic(cls, depths: NDArray[np.number], 
                  start:str ="2000-01-01", 
                  end:str ="2003-01-01",
                  freq: "str"="D",
                  Q:float=0.2, 
                  c:float=1.6e6,
                  k:float=2.5,
                  A:float=6,
                  MAGST:float=-0.5, 
                  **kwargs) -> "TSP":
        """
        Create a 'synthetic' temperature time series using the analytical solution to the heat conduction equation.
        Suitable for testing 
        
        Parameters
        ----------   
        depths : np.ndarray
            array of depths in metres
        start : str
            start date for the time series, in the format "YYYY-MM-DD"
        end : str
            end date for the time series, in the format "YYYY-MM-DD"
        freq : str
            pandas frequency string, e.g. "D" for daily, "H" for hourly, etc.
        Q : Optional[float], optional
            Ground heat flux [W m-2], by default 0.2
        c : Optional[float], optional
            heat capacity [J m-3 K-1], by default 1.6e6
        k : Optional[float], optional
            thermal conductivity [W m-1 K-1], by default 2.5
        A : Optional[float], optional
            Amplitude of temperature fluctuation [C], by default 6
        MAGST : Optional[float], optional
            Mean annual ground surface temperature [C], by default -0.5
        
        Returns 
        -------
        TSP 
            A timeseries profile (TSP) object
        """
        times = pd.date_range(start=start, end=end, freq=freq).to_pydatetime()
        t_sec = np.array([(t-times[0]).total_seconds() for t in times])
        
        values = analytical_fourier(depths=depths,
                                    times=t_sec,
                                    Q=Q,
                                    c=c,
                                    k=k,
                                    A=A,
                                    MAGST=MAGST)
        
        this = cls(depths=depths, times=times, values=values, **kwargs)
        
        return this

    @property
    @functools.lru_cache()
    def long(self) -> "pd.DataFrame":
        """ Return the data in a 'long' or 'tidy' format (one row per observation, one column per variable)

        Returns
        -------
        pandas.DataFrame
            Time series profile data with columns:
                - **time**: time
                - **depth**: depth 
                - **temperature_in_ground**: temperature
                - **number_of_observations**: If data are aggregated, how many observations are used in the aggregation
        """
        values = self.wide.melt(id_vars='time',
                                var_name="depth",
                                value_name="temperature_in_ground")

        number_of_observations = self.number_of_observations.melt(id_vars='time',
                                  var_name="depth",
                                  value_name="number_of_observations")
                              
        values['number_of_observations'] = number_of_observations['number_of_observations']

        return values

    @property
    @functools.lru_cache()
    def wide(self) -> "pd.DataFrame":
        """ Return the data in a 'wide' format (one column per depth)

        Returns
        -------
        pandas.DataFrame
            Time series profile data
        """
        tabular = pd.DataFrame(self._values)
        tabular.columns = self._depths
        tabular.index = self.times
        tabular.insert(0, "time", self.times)

        return tabular

    @property
    @functools.lru_cache()
    def number_of_observations(self) -> "pd.DataFrame":
        """ The number of observations for an average at a particular depth or time.

        For pure observational data, the number of observations will always be '1'. When data are aggregated, 
        (e.g. using :py:meth:`~tsp.core.TSP.monthly` or :py:meth:`~tsp.core.TSP.daily`) these numbers
        will be greater than 1.

        Returns
        -------
        DataFrame
            Number of observations 
        """
        tabular = pd.DataFrame(self.__number_of_observations, dtype=int)
        tabular.columns = self._depths
        tabular.index = self._times
        tabular.insert(0, "time", self._times)

        return tabular

    @number_of_observations.setter
    def number_of_observations(self, value):
        raise ValueError(f"You can't assign {value} to this variable (no assignment allowed).")

    def reset_counts(self):
        """ Set observation count to 1 if data exists, 0 otherwise """
        self.__number_of_observations = (~self.wide.isna()).astype('boolean')

    def set_utc_offset(self, offset:"Union[int,str]") -> None:
        """ Set the time zone of the data by providing a UTC offset 

        Parameters
        ----------
        offset : int, str
            If int, the number of seconds. If str, a string in the format "+HH:MM" or "-HH:MM"
        """
        if self.utc_offset is not None:
            raise ValueError("You can only set the UTC offset once.")

        utc_offset = get_utc_offset(offset)

        tz = timezone(timedelta(seconds = utc_offset)) 
        self._times = self._times.tz_localize(tz)
        self._output_utc_offset = timezone(timedelta(seconds = utc_offset)) 

        TSP.wide.fget.cache_clear()
        TSP.long.fget.cache_clear()

    @property
    def utc_offset(self) -> "Optional[tzinfo]":
        """ Get the time zone of the data by providing a UTC offset

        Returns
        -------
        datetime.tzinfo
            A timezone object
        """
        if self._times.tz is None:
            return None
        else:
            return self._times.tz
    
    @utc_offset.setter
    def utc_offset(self, value):
        self.set_utc_offset(value)
    
    @property
    def output_utc_offset(self) -> "Optional[tzinfo]":
        """ Get the time zone in which to output or display the data by providing a UTC offset
        
        Returns
        -------
        datetime.tzinfo
            A timezone object
        """
        if self._output_utc_offset is None:
            return None
        else:
            return self._output_utc_offset
    
    @output_utc_offset.setter
    def output_utc_offset(self, offset:"Union[int,str]") -> None:
        self.set_output_utc_offset(offset)

    def set_output_utc_offset(self, offset:"Union[int,str]") -> None:
        """ Set the time zone in which to display the output or data by providing a UTC offset
        Parameters
        ----------
        offset : int, str
            If int, the number of seconds. If str, a string in the format "+HH:MM" or "-HH:MM"
        """
        utc_offset = get_utc_offset(offset)
        tz = timezone(timedelta(seconds = utc_offset))
        self._output_utc_offset = tz
        
        TSP.wide.fget.cache_clear()
        TSP.long.fget.cache_clear()

    def reset_output_utc_offset(self) -> None:
        """ Reset the time zone in which to output or display the data to the default (the one set by set_utc_offset)
        
        """
        if self.utc_offset is None:
            raise ValueError("You can't reset the output time zone if the time zone of the data hasn't yet been set with set_utc_offset.")
        else:
            self._output_utc_offset = self.utc_offset

    def __nly(self, 
              freq_fmt:str,
              new_freq,
              min_count:Optional[int],
              max_gap:Optional[int],
              min_span:Optional[int]) -> TSP:
        """
        Temporal aggregation by grouping according to a string-ified time

        Parameters
        ----------
        freq_fmt : str
            Python date format string  used to aggregate and recover time 
        
        Returns
        -------
        tuple[pd.DataFrame, pd.DataFrame]
            A tuple of dataframes, the first containing the aggregated data, the second containing the number of observations
        """
        R = self.wide.drop("time", axis=1).resample(freq_fmt)
        cumulative_obs = self.number_of_observations.drop("time", axis=1).resample(freq_fmt).sum()
        total_obs = R.count()
        values = R.mean()

        # Calculate masks
        mc_mask = Mg_mask = ms_mask = pd.DataFrame(index=values.index, columns=values.columns, data=False)

        if min_count is not None:
            mc_mask = (cumulative_obs < min_count)
        if max_gap is not None:
            Mg_mask = max_gap_mask(R, max_gap)
        if min_span is not None:
            ms_mask = min_span_mask(R, min_span)
        
        mask = (mc_mask | Mg_mask | ms_mask)
        values[mask] = np.nan
        
        # Construct TSP
        t = TSP.__from_tsp(self, times=values.index, 
                           depths=values.columns, 
                           values=values.values)
        t.__number_of_observations = cumulative_obs
        t.freq = new_freq

        # Calculate data completeness
        if self.freq is not None:
            f1 = self.freq
            f2 = new_freq
            t._completeness = completeness(total_obs, f1, f2)

        return t
    
    def monthly(self,
                min_count:Optional[int]=24,
                max_gap:Optional[int]=3600*24*8,
                min_span:Optional[int]=3600*24*21) -> "TSP":
        """ Monthly averages, possibly with some months unavailable (NaN) if there is insufficient data

        Parameters
        ----------
        min_count : int
            Minimum number of observations in a month to be considered a valid average,
            defaults to None
        max_gap : int
            Maximum gap (in seconds) between data points to be considered a valid average,
             defaults to None
        min_span : int
            Minimum total data range (in seconds) to be consiered a valid average,
            defaults to None
            
        Returns
        -------
        TSP
            A TSP object with data aggregated to monthly averages
        """
        t = self.__nly(freq_fmt="ME", 
                       new_freq=lbl.MONTHLY, 
                       min_count=min_count, 
                       max_gap=max_gap, 
                       min_span=min_span)

        return t

    def daily(self, 
              min_count:Optional[int]=None,
              max_gap:Optional[int]=None,
              min_span:Optional[int]=None) -> "TSP":
        """ Daily averages, possibly with some days unavailable (NaN) if there is insufficient data

        Parameters
        ----------
        min_count : int
            Minimum number of observations in a day to be considered a valid average, 
            defaults to None
        max_gap : int
            Maximum gap (in seconds) between data points to be considered a valid average, defaults to None
        min_span : int
            Minimum total data range (in seconds) to be consiered a valid average, defaults to None
        
        Returns
        -------
        TSP
            A TSP object with data aggregated to daily averages
        """
        # if the data is already daily +/- 1min , just return it
        t = self.__nly(freq_fmt="D", 
                new_freq=lbl.DAILY, 
                min_count=min_count, 
                max_gap=max_gap, 
                min_span=min_span)

        return t

    def yearly(self,
               min_count:Optional[int]=None,
               max_gap:Optional[int]=None,
               min_span:Optional[int]=None) -> "TSP":
        """ Yearly averages, possibly with some years unavailable (NaN) if there is insufficient data

        Parameters
        ----------
        min_count : int
            Minimum number of observations in a month to be considered a valid average, defaults to None
        max_gap : int
            Maximum gap (in seconds) between data points to be considered a valid average, defaults to None
        min_span : int
            Minimum total data range (in seconds) to be consiered a valid average, defaults to None
        
        Returns
        -------
        TSP
            A TSP object with data aggregated to yearly averages
        """
        t = self.__nly(freq_fmt="YE", 
                new_freq=lbl.YEARLY, 
                min_count=min_count, 
                max_gap=max_gap, 
                min_span=min_span)

        return t

    @property
    def counts(self) -> NDArray[np.number]:
        """ Return the number of observations at each time and depth in the profile 

        Returns
        -------
        numpy.ndarray
            The number of observations at each time and depth in the profile
        """
        return self.__number_of_observations
    
    @counts.setter
    def counts(self, value):
        counts = np.atleast_2d(value)
        
        if not counts.shape == self.__number_of_observations.shape:
            raise ValueError(f"Array of counts must have shape of {self.__number_of_observations.shape}.")

        self.__number_of_observations = counts

    @property
    def depths(self) -> NDArray[np.number]:
        """ Return the depth values in the profile 

        Returns
        -------
        numpy.ndarray
            The depths in the profile
        """
        return self._depths

    @depths.setter
    def depths(self, value):
        depths = np.atleast_1d(value)
        
        if not len(depths) == len(self._depths):
            raise ValueError(f"List of depths must have length of {len(self._depths)}.")

        self._depths = depths

        TSP.wide.fget.cache_clear()
        TSP.long.fget.cache_clear()

    @property
    def times(self):
        """ Return the timestamps in the time series 

        Returns
        -------
        pandas.DatetimeIndex
            The timestamps in the time series
        """
        if self.utc_offset is None:
            return self._times
        
        elif self._output_utc_offset == self.utc_offset:
            return self._times

        else:
            return self._times.tz_convert(self.output_utc_offset)

    @property
    def values(self):
        return self._values
    
    def counts_df(self) -> pd.DataFrame:
        """ Return the number of observations as a DataFrame

        Returns
        -------
        pandas.DataFrame
            DataFrame of number of observations at each time and depth in the profile
        """
        df = pd.DataFrame(data=self.__number_of_observations, index=self.wide.index, columns=self.depths)
        return df

    def to_gtnp(self, filename: str) -> None:
        """ Write the data in GTN-P format
        
        Parameters
        ----------
        filename : str
            Path to the file to write to
        """
        df = self.wide.round(self._export_precision).rename(columns={'time': 'Date/Depth'})
        df['Date/Depth'] = df['Date/Depth'].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        df.to_csv(filename, index=False, na_rep="-999")

    def to_ntgs(self, filename:str, project_name:Optional[str]="", site_id:"Optional[str]" = None, latitude:"Optional[float]"=None, longitude:"Optional[float]"=None) -> None:
        """ Write the data in NTGS template format 

        Parameters
        ----------
        filename : str
            Path to the file to write to
        project_name : str, optional
            The project name, by default ""
        site_id : str, optional
            The name of the site , by default None
        latitude : float, optional
            WGS84 latitude at which the observations were recorded, by default None
        longitude : float, optional
            WGS84 longitude at which the observations were recorded, by default None
        """
        if latitude is None:
            latitude = self.latitude if self.latitude is not None else ""

        if longitude is None:
            longitude = self.longitude if self.longitude is not None else ""

        if site_id is None:
            site_id = self.site_id if self.site_id is not None else ""

        if project_name is None:
            project_name = self.metadata.get("project_name", "")

        data = self.values

        df = pd.DataFrame({'project_name': pd.Series(dtype='str'),
                           'site_id': pd.Series(dtype='str'),
                           'latitude': pd.Series(dtype='float'),
                           'longitude': pd.Series(dtype='float')
                           })

        df["date_YYYY-MM-DD"] = pd.Series(self.times).dt.strftime(r"%Y-%m-%d")
        df["time_HH:MM:SS"] = pd.Series(self.times).dt.strftime(r"%H:%M:%S")

        df["project_name"] = project_name
        df["site_id"] = site_id
        df["latitude"] = latitude
        df["longitude"] = longitude
        
        headers = [str(d) + "_m" for d in self.depths]
        
        for i, h in enumerate(headers):
            df[h] = data[:, i].round(self._export_precision)

        df.to_csv(filename, index=False)

    def to_netcdf(self, file: str, only_use_cf_metadata=True, 
                  calculate_extent_metadata=True, zlib=True, complevel=4) -> None:
        """  Write the data as a netcdf"""
        try:
            ncf = make_temperature_base(file, ndepth=len(self.depths), ntime=len(self.times), strings_as_strings=True, zlib=zlib, complevel=complevel)
        except NameError:
            warnings.warn("Missing required packages. Try installing with `pip install tsp[nc]`", stacklevel=2)
            return
        
        with nc.Dataset(ncf, 'a') as ncd:
            pytime = self.times.to_pydatetime()

            ncd['depth_below_ground_surface'][:] = self.depths

            
            ncd['time'][:] = nc.date2num(pytime, ncd['time'].units, ncd['time'].calendar)
            ncd['ground_temperature'][:] = self.values
            
            if self.latitude:
                ncd['latitude'][:] = self.latitude
            if self.longitude:
                ncd['longitude'][:] = self.longitude
            if self.site_id:
                if ncd['site_name'].dtype == str:
                    ncd['site_name'][0] = self.site_id
                else:
                    strlen = ncd['site_name'].shape[0]
                    ncd['site_name'][:] = nc.stringtochar(np.array([self.site_id], f"S{strlen}"))

            if "_elevation" in self.metadata:
                ncd['surface_elevation'][:] = self.metadata.get("_elevation")
            
            if only_use_cf_metadata:
                metadata = self.metadata.get('CF', {})
            else:
                metadata = self.metadata
            
            for key, value in metadata.items():
                try:
                    if isinstance(value, str):
                        ncd.setncattr_string(key, value)
                    else:
                        ncd.setncattr(key, value)
                except Exception:
                    warnings.warn(f"Could not set metadata item: {key} : {value}", stacklevel=2)

            if calculate_extent_metadata:
                calc_ext_meta(ncd)
                
    def to_json(self, file: str) -> None:
        """ Write the data to a serialized json file """
        with open(file, 'w') as f:
            f.write(self._to_json())

    def to_csv(self, file: str, include_metadata=False, long=False) -> None:
        """ Write the data to a tsp-style csv file 
        
        Parameters
        ----------
        file : str
            Path to the file to write to
        include_metadata : bool | str
            If True, include all metadata as commented lines at the top of the file.

        long : bool
            If True, write the data in long format, otherwise wide format
        """
        with open(file, 'w', encoding='utf-8') as f:
            if include_metadata == 'standard':
                md = {}
                for key in mdf.standardized_keys.keys():
                    if self.metadata.get(key):
                        md[key[1:]] = self.metadata.get(key)
            
            elif include_metadata is True:
                md = {}
                for key, value in self.metadata.items():
                    if key in mdf.standardized_keys.keys():
                        md[key[1:]] = value
                    else:
                        md[key] = value            
            else:
                md = {}
            
            md_lines = mdf.dict_to_metadata(md)
            for line in md_lines:
                f.write(f"{line}\n")

            if long:
                df = self.long.round(self._export_precision)
                df.rename(columns={"time": "timestamp", 
                                   "temperature_in_ground": "temperature"}, inplace=True)
                f.write(df.to_csv(index=False, lineterminator='\n'))
            else:
                df = self.wide.round(self._export_precision)
                df.rename(columns={"time": "timestamp"}, inplace=True)
                f.write(df.to_csv(index=False, lineterminator='\n'))

    def _to_json(self) -> str:
        return self.wide.round(self._export_precision).to_json()

    def plot_profiles(self, P:int=100, n:int=10, metadata=False) -> Figure:
        """ Create a plot of the temperature profiles at different times
        
        Parameters
        ----------
        P : int
            Percentage of time range to plot
        n : int
            Number of evenly-spaced profiles to plot
        
        Returns
        -------
        Figure
            matplotlib `Figure` object
        """
        fig = profile_evolution(depths=self.depths, times=self.times, values=self._values, P=P, n=n)
        if metadata:
            fig = _plot_overlay(fig, self)
        fig.show()
        return fig
    
    def plot_trumpet(self, 
                     year: Optional[int]=None,
                     begin: Optional[datetime]=None,
                     end: Optional[datetime]=None,
                     min_completeness: Optional[float]=None,
                     metadata=False,
                     **kwargs) -> Figure:
        """ Create a trumpet plot from the data
        
        Parameters
        ----------
        year : int, optional
            Which year to plot
        begin : datetime, optional
            If 'end' also provided, the earliest measurement to include in the averaging for the plot
        end : datetime, optional
            If 'begin' also provided, the latest measurement to include in the averaging for the plot
        min_completeness : float, optional
            If provided, the minimum completeness (fractional, 0 to 1) required to include
            in temperature envelope, otherwise
            the point is plotted as an unconnected, slightly transparent dot, by default None
        **kwargs : dict, optional
            Extra arguments to the plotting function: refer to the documentation for :func:`~tsp.plots.static.trumpet_curve` for a
            list of all possible arguments.

        Returns
        -------
        Figure
            a matplotlib `Figure` object
        """
        df = self.long.dropna()
 
        if year is not None:
            df = df[df['time'].dt.year == year]

        elif begin is not None or end is not None:
            raise NotImplementedError

        else:
            raise ValueError("One of 'year', 'begin', 'end' must be provided.")

        grouped = df.groupby('depth')

        max_t = grouped.max().get('temperature_in_ground').values
        min_t = grouped.min().get('temperature_in_ground').values
        mean_t = grouped.mean().get('temperature_in_ground').values
        depth = np.array([d for d in grouped.groups.keys()])

        # Calculate completeness
        c = self.yearly(None, None, None).completeness
        
        if min_completeness is not None and c is not None:
            C = c[c.index.year == year]
            C = C[depth].iloc[0,:].values
        
        else:
            C = None

        fig = trumpet_curve(depth=depth, 
                            t_max=max_t, 
                            t_min=min_t, 
                            t_mean=mean_t, 
                            min_completeness=min_completeness,
                            data_completeness=C,
                            **kwargs)
        if metadata:
            fig = _plot_overlay(fig, self)

        fig.show()

        return fig
    
    def plot_contour(self, metadata=False, **kwargs) -> Figure:
        """ Create a contour plot
        
        Parameters
        ----------
        **kwargs : dict, optional
            Extra arguments to the plotting function: refer to the documentation for :func:`~tsp.plots.static.colour_contour` for a
            list of all possible arguments.

        Returns
        -------
        Figure
            matplotlib `Figure` object
        """
        fig = colour_contour(depths=self.depths, times=self.times, values=self._values, **kwargs)

        if self.output_utc_offset is not None:
            label = format_utc_offset(self.output_utc_offset)
            if label != "UTC":
                label = f"UTC{label}"         
            fig.axes[0].set_xlabel(f"Time [{label}]")
        
        if metadata:
            fig = _plot_overlay(fig, self)

        fig.show()

        return fig

    def plot_timeseries(self, depths: list=[], metadata=False, **kwargs) -> Figure:
        """Create a time series T(t) plot 

        Parameters
        ----------
        depths : list, optional
            If non-empty, restricts the depths to include in the plot, by default []
        **kwargs : dict, optional
            Extra arguments to the plotting function: refer to the documentation for :func:`~tsp.plots.static.time_series` for a
            list of all possible arguments.

        Returns
        -------
        Figure
            matplotlib `Figure` object
        """
        if depths == []:
            depths = self.depths
        
        d_mask = np.isin(self.depths, depths)
        
        fig = time_series(self.depths[d_mask], self.times, self.values[:, d_mask], **kwargs)
  

        if self.output_utc_offset is not None:
            label = format_utc_offset(self.output_utc_offset)
            if label != "UTC":
                label = f"UTC{label}"         
            fig.axes[0].set_xlabel(f"Time [{label}]")
        fig.autofmt_xdate()
        
        if metadata:
            fig = _plot_overlay(fig, self)
        
        fig.show()
        
        return fig


class AggregatedTSP(TSP):
    """ A Time Series Profile that uses indices (1,2,3,...) instead of depth values. 
    
    Used in situations when depths are unknown (such as when reading datlogger exports
    that don't have depth measurements.)
    
    Parameters
    ----------
    times : list-like
        t-length array of datetime objects
    values : numpy.ndarray
        array with shape (t,d) containing values at (t)emperatures and (d)epths
    **kwargs : dict
        Extra arguments to parent class: refer to :py:class:`tsp.core.TSP` documentation for a
        list of all possible arguments.
    """


class IndexedTSP(TSP):
    """ A Time Series Profile that uses indices (1,2,3,...) instead of depth values. 
    
    Used in situations when depths are unknown (such as when reading datlogger exports
    that don't have depth measurements.)
    
    Parameters
    ----------
    times : list-like
        t-length array of datetime objects
    values : numpy.ndarray
        array with shape (t,d) containing values at (t)emperatures and (d)epths
    **kwargs : dict
        Extra arguments to parent class: refer to :py:class:`~tsp.core.TSP` documentation for a
        list of all possible arguments.
    """

    def __init__(self, times, values, **kwargs):
        depths = np.arange(0, values.shape[1]) + 1
        super().__init__(times=times, depths=depths, values=values, **kwargs)

    @property
    def depths(self) -> np.ndarray:
        """Depth indices 

        Returns
        -------
        numpy.ndarray
            An array of depth indices
        """
        warnings.warn("This TSP uses indices (1,2,3,...) instad of depths. Use set_depths() to use measured depths.", stacklevel=2)
        return self._depths

    @depths.setter
    def depths(self, value):
        TSP.depths.__set__(self, value)

    def set_depths(self, depths: np.ndarray):
        """Assign depth values to depth indices. Change the object to a :py:class:`~tsp.core.TSP`

        Parameters
        ----------
        depths : np.ndarray
            An array or list of depth values equal in lenth to the depth indices
        """
        self.depths = depths
        self.__class__ = TSP



def span(S: pd.Series) -> float:
    first = S.first_valid_index()  # type: pd.Timestamp
    last = S.last_valid_index()  # type: pd.Timestamp
    if first is None or last is None:
        return 0
    
    return (last - first).total_seconds()

def min_span_mask(R: "pd.core.resample.DatetimeIndexResampler",
             threshold: float) -> "pd.DataFrame":
    s = R.apply(lambda x: span(x))
    return s < threshold


def gap(S: pd.Series) -> float:

    d = np.diff(S.dropna().index)
    if len(d) == 0:
        return 0
    elif len(d) == 1:
        return 0
    elif len(d) > 1:
        gap = max(d).astype('timedelta64[s]').astype(float)
    return gap


def max_gap_mask(R: "pd.core.resample.DatetimeIndexResampler",
            threshold: float) -> "pd.DataFrame":
    g = R.apply(lambda x: gap(x))
    return (g > threshold) | (g == 0)




def _temporal_gap_mask(grouped: "pd.core.groupby.DataFrameGroupBy", max_gap: Optional[int], min_span: Optional[int]) -> np.ndarray:
    """ Mask out observational groups in which there is more than a certain size temporal gap

    Controls for gaps in the data within an aggregation group (using max_gap) and missing data at the beginning
    or end of the aggregation group (using min_span).
    
    Parameters
    ----------
    grouped : pandas.core.groupby.DataFrameGroupBy
        groupby  with 'time' and 'depth' columns
    max_gap : int
        maximum gap in seconds to tolerate between observations in a group
    min_span : int
        minimum data range (beginning to end) in seconds. 

    Returns
    -------
    numpy.ndarray
        boolean array with ``True`` where measurement spacing or range in group does not satisfy tolerances
    """
    if max_gap is not None:
        max_diff = grouped.time.apply(np.diff).apply(lambda x: np.max(x, initial=np.timedelta64(0))).apply(lambda x: x.total_seconds())
        max_diff = max_diff.unstack().to_numpy()
        diff_mask = np.where((max_diff == 0) | (max_diff >= max_gap), True, False)
    else:
        diff_mask = np.zeros_like(grouped, dtype=bool)
    
    if min_span is not None:
        total_span = grouped.time.apply(np.ptp).apply(lambda x: x.total_seconds()).unstack().to_numpy()
        span_mask = np.where(total_span < min_span, True, False)
    else:
        span_mask = np.zeros_like(grouped, dtype=bool)

    mask = diff_mask * span_mask

    return mask


def _observation_count_mask(number_of_observations: np.ndarray, min_count:int) -> np.ndarray:
    """ Create a mask array for an
    
    Parameters
    ----------
    number_of_observations : numpy.ndarray
        Array of how many data points are in aggregation
    min_count : int
        Minimum number of data points for aggregation to be 'valid'

    Returns
    -------
    np.ndarray
        a mask, True where data should be masked
    """
    valid = np.less(number_of_observations, min_count)  # type: np.ndarray
    return valid


def handle_incoming_times(times: "Union[np.ndarray, pd.DatetimeIndex, pd.Series, list]") -> "pd.DatetimeIndex":
    """Convert a list of times to a pandas DatetimeIndex object"""
    invalid_msg = "Times must be a list, numpy array, pandas DatetimeIndex, or pandas Series"

    try:
        if not len(times):
            raise ValueError(invalid_msg)
    except TypeError:
        raise ValueError(invalid_msg)

    if isinstance(times, pd.DatetimeIndex):
        return times

    elif isinstance(times, pd.Series):
        try:
            times = pd.DatetimeIndex(times)
        except Exception:
            raise ValueError("Series must be convertible to DatetimeIndex")
        times.name = 'time'

        return times

    elif isinstance(times, np.ndarray):
        times = pd.to_datetime(times)
        times.name = 'time'
        return times
    
    elif isinstance(times, list):
        return pd.to_datetime(times)

    else:
        raise ValueError(invalid_msg)

def tsp_concat(tsp_list, on_conflict='error', metadata='first') -> TSP:
    """Combine multiple TSPs into a single TSP.
    
    Parameters
    ----------
    tsp_list : list[TSP]
        List of TSPs to combine. They must have the same depths
    on_conflict : str, optional
        Method to resolve duplicate times with different values. Chosen from "error", "keep", by default "error"
        - "error": Raise an error if duplicate times with different values are found.
        - "keep": Keep the first occurrence of the duplicate time.
    metadata : str, optional
        Method to select metadata from the TSPs. Chosen from "first", "identical", or "none", by default "first"
        - "first": Use the metadata from the first TSP in the list.
        - "identical": Only keep metadata records that are identical across TSPs.
        - "none": Ignore metadata and set it to None.
    Returns
    -------
    TSP
        Combined TSP.
        
    Description
    -----------
    This function combines multiple TSPs into a single TSP. The TSPs must have the same depths.
    """
    tsp_dict = _tsp_concat(tsp_list=tsp_list, on_conflict=on_conflict, metadata=metadata)
    times = tsp_dict.pop('times')
    depths = tsp_dict.pop('depths')
    values = tsp_dict.pop('values')
    counts = tsp_dict.pop('counts')

    t = TSP(times, depths, values, **tsp_dict)
    t.counts = counts

    return t


def is_single_line(s: str) -> bool:
    return "\n" not in s and "\r" not in s


def is_valid_site_name_unicode(s: str) -> bool:
    if not is_single_line(s):
        return False
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        return False
    
    for ch in s:
        cat = unicodedata.category(ch)
        if cat.startswith("C"):  # control chars, surrogates, etc.
            return False
    return True