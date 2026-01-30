# -*- coding: utf-8 -*-
"""
*DESCRIPTION*

Author: rparker
Created: 2024-01-10
"""
import os
import pathlib
import pandas as pd
import datetime as dt

from .AbstractReader import AbstractReader


class Vemco(AbstractReader):
    def __init__(self):
        self.META = {}

    def read(self, file_path: str):
        file_extention = pathlib.Path(file_path).suffix.lower()
        if file_extention == ".000":
            try:
                with open(file_path, "r", encoding="cp1252") as file:
                    first_line = file.readline()
                if first_line.startswith("*"):
                    self._read_old_000_logger_file(file_path)
                else:
                    raise IOError(f"{os.path.basename(file_path)} unreadable. Try opening this file in Logger VUE and "
                                  f"exporting it as a .csv")
            except UnicodeDecodeError as e:
                raise IOError(f"{os.path.basename(file_path)} unreadable. Try opening this file in Logger VUE and "
                              f"exporting it as a .csv")
        elif file_extention == ".csv":
            self._read_logger_vue_csv(file_path)
        else:
            raise ValueError("File is not a .csv or .000")
        return self.DATA

    def _read_old_000_logger_file(self, file_path):
        with open(file_path, "r", encoding="cp1252") as file:
            lines = file.readlines()
        header_lines = lines[:6]
        data_lines = [l.strip().split(",") for l in lines[6:]]
        self.META["logger_model"] = header_lines[0].split("=")[-1].strip()
        self.META["logger_sn"] = header_lines[1].split("=")[-1].strip()
        self.META["study_id"] = header_lines[2].split("=")[-1].strip()
        self.META["logging_start"] = dt.datetime.strptime(header_lines[3].split("=")[-1].strip(), "%d/%m/%Y %H:%M:%S")
        self.META["download_date"] = dt.datetime.strptime(header_lines[4].split("=")[-1].strip(), "%d/%m/%Y %H:%M:%S")
        sample_interval = dt.datetime.strptime(header_lines[5].split("=")[-1].strip(), "%H:%M:%S")
        self.META["sample_interval"] = dt.timedelta(hours=sample_interval.hour, minutes=sample_interval.minute,
                                                    seconds=sample_interval.second)
        self.META['raw'] = "".join(header_lines)
        self.DATA = pd.DataFrame(data_lines[1:], columns=["TIME", "TEMPERATURE"])
        self.DATA["TIME"] = pd.to_datetime(self.DATA["TIME"], format="%d/%m/%Y %H:%M:%S")
        self.DATA["TEMPERATURE"] = pd.to_numeric(self.DATA["TEMPERATURE"], errors='coerce')
        return

    def _read_logger_vue_csv(self, file_path):
        with open(file_path, "r", encoding="cp1252") as file:
            lines = file.readlines()

        header_lines = lines[:7]
        data_lines = [l.strip().split(",") for l in lines[7:]]
        model_and_sn = header_lines[1][15:-1]
        self.META["logger_sn"] = model_and_sn.split("-")[-1]
        self.META["logger_model"] = "-".join(model_and_sn.split("-")[:-1])
        self.META["study_id"] = header_lines[2].split(":")[-1].strip()
        self.META["logging_start"] = dt.datetime.strptime(header_lines[4][18:-1], "%Y-%m-%d %H:%M:%S")
        self.META["download_date"] = dt.datetime.strptime(header_lines[5][17:-1], "%Y-%m-%d %H:%M:%S")
        if header_lines[3].endswith(")"):
            data_tz = dt.timezone(dt.timedelta(hours=int(header_lines[3][45:-2])))
            self.META["logging_start"] = self.META["logging_start"].replace(tzinfo=data_tz)
            self.META["download_date"] = self.META["download_date"].replace(tzinfo=data_tz)
            self.META["utc_offset"] = data_tz
        sample_interval = dt.datetime.strptime(header_lines[6][17:-1], "%H:%M:%S")
        self.META["sample_interval"] = dt.timedelta(hours=sample_interval.hour, minutes=sample_interval.minute,
                                                    seconds=sample_interval.second)
        self.META['raw'] = "".join(header_lines)
        self.DATA = pd.DataFrame(data_lines[1:], columns=["date", "time", "TEMPERATURE"])
        self.DATA["TIME"] = pd.to_datetime(self.DATA["date"] + " " + self.DATA["time"], format="%Y-%m-%d %H:%M:%S")
        self.DATA["TEMPERATURE"] = pd.to_numeric(self.DATA["TEMPERATURE"], errors='coerce')
        self.DATA.drop(columns=["date", "time"], inplace=True)
        return
