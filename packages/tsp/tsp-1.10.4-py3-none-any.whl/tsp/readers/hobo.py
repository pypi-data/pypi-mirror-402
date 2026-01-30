from typing import  Optional

from tsp.dataloggers.HOBO import HOBO, HOBOProperties


from tsp.core import IndexedTSP


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

