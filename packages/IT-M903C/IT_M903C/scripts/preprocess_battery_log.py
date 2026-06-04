from IT_M903C.battery_test.battery_test_log import BatteryTestLog


def preprocess_battery_log(path: str):
    """Preprocess csv file from IT_M903C battery tester.

    Args:
        path (str): Path to the .csv log file.
    """
    bat_log = BatteryTestLog(path)
    bat_log.preprocess_log()


def main():
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre process csv file from IT_M903C battery tester."
    )
    parser.add_argument("input", type=str, help="Path to the input .csv file")
    args = parser.parse_args()
    preprocess_battery_log(args.input)


if __name__ == "__main__":
    main()
