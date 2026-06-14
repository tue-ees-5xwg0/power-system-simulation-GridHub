from ..grid_model import aggregate_voltage_results


def compute_best_tap_voltage(results_per_tap):
    """
    Select tap position with minimal voltage deviation from 1 p.u.
    """

    deviation_per_tap = {}

    for tap, data in results_per_tap.items():

        output_data = data["output_data"]
        timestamps = data["timestamps"]

        # process power flow results into voltage metrics per timestamp
        voltage_results = aggregate_voltage_results(output_data, timestamps)

        total_deviation = 0.0

        # loop over all timesteps
        for _, row in voltage_results.iterrows():
            v_max = row["Max_Voltage"]
            v_min = row["Min_Voltage"]

            # compute deviation from 1 p.u.
            deviation = abs(v_max - 1.0) + abs(v_min - 1.0)

            total_deviation += deviation

        # average deviation over time
        avg_deviation = total_deviation / len(voltage_results)

        deviation_per_tap[tap] = avg_deviation

    # select tap with minimum deviation
    best_tap = min(deviation_per_tap, key=deviation_per_tap.get)

    return best_tap
