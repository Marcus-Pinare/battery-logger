from ..battery_test.battery_test_log import BatteryTestLog


def preprocess_battery_log(path: str, capacity, voltage, cell_number, manufacutrer=""):
    """Preprocess csv file from IT_M903C battery tester.

    Args:
        path (str): Path to the .csv log file.
    """
    bat_log = BatteryTestLog(
        path, capacity, voltage, cell_number, manufacutrer=manufacutrer
    )
    bat_log.preprocess_log()


def main():
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre process csv file from IT_M903C battery tester."
    )
    parser.add_argument("path", type=str, help="Path to the input .csv file")
    parser.add_argument(
        "capacity", type=float, help="Total capacity of the battery in A.h"
    )
    parser.add_argument("voltage", type=float, help="Nominal voltage in V.")
    parser.add_argument("cell_num", type=float, help="Cell number (1S, 2S, 6S, ...)")
    parser.add_argument("manufacturer", type=float, help="Manufacturer name")

    args = parser.parse_args()
    preprocess_battery_log(
        args.path, args.capacity, args.voltage, args.cell_num, args.manufacturer
    )


if __name__ == "__main__":
    main()
