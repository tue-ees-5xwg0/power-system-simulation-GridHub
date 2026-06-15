from power_system_simulation.grid_model import aggregate_line_results
from power_system_simulation.optimal_tap_position.minimal_energy_loss import compute_best_tap_losses
from power_system_simulation.optimal_tap_position.powerflow_calculation import run_powerflow_all_taps


def test_minimal_energy_loss_real_data(model, profiles, input_data, tap_positions):
    active_profile, reactive_profile = profiles

    results_per_tap = run_powerflow_all_taps(
        model,
        tap_positions,
        input_data,
        active_profile,
        reactive_profile,
    )

    # compute expected manually
    losses_per_tap = {}

    for tap, result in results_per_tap.items():
        line_df = aggregate_line_results(
            result["output_data"],
            result["timestamps"],
        )

        losses_per_tap[tap] = line_df["Total_Loss"].sum()

    expected_best = min(losses_per_tap, key=losses_per_tap.get)

    computed_best = compute_best_tap_losses(results_per_tap)

    assert computed_best == expected_best
