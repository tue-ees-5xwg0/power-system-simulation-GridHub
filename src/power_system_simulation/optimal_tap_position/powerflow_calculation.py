import copy

from ..grid_model import construct_model, create_batch_update, run_power_flow


def run_powerflow_all_taps(model, tap_positions, input_data, active_profile, reactive_profile):
    """
    Runs time-series power flow for all tap positions.

    Returns:
        dict:
            {
                tap_position: {
                    "output_data": ...,
                    "timestamps": ...
                }
            }
    """

    results_per_tap = {}

    for tap in tap_positions:

        # copy input_data
        current_input_data = copy.deepcopy(input_data)

        # change transformer tap in input_data
        transformer_data = current_input_data["transformer"]

        for i in range(len(transformer_data)):
            transformer_data["tap_pos"][i] = tap

        # reconstruct model from modified input_data
        current_model = construct_model(current_input_data)

        # create batch update
        update_data, timestamps = create_batch_update(
            active_profile=active_profile,
            reactive_profile=reactive_profile,
        )

        # run power flow
        output_data = run_power_flow(
            model=current_model,
            input_data=current_input_data,
            update_data=update_data,
        )

        # store output_data and timestamps
        results_per_tap[tap] = {
            "output_data": output_data,
            "timestamps": timestamps,
        }

    return results_per_tap
