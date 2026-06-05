import os
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.pyplot import savefig
from pandas.errors import EmptyDataError


class BatteryTestLog:
    log_path: Path
    cell_number: int
    battery_capacity: float  # A.h
    battery_voltage: float  # V
    battery_manufacturer: str

    def __init__(
        self,
        log_path: str,
        battery_capacity: float,
        battery_voltage: float,
        cell_number: int,
        battery_manufacturer="Battery",
    ):
        self.log_path = Path(log_path).resolve()

        if not self.log_path.exists() or not self.log_path.is_file():
            raise ValueError("File not found")

        # # Check the csv
        self.check_log_validity(str(self.log_path))

        self.battery_manufacturer = battery_manufacturer

        # Capacity
        if battery_capacity <= 0:
            raise ValueError("Battery capacity must be greater than 0")
        self.battery_capacity = battery_capacity

        # Voltage
        if battery_voltage <= 0:
            raise ValueError("Battery voltage must be greater than 0")
        self.battery_voltage = battery_voltage

        # Cell number
        if cell_number <= 0:
            raise ValueError("Cell number must be greater than 0")
        self.cell_number = cell_number

    def preprocess_log(self):
        """
        Preprocess a csv log by removing the IT-M903C header.
        :return:
        """
        self.pop_first_file_line(str(self.log_path))

    def get_discharge_data(self):
        """
        Retrieve timestamp, voltage and capacity from battery log.
        :return: tuple(time, voltage, capacity)
        """
        df = pd.read_csv(str(self.log_path), skiprows=1, sep=";", usecols=[0, 2, 3])

        timestamp = pd.to_datetime(df["TestTime"], format="%H:%M:%S").dt.time

        # Voltage and swap , for .
        voltage = pd.to_numeric(df["Voltage"].str.replace(",", "."), errors="coerce")

        # Capacity and swap , for .
        capacity = pd.to_numeric(
            df["Capability"].str.replace(",", "."), errors="coerce"
        )
        capacity = abs((self.battery_capacity - capacity))

        return timestamp, voltage, capacity

    def generate_discharge_curve(self, capacity, voltage, out_path: str):
        # Output path checking
        path = Path(out_path).resolve()
        if not path.exists() or not path.is_dir():
            raise ValueError("Invalid output path")

        name = (
            f"{self.battery_manufacturer}_"
            f"{self.battery_capacity}Ah_"
            f"{self.battery_voltage}V_"
            f"{self.cell_number}S_Discharge_curve"
        )

        plt.ylabel("Voltage [V]")
        plt.xlabel("Capacity [A.h]")
        plt.title(name)
        plt.grid(True)
        plt.plot(capacity, voltage)

        savefig(out_path + name + ".png")

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
        # Check the file validity
        with open(file_path, "r") as f:
            if f.readline() != "1@True@1\n":
                raise ValueError("File not valid")

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


tmp = BatteryTestLog(
    "/home/vscode/workspace/packages/IT-M903C/IT_M903C/battery_test/tmp.csv",
    33,
    44.4,
    12,
    "RACEPOW",
)
# tmp.preprocess_log()
print(tmp.log_path)
print(tmp.get_discharge_data())
time, voltage, capability = tmp.get_discharge_data()
print(tmp.generate_discharge_curve(capability, voltage, ""))
