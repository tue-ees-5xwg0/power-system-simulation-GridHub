from ..grid_model import create_batch_update, run_power_flow


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

    # create batch update
    update_data, timestamps = create_batch_update(
            active_profile=active_profile,
            reactive_profile=reactive_profile,
        )

    for tap in tap_positions:

        # copy model
        import copy
        current_model = copy.deepcopy(model)

        # set transformer tap
        transformer_data = current_model.input_data["transformer"]
        transformer_data["tap_pos"] = tap

        # run power flow
        output_data = run_power_flow(
            model=current_model,
            input_data=input_data,
            update_data=update_data,
        )

        # store output_data and timestamps
        results_per_tap[tap] = {
            "output_data": output_data,
            "timestamps": timestamps,
        }

    return results_per_tap
