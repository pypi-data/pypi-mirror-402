import pathlib
import warnings
import numpy as np
import pandas as pd
import datetime as dt
from .AbstractReader import AbstractReader


class RBRXL800(AbstractReader):

    def read(self, file_path: str) -> "pd.DataFrame":
        """

        Parameters
        ----------
        file

        Returns
        -------

        """
        file_extention = pathlib.Path(file_path).suffix.lower()
        if file_extention not in [".dat", ".hex"]:
            raise IOError("Unrecognised file. File is not a .dat or .hex")

        with open(file_path, "r") as f:
            header_lines = [next(f) for i in range(18)]
            self._parse_meta(header_lines)

            data_lines = f.readlines()
            if file_extention == ".dat":
                if data_lines[0] == "\n" or len(data_lines[0].split()) == self.META["num_channels"] + 2:
                    self._read_daily_dat_format(data_lines)
                else:
                    if len(data_lines[0].split()) == 1 + self.META["num_channels"]:
                        self._read_standard_dat_format(data_lines, True)
                    elif len(data_lines[0].split()) == self.META["num_channels"]:
                        self._read_standard_dat_format(data_lines, False)
                    else:
                        raise RuntimeError("Error: Number of column names and number of columns do not match any"
                                           "expected pattern.")

            elif file_extention == ".hex":
                self.META["num_bytes"] = int(data_lines[0].split()[-1])
                data_lines = data_lines[1:]
                self._read_standard_hex_format(data_lines)

            if len(self.DATA.index) != self.META["num_samples"]:
                warnings.warn(f"{file_path} Mismatch between number of samples in specified header "
                              f"({self.META['num_samples']}) and number of samples read {len(self.DATA.index)}. Some "
                              "data may be missing")
        return self.DATA

    def _parse_meta(self, header_lines: list):
        self.META["logger_model"] = header_lines[0].split()[1]
        self.META["logger_sn"] = header_lines[0].split()[3]
        sample_interval = dt.datetime.strptime(header_lines[5].split()[-1], "%H:%M:%S")
        self.META["sample_interval"] = dt.timedelta(hours=sample_interval.hour, minutes=sample_interval.minute,
                                                    seconds=sample_interval.second)
        # try:
        self.META["logging_start"] = dt.datetime.strptime(" ".join(header_lines[3].split()[-2:]), "%y/%m/%d %H:%M:%S")
        """
        except ValueError:
            date = header_lines[3].split()[-2]
            if "00" in date.split("/"):
                warnings.warn("Invalid logging start date given in header. Logger may have experienced power issues and"
                              "data may be corrupt")"""

        line_7_info = header_lines[6].split(",")
        self.META["num_channels"] = int(line_7_info[0].split()[-1])
        self.META["num_samples"] = int(line_7_info[1].split()[-1])
        self.META["precision"] = int(header_lines[9].split("%")[1][-2])

        self.META["calibration_parameters"] = {}
        calibration_start_line = 10
        for i in range(self.META["num_channels"]):
            self.META["calibration_parameters"][f"channel_{i + 1}"] = {}
            line_num = calibration_start_line + i
            raw_calibration = header_lines[line_num].split()
            if raw_calibration[1] != "2":
                raise ValueError(f"Calibration equation #{raw_calibration[1]} currently unsupported.")
            self.META["calibration_parameters"][f"channel_{i + 1}"]["a0"] = float(raw_calibration[2])
            self.META["calibration_parameters"][f"channel_{i + 1}"]["a1"] = float(raw_calibration[3])
            self.META["calibration_parameters"][f"channel_{i + 1}"]["a2"] = float(raw_calibration[4])
            if raw_calibration[5] == "0":
                self.META["calibration_parameters"][f"channel_{i + 1}"]["a3"] = 1
            else:
                self.META["calibration_parameters"][f"channel_{i + 1}"]["a3"] = float(raw_calibration[2])
        self.META['raw'] = "".join(header_lines)
        return

    def _read_daily_dat_format(self, raw_data: list):
        """

        Parameters
        ----------
        raw_data

        Returns
        -------

        """
        self.DATA = pd.DataFrame(columns=[f"channel_{i + 1}" for i in range(self.META["num_channels"])])
        for line in raw_data:
            if line != "\n":
                if len(line) == 20 or len(line.split()) == self.META["num_channels"] + 2:
                    date_stamp = dt.datetime.strptime(" ".join(line.split()[0:2]), "%Y/%m/%d %H:%M:%S")
                    interval_num = 0
                elif len(line.split()) == self.META["num_channels"] + 1:
                    self.DATA.loc[date_stamp + self.META["sample_interval"] * interval_num] = line.split()[1:]
                    interval_num += 1
                else:
                    self.DATA.loc[date_stamp + self.META["sample_interval"] * interval_num] = line.split()
                    interval_num += 1
        for col in self.DATA:
            self.DATA[col] = pd.to_numeric(self.DATA[col], errors='coerce')
        self.DATA.reset_index(inplace=True)
        self.DATA.rename(columns={"index": "TIME"}, inplace=True)
        return

    def _read_standard_hex_format(self, raw_data: list):
        byte_list = []
        for line in raw_data:
            eight_bytes = [line[i: i + 4] for i in range(0, len(line), 4)][:-1]
            for byte in eight_bytes:
                byte_list.append(byte)
        byte_num = 0
        self.DATA = pd.DataFrame(columns=[f"channel_{i + 1}" for i in range(self.META["num_channels"])])
        line_num = 0
        prev_line_day = 0
        for line in range(self.META["num_samples"]):
            line_time = self.META["logging_start"] + self.META["sample_interval"] * line_num
            if line_time.day != prev_line_day:
                byte_num += 7
                prev_line_day = line_time.day
            line_bytes = byte_list[byte_num: byte_num + 8]
            line_temps = []
            for channel in range(len(line_bytes)):
                hex_val = line_bytes[channel]
                first_digit = hex_val[0]
                if first_digit == "0":
                    data_val = -int(hex_val[1:], 16)
                if first_digit == "2":
                    data_val = int(hex_val[1:], 16)
                elif first_digit in ["1", "3"]:
                    data_val = np.nan
                if not np.isnan(data_val) and data_val > 0:
                    a0 = self.META["calibration_parameters"][f"channel_{channel + 1}"]["a0"]
                    a1 = self.META["calibration_parameters"][f"channel_{channel + 1}"]["a1"]
                    a2 = self.META["calibration_parameters"][f"channel_{channel + 1}"]["a2"]
                    a3 = self.META["calibration_parameters"][f"channel_{channel + 1}"]["a3"]
                    y = a2 * ((2048 * (a3 / data_val)) - 1)
                    temp = (a1 / ((a1 / 273.15) - np.log(a0 / y))) - 273.15
                    line_temps.append(round(temp, self.META["precision"]))
                else:
                    line_temps.append(np.nan)
            self.DATA.loc[line_time] = line_temps
            byte_num += 8
            line_num += 1
        for col in self.DATA:
            self.DATA[col] = pd.to_numeric(self.DATA[col], errors='coerce')
        self.DATA.reset_index(inplace=True)
        self.DATA.rename(columns={"index": "TIME"}, inplace=True)
        return

    def _read_standard_dat_format(self, raw_data: list, line_numbers=False):
        """

        Parameters
        ----------
        raw_data
        line_numbers

        Returns
        -------

        """
        self.DATA = pd.DataFrame(columns=[f"channel_{i + 1}" for i in range(self.META["num_channels"])])
        line_num = 0
        for line in raw_data:
            line_data = line.split()
            if line_numbers:
                line_data = line_data[1:]
            self.DATA.loc[self.META["logging_start"] + self.META["sample_interval"] * line_num] = line_data
            line_num += 1
        for col in self.DATA:
            self.DATA[col] = pd.to_numeric(self.DATA[col], errors='coerce')
        self.DATA.reset_index(inplace=True)
        self.DATA.rename(columns={"index": "TIME"}, inplace=True)
        return
