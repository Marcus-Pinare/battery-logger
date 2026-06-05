import os
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.pyplot import savefig
from pandas.errors import EmptyDataError


class BatteryTestLog:
    """Battery test log processor.

    Handles reading, validation, and processing of battery discharge test log files.
    Provides methods to extract discharge data and generate discharge curves.

    Attributes:
        log_path (Path): Resolved path to the log file.
        cell_number (int): Number of cells in the battery.
        battery_capacity (float): Battery capacity in ampere-hours (Ah).
        battery_voltage (float): Battery nominal voltage in volts (V).
        battery_manufacturer (str): Battery manufacturer name.
    """

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
        battery_manufacturer: str = "Battery",
    ) -> None:
        """Initialize BatteryTestLog.

        Args:
            log_path: Path to the battery test log file.
            battery_capacity: Battery capacity in ampere-hours. Must be > 0.
            battery_voltage: Battery nominal voltage in volts. Must be > 0.
            cell_number: Number of cells in the battery. Must be > 0.
            battery_manufacturer: Battery manufacturer name. Defaults to "Battery".

        Raises:
            ValueError: If log_path does not exist or is not a file.
            ValueError: If any numeric parameter is <= 0.
            ValueError: If the log file is invalid (via check_log_validity).
        """
        self.log_path = Path(log_path).resolve()

        if not self.log_path.exists() or not self.log_path.is_file():
            raise ValueError("File not found")

        self.check_log_validity(str(self.log_path))

        self.battery_manufacturer = battery_manufacturer

        if battery_capacity <= 0:
            raise ValueError("Battery capacity must be greater than 0")
        self.battery_capacity = battery_capacity

        if battery_voltage <= 0:
            raise ValueError("Battery voltage must be greater than 0")
        self.battery_voltage = battery_voltage

        if cell_number <= 0:
            raise ValueError("Cell number must be greater than 0")
        self.cell_number = cell_number

    def preprocess_log(self) -> None:
        """Preprocess the log file by removing the IT-M903C header line.

        Modifies the log file in place by removing the first line.
        """
        self.pop_first_file_line(str(self.log_path))

    def get_discharge_data(self) -> tuple:
        """Retrieve discharge data from the battery log.

        Extracts timestamp, voltage, and capacity data from the log file.
        Converts comma decimal separators to dots and handles numeric conversion.

        Returns:
            tuple: A tuple containing:
                - timestamp (pd.Series): Time of each observation.
                - voltage (pd.Series): Voltage at each observation time.
                - capacity (pd.Series): Remaining capacity at each observation time.

        Raises:
            pd.errors.EmptyDataError: If the log file is empty or has no valid data.
            pd.errors.ParserError: If the log file cannot be parsed as CSV.
        """
        df = pd.read_csv(str(self.log_path), skiprows=1, sep=";", usecols=[0, 2, 3])

        timestamp = pd.to_datetime(df["TestTime"], format="%H:%M:%S").dt.time

        voltage = pd.to_numeric(df["Voltage"].str.replace(",", "."), errors="coerce")

        capacity = pd.to_numeric(
            df["Capability"].str.replace(",", "."), errors="coerce"
        )
        capacity = abs((self.battery_capacity - capacity))

        return timestamp, voltage, capacity

    def generate_discharge_curve(
        self, capacity: pd.Series, voltage: pd.Series, out_path: str
    ) -> None:
        """Generate and save a discharge curve plot (Voltage vs Capacity).

        Args:
            capacity: Capacity data (x-axis).
            voltage: Voltage data (y-axis).
            out_path: Directory path where the plot image will be saved.

        Raises:
            ValueError: If out_path is not a valid directory.
        """
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

        savefig(str(path / f"{name}.png"))
        plt.close()

    @staticmethod
    def pop_first_file_line(file_path: str) -> str:
        """Delete the first line from a file.

        Args:
            file_path: Path to the file to modify.

        Returns:
            str: The deleted line.

        Raises:
            FileNotFoundError: If file_path does not exist.
            IOError: If file operations fail.
        """
        with open(file_path, "r") as f:
            first_line = f.readline()

        temp_path = f"{file_path}.tmp"
        with open(file_path, "r") as f_in, open(temp_path, "w") as f_out:
            next(f_in)
            shutil.copyfileobj(f_in, f_out)

        os.replace(temp_path, file_path)
        return first_line

    @staticmethod
    def check_log_validity(file_path: str) -> None:
        """Validate the battery test log file.

        Checks the file header and required columns.

        Args:
            file_path: Path to the log file to validate.

        Raises:
            ValueError: If the file header is invalid.
            EmptyDataError: If the CSV file is empty.
            ValueError: If any required column is missing.
        """
        with open(file_path, "r") as f:
            if f.readline() != "1@True@1\n":
                raise ValueError("File not valid")

        df = pd.read_csv(file_path, skiprows=1, nrows=2, sep=";")
        if df.empty:
            raise EmptyDataError("Empty csv file")

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
