from power_system_simulation.grid_model import aggregate_voltage_results


def compute_best_tap_voltage(results_per_tap):
    """
    Determines the optimal tap position based on minimal voltage deviation.

    Args:
        results_per_tap (dict): Output of run_powerflow_all_taps

    Returns:
        int: Optimal tap position
    """

    best_tap = None
    best_value = None

    for tap, result in results_per_tap.items():

        # load output data and timestamps
        output_data = result["output_data"]
        timestamps = result["timestamps"]

        # compute voltage results
        df = aggregate_voltage_results(output_data, timestamps)

        # compute deviation from 1.0 pu
        avg_deviation = (
            (df["Max_Voltage"] - 1).abs() +
            (df["Min_Voltage"] - 1).abs()
        ).mean()

        # select best tap
        if best_value is None or avg_deviation < best_value:
            best_value = avg_deviation
            best_tap = tap

    return best_tap
