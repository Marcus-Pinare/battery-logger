from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
from IT_M903C.battery_test.battery_test_log import BatteryTestLog


class BatteryTestReport:
    """Battery test report generator.

    Aggregates and processes discharge data from multiple battery test logs.
    Handles multiple tests with identical discharge rates by assigning unique test IDs.

    Attributes:
        cell_number (int): Number of cells in the battery.
        battery_capacity (float): Battery capacity in ampere-hours.
        battery_voltage (float): Battery nominal voltage in volts.
        battery_manufacturer (str): Battery manufacturer name.
        inventory (pd.DataFrame): DataFrame mapping discharge rates to log file paths,
            indexed by unique test IDs.
    """

    cell_number: int
    battery_capacity: float  # A.h
    battery_voltage: float  # V
    battery_manufacturer: str

    def __init__(
        self,
        cell_number: int,
        battery_capacity: float,
        battery_voltage: float,
        current_charge: List[str],
        log_file_path: List[str],
        battery_manufacturer: str = "",
    ) -> None:
        """Initialize BatteryTestReport.

        Args:
            cell_number: Number of cells in the battery. Must be > 0.
            battery_capacity: Battery capacity in ampere-hours. Must be > 0.
            battery_voltage: Battery nominal voltage in volts. Must be > 0.
            current_charge: List of discharge rates (e.g., ["1C", "2C"]).
            log_file_path: List of paths to log files, aligned with current_charge.
            battery_manufacturer: Battery manufacturer name. Defaults to empty string.

        Raises:
            ValueError: If any numeric parameter is <= 0.
            ValueError: If log files are invalid (via BatteryTestLog.
            check_log_validity).
            ValueError: If current_charge and log_file_path have
            different lengths.
        """
        if len(current_charge) != len(log_file_path):
            raise ValueError(
                "current_charge and log_file_path must have the same length"
            )

        # Validate log files
        for path in log_file_path:
            BatteryTestLog.check_log_validity(path)

        # Create inventory with unique test IDs as index
        test_ids = [f"test_{i}" for i in range(len(current_charge))]
        self.inventory = pd.DataFrame(
            {"Discharge Rate": current_charge, "Path": log_file_path},
            index=pd.Index(test_ids, name="TestID"),
        )

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

    def add_battery_test(self, current_charge: str, path: str) -> None:
        """Add a new battery test to the inventory.

        Args:
            current_charge: Discharge rate (e.g., "1C").
            path: Path to the log file.

        Raises:
            ValueError: If the log file is invalid.
        """
        BatteryTestLog.check_log_validity(path)
        new_index = f"test_{len(self.inventory)}"
        new_row = pd.DataFrame(
            {"Discharge Rate": [current_charge], "Path": [path]}, index=[new_index]
        )
        self.inventory = pd.concat([self.inventory, new_row])

    def remove_battery_test(self, test_id: str) -> None:
        """Remove a test from the inventory.

        Args:
            test_id: The TestID of the test to remove.

        Raises:
            KeyError: If test_id does not exist in inventory.
        """
        self.inventory.drop(test_id, inplace=True)

    def generate_raw_discharge_report(self) -> pd.DataFrame:
        """Generate a consolidated DataFrame of discharge data from all test logs.

        Each row corresponds to a single timestamp observation, with columns for
        test ID, discharge rate, timestamp, voltage, and capacity.

        Returns:
            pd.DataFrame: DataFrame with columns:
                - Test ID: Unique identifier for each test (from inventory index).
                - Discharge Rate: Discharge rate from current_charge.
                - Timestamp: Time of observation.
                - Voltage: Voltage at observation time.
                - Capacity: Capacity at observation time.

        Raises:
            Any exception raised by BatteryTestLog initialization or get_discharge_data.
        """
        all_data = []
        for test_id, row in self.inventory.iterrows():
            log = BatteryTestLog(
                row["Path"],
                self.cell_number,
                self.battery_capacity,
                self.battery_voltage,
                self.battery_manufacturer,
            )
            timestamp, vol, cap = log.get_discharge_data()
            df_temp = pd.DataFrame(
                {
                    "Test ID": test_id,
                    "Discharge Rate": row["Discharge Rate"],
                    "Timestamp": timestamp,
                    "Voltage": vol,
                    "Capacity": cap,
                }
            )
            all_data.append(df_temp)
        return pd.concat(all_data, ignore_index=True)

    def generate_discharge_curve(self, out_path: str) -> None:
        """Generate and save discharge curves (Voltage vs Capacity) for all tests.

        Each test is plotted as a separate curve on the same axes. Tests are identified
        by their TestID and discharge rate in the legend. The plot is saved as
        a PNG file.

        Args:
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

        data = self.generate_raw_discharge_report()
        plt.figure(figsize=(10, 6))

        for test_id in data["Test ID"].unique():
            test_data = data[data["Test ID"] == test_id]
            discharge_rate = test_data["Discharge Rate"].iloc[0]
            plt.plot(
                test_data["Capacity"],
                test_data["Voltage"],
                label=f"{test_id} ({discharge_rate})",
            )

        plt.ylabel("Voltage [V]")
        plt.xlabel("Capacity [A.h]")
        plt.title(name)
        plt.legend()
        plt.grid(True)
        plt.savefig(str(path / f"{name}.png"))
        plt.close()
