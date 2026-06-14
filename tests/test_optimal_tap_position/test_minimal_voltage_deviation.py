from power_system_simulation.optimal_tap_position.minimal_voltage_deviation import compute_best_tap_voltage


def test_voltage_runs():
    results_per_tap = {
        0: {"output_data": {}, "timestamps": []},
        1: {"output_data": {}, "timestamps": []},
    }

    result = compute_best_tap_voltage(results_per_tap)
    assert result in results_per_tap
