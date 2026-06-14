from ..grid_model import aggregate_line_results


def compute_best_tap_losses(results_per_tap):
    """
    Select tap position with minimal total energy loss.
    """

    losses_per_tap = {}

    for tap, output_data in results_per_tap.items():

        # get timestamps from output_data
        timestamps = output_data["timestamps"]

        # use aggregate_line_results to get total energy loss per line
        line_results = aggregate_line_results(output_data, timestamps)

        # sum total losses of all lines
        total_loss = line_results["Total_Loss"].sum()

        losses_per_tap[tap] = total_loss

    # select tap with minimum loss
    best_tap = min(losses_per_tap, key=losses_per_tap.get)

    return best_tap
