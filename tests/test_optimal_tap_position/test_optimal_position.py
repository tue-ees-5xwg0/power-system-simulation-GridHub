import pytest

from power_system_simulation.optimal_tap_position.optimal_position import (
    get_optimal_tap,
)
from power_system_simulation.optimal_tap_position.powerflow_calculation import (
    run_powerflow_all_taps,
)


# test using real data for minimal energy loss criterion
def test_get_optimal_tap_losses_real_data(model, profiles, input_data, tap_positions):
    active_profile, reactive_profile = profiles

    results_per_tap = run_powerflow_all_taps(
        model,
        tap_positions,
        input_data,
        active_profile,
        reactive_profile,
    )

    # compute expected result manually
    losses_per_tap = {}

    from power_system_simulation.grid_model import aggregate_line_results

    for tap, result in results_per_tap.items():
        output_data = result["output_data"]
        timestamps = result["timestamps"]

        # use aggregation function
        line_df = aggregate_line_results(output_data, timestamps)

        total_loss = line_df["Total_Loss"].sum()
        losses_per_tap[tap] = total_loss

    expected_best = min(losses_per_tap, key=losses_per_tap.get)

    # run function
    computed_best = get_optimal_tap(
        model,
        tap_positions,
        "losses",
        input_data,
        active_profile,
        reactive_profile,
    )

    assert computed_best == expected_best


# test using real data for minimal voltage deviation criterion
def test_get_optimal_tap_voltage_real_data(model, profiles, input_data, tap_positions):
    active_profile, reactive_profile = profiles

    results_per_tap = run_powerflow_all_taps(
        model,
        tap_positions,
        input_data,
        active_profile,
        reactive_profile,
    )

    voltage_scores = {}

    from power_system_simulation.grid_model import aggregate_voltage_results

    for tap, result in results_per_tap.items():
        output_data = result["output_data"]
        timestamps = result["timestamps"]

        voltage_df = aggregate_voltage_results(output_data, timestamps)

        # deviation from 1 p.u.
        deviation = ((voltage_df["Max_Voltage"] - 1).abs() + (voltage_df["Min_Voltage"] - 1).abs()).mean()

        voltage_scores[tap] = deviation

    expected_best = min(voltage_scores, key=voltage_scores.get)

    # run function
    computed_best = get_optimal_tap(
        model,
        tap_positions,
        "voltage",
        input_data,
        active_profile,
        reactive_profile,
    )

    assert computed_best == expected_best


# invalid criterion should raise error
def test_get_optimal_tap_invalid():
    with pytest.raises(ValueError):
        get_optimal_tap(None, [0], "invalid", None, None, None)
