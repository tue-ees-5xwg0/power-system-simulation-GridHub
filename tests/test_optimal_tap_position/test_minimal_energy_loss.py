from power_system_simulation.optimal_tap_position.minimal_energy_loss import compute_best_tap_losses


def test_compute_best_tap_losses_runs():
    """
    Test that the function runs and returns a valid tap.
    """

    # minimal valid structure (you don't test aggregation correctness here)
    results_per_tap = {
        0: {"output_data": {}, "timestamps": []},
        1: {"output_data": {}, "timestamps": []},
    }

    result = compute_best_tap_losses(results_per_tap)

    # just check valid output
    assert result in results_per_tap.keys()
