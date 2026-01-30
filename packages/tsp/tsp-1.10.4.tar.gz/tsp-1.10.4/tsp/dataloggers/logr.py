import pandas as pd
import regex as re
import numpy as np
import datetime as dt


class LogR:
    SEP = ","

    def __init__(self):
        self.DATA = None
        self.META = None
        pass

    def read(self, file: str, cfg_txt: str = None):
        raw = is_raw_data(file)
        if raw and cfg_txt is None:
            raise ValueError("cfg_txt must be specified if providing raw data.")

        if cfg_txt is not None:
            config_params = read_cfg_file(cfg_txt)
        else:
            config_params = None

        header_rows = read_logr_header(file)
        columns = [line.strip().split(',') for line in header_rows if is_columns_row(line)][0]
        labels = [line.strip().split(',') for line in header_rows if is_label_row(line)][0]
        data = pd.read_csv(file, header=len(header_rows) - 1,
                           names=["TIME" if c == 'timestamp' else c for c in columns])
        if raw:
            data = convert_raw_to_temperatures(data=data, channel_metadata=config_params["channel_metadata"])
        else:
            data['TIME'] = pd.to_datetime(data['TIME'], format=dateformat())
            if config_params is not None and "UTC Offset" in config_params.keys():
                pattern = re.compile(r"-?\+?\d{2}:?\d{0,2}")
                match = pattern.search(config_params["UTC Offset"])
                if match is None:
                    raise ValueError("Could not parse UTC offset")
                offset = [int(ele) for ele in match.group().split(":")]
                if len(offset) == 1:
                    tz = dt.timezone(dt.timedelta(hours=offset[0]))
                elif len(offset) == 2:
                    tz = dt.timezone(dt.timedelta(hours=offset[0], minutes=offset[1]))
                else:
                    raise ValueError("Could not parse UTC offset")
                data['TIME'] = data['TIME'].dt.tz_localize(tz)

        channels = pd.Series(data.columns).str.match("^CH")

        self.DATA = data
        self.META = {'label': labels,
                     'guessed_depths': guess_depths(labels)[-sum(channels):]}
        if config_params is not None:
            self.META = self.META | config_params

        return self.DATA


def read_cfg_file(file_path: str):
    metadata = dict()
    with open(file_path, "r") as f:
        for i in range(50):
            line = f.readline()
            if line.startswith("ChannelID"):
                break
            if line != "\n":
                line = line.split(":")
                metadata[line[0].strip()] = line[1].strip()
    if "Serial Number" in metadata.keys():
        metadata["logger_sn"] = metadata["Serial Number"]
        del metadata["Serial Number"]
    metadata["channel_metadata"] = pd.read_csv(file_path, delimiter="\t", header=len(metadata.keys()),
                                               index_col="ChannelID")
    return metadata


def convert_raw_to_temperatures(data: pd.DataFrame, channel_metadata: pd.DataFrame):
    data["TIME"] = pd.to_datetime(data["TIME"], unit="s", utc=True)
    voltage_ref = 2.5
    r_fixed = 7500
    r_correction = 100
    for channel in channel_metadata.index:
        if channel in data.columns:
            coefficents = {letter: channel_metadata.loc[channel, letter] for letter in ["A", "B", "C", "D", "E"]}
            resistances = r_fixed / (voltage_ref / data[channel] - 1) - r_correction
            data[channel] = 1 / (coefficents["A"] + coefficents["B"] * np.log(resistances)
                                 + coefficents["C"] * np.power(np.log(resistances), 3)
                                 + coefficents["D"] * np.power(np.log(resistances), 5)) - 273.15
    return data


def read_logr_header(file: str) -> list:
    """ Read metadata / header lines from LogR file 

    Parameters
    ----------
    file : str
        path to a LogR file

    Returns
    -------
    list
        list of lines in the header block

    Raises
    ------
    ValueError
        _description_
    """
    found_data = False
    max_rows = 50
    header_lines = list()

    with open(file) as f:
        while not found_data and max_rows:
            max_rows -= 1
            line = f.readline()
            if is_data_row(line):
                found_data = True
                break
            else:
                header_lines.append(line)
    if not found_data:
        raise ValueError("Could not find start of data")
    return header_lines


def guess_depths(labels: list[str]) -> list[float]:
    pattern = re.compile(r"(-?[\d\.]+)")

    matches = [pattern.search(l) for l in labels]
    depths = [float(d.group(1)) if d else None for d in matches]

    return depths


def guessed_depths_ok(depths, n_channel) -> bool:
    """ Evaluate whether the guessed depths are valid """
    d = np.array(depths, dtype='float64')

    # monotonic (by convention)
    if not (np.diff(d) > 0).all() or (np.diff(d) < 0).all():
        return False

    # equal to number of channels
    if not sum(~np.isnan(d)) == n_channel:
        return False

    return True


def dateformat():
    return "%Y/%m/%d %H:%M:%S"


def is_data_row(line: str) -> bool:
    if line == "":
        return False
    second_element = line.split(",")[1]
    try:
        if second_element.isnumeric():
            dt.datetime.fromtimestamp(float(second_element))
        else:
            dt.datetime.strptime(second_element, dateformat())
        return True
    except:
        return False


def is_raw_data(file: str) -> bool:
    with open(file) as f:
        for i in range(50):
            line = f.readline()
            if line == "":
                continue
            second_element = line.split(",")[1]
            try:
                if second_element.isnumeric():
                    dt.datetime.fromtimestamp(float(second_element))
                    return True
                else:
                    dt.datetime.strptime(second_element, dateformat())
                    return False
            except:
                pass
    raise RuntimeError("Could not determine if raw data")


def is_columns_row(line: str) -> bool:
    pattern = re.compile(r"^SensorId")
    return bool(pattern.match(line))


def is_label_row(line: str) -> bool:
    pattern = re.compile(r"^Label")
    return bool(pattern.match(line))
