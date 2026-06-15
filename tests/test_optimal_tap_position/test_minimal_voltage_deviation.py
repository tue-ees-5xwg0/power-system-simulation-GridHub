import pandas as pd

from power_system_simulation.grid_model import aggregate_voltage_results
from power_system_simulation.optimal_tap_position.minimal_voltage_deviation import (
    compute_best_tap_voltage,
)
from power_system_simulation.optimal_tap_position.powerflow_calculation import (
    run_powerflow_all_taps,
)


def test_minimal_voltage_deviation_real_data(model, profiles, input_data, tap_positions):
    active_profile, reactive_profile = profiles

    results_per_tap = run_powerflow_all_taps(
        model,
        tap_positions,
        input_data,
        active_profile,
        reactive_profile,
    )

    voltage_scores = {}

    for tap, result in results_per_tap.items():
        df = aggregate_voltage_results(
            result["output_data"],
            result["timestamps"],
        )

        deviation = ((df["Max_Voltage"] - 1).abs() + (df["Min_Voltage"] - 1).abs()).mean()

        voltage_scores[tap] = deviation

    expected_best = min(voltage_scores, key=voltage_scores.get)

    computed_best = compute_best_tap_voltage(results_per_tap)

    assert computed_best == expected_best


def test_minimal_voltage_single_tap(monkeypatch):
    from power_system_simulation.optimal_tap_position import (
        minimal_voltage_deviation as mvd,
    )

    results = {1: {"output_data": "A", "timestamps": [0]}}

    def fake_aggregate_voltage_results(output_data, timestamps):
        return pd.DataFrame(
            {
                "Max_Voltage": [1.0],
                "Min_Voltage": [1.0],
            }
        )

    monkeypatch.setattr(
        "power_system_simulation.optimal_tap_position.minimal_voltage_deviation.aggregate_voltage_results",
        fake_aggregate_voltage_results,
    )

    best = mvd.compute_best_tap_voltage(results)

    assert best == 1
