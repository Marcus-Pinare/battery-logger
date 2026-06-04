import os
import shutil
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError


class BatteryTestLog:
    log_path: Path

    def __init__(self, log_path: str):
        self.log_path = Path(log_path).resolve()

        if not self.log_path.exists() or not self.log_path.is_file():
            raise ValueError("File not found")

        # # Check the csv
        self.check_log_validity(str(self.log_path))

    def preprocess_log(self):
        self.pop_first_file_line(str(self.log_path))

    @staticmethod
    def pop_first_file_line(file_path: str):
        """
        Delete first line from a file.
        :return: The deleted line
        """
        with open(file_path, "r") as f:
            first_line = f.readline()  # Read first line

        # Create temp file
        temp_path = f"{file_path}.tmp"
        with open(file_path, "r") as f_in, open(temp_path, "w") as f_out:
            next(f_in)  # Skip first line
            shutil.copyfileobj(f_in, f_out)

        os.replace(temp_path, file_path)
        return first_line

    @staticmethod
    def check_log_validity(file_path: str):
        # Check the csv
        df = pd.read_csv(file_path, skiprows=1, nrows=2, sep=";")
        if df.empty:
            raise EmptyDataError("Empty csv file")

        # Validate required columns
        required_columns = [
            "Voltage",
            "CurrentA",
            "Capability",
            "TestTime",
            "RunCount",
            "SaveTime",
        ]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Column {col} not in csv file")
