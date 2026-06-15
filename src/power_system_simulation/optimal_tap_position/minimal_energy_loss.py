from ..grid_model import aggregate_line_results


def compute_best_tap_losses(results_per_tap):
    """
    Select tap position with minimal total energy loss.
    """

    best_tap = None
    best_value = None

    for tap, data in results_per_tap.items():
        # load output data and timestamps
        output_data = data["output_data"]
        timestamps = data["timestamps"]

        # compute losses
        line_results = aggregate_line_results(output_data, timestamps)
        total_loss = line_results["Total_Loss"].sum()

        # select best tap
        if best_value is None or total_loss < best_value:
            best_value = total_loss
            best_tap = tap

    return best_tap
