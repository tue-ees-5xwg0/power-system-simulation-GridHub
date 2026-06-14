from ..grid_model import aggregate_line_results


def compute_best_tap_losses(results_per_tap):
    """
    Select tap position with minimal total energy loss.
    """

    losses_per_tap = {}

    for tap, data in results_per_tap.items():
        # get output data for this tap position
        output_data = data["output_data"]

        # get timestamps from data
        timestamps = data["timestamps"]

        # handle case where output_data is empty or timestamps are missing
        if isinstance(output_data, dict) and "output_data" in output_data:
            inner = output_data
            output_data = inner.get("output_data", {})
            timestamps = inner.get("timestamps", timestamps)

        if not output_data or len(timestamps) == 0:
            losses_per_tap[tap] = float("inf")
            continue

        try:
            # use aggregate_line_results to get total energy loss per line
            line_results = aggregate_line_results(output_data, timestamps)

            # sum total losses of all lines
            total_loss = line_results["Total_Loss"].sum()

        except Exception:
            total_loss = float("inf")

        losses_per_tap[tap] = total_loss

    # select tap with minimum loss
    best_tap = min(losses_per_tap, key=losses_per_tap.get)

    return best_tap
