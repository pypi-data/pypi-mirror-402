import numpy as np
import pandas as pd
import warnings

import tsp.tspwarnings as tw

from tsp.core import TSP
from tsp.readers.csv import read_csv


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