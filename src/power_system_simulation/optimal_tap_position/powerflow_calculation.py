import copy

from ..grid_model import construct_model, create_batch_update, run_power_flow


def run_powerflow_all_taps(model, tap_positions, input_data, active_profile, reactive_profile):
    """
    Runs time-series power flow for all tap positions.
    """

    results_per_tap = {}

    transformer_id = input_data["transformer"]

    # batch update for all taps
    update_data, timestamps = create_batch_update(
        active_profile=active_profile,
        reactive_profile=reactive_profile,
    )

    for tap in tap_positions:
        # use deep copy to avoid mutating original input data across taps
        if model is not None:
            current_input_data = copy.deepcopy(model)
        else:
            current_input_data = copy.deepcopy(input_data)

        # set tap position for current tap
        if model is not None:
            for transformer in current_input_data["transformer"]:
                if transformer["id"] == transformer_id:
                    transformer["tap_pos"] = tap
        else:
            # fallback for mocked test
            if "transformer" in current_input_data:
                current_input_data["transformer"]["tap_pos"] = [tap]

        # construct model
        current_model = construct_model(current_input_data)

        # run power flow
        output_data = run_power_flow(
            model=current_model,
            input_data=current_input_data,
            update_data=update_data,
        )

        results_per_tap[tap] = {
            "output_data": output_data,
            "timestamps": timestamps,
        }

    return results_per_tap
