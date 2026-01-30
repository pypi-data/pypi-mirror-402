def write_gtnp(filename, depths, times, values, precision=3, legacy=True):
    """ Write data in GTN-P format
    
    Parameters
    ----------
    filename : str
        Path to the file to write to
    depths : array-like
        Depth or time values
    times : array-like
        Time values
    values : 2D array-like
        Data values, shape (len(depths), len(times))
    precision : int, optional
        Number of decimal places to round to, by default 3
    legacy : bool, optional
        Whether to use legacy format, by default True
    """
    import pandas as pd
    import numpy as np

    # Create DataFrame
    df = pd.DataFrame(values, index=depths, columns=times)
    df.index.name = 'Date/Depth'
    
    # Round values
    df = df.round(precision)
    
    # Format index if it's datetime
    if np.issubdtype(df.index.dtype, np.datetime64):
        df.index = df.index.strftime("%Y-%m-%d %H:%M:%S")
    
    # Write to CSV
    df.to_csv(filename, na_rep="-999")


def _write_gtnp_legacy(filename: str, precision=3, legacy=True) -> None:
    """ Write data in GTN-P format
    
    Parameters
    ----------
    filename : str
        Path to the file to write to
    """
    df = self.wide.round(self._export_precision).rename(columns={'time': 'Date/Depth'})
    df['Date/Depth'] = df['Date/Depth'].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    df.to_csv(filename, index=False, na_rep="-999")