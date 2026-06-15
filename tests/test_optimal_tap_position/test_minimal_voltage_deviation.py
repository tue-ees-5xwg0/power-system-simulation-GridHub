from pathlib import Path

import pandas as pd

from power_system_simulation.grid_model import aggregate_voltage_results, load_input_data
from power_system_simulation.optimal_tap_position.minimal_voltage_deviation import compute_best_tap_voltage
from power_system_simulation.optimal_tap_position.powerflow_calculation import run_powerflow_all_taps

TEST_DIR = Path(__file__).resolve().parent


def load_model():
    return load_input_data(TEST_DIR / "input_network_data.json")


def load_profiles():
    active = pd.read_parquet(TEST_DIR / "active_power_profile.parquet")
    reactive = pd.read_parquet(TEST_DIR / "reactive_power_profile.parquet")
    return active, reactive


def get_input_data():
    return {"mv_source_node": 0, "lv_busbar": 1, "transformer": 11, "lv_feeders": [16, 20], "source": 10}


def get_tap_positions():
    return [1, 2, 3, 4, 5]


def test_minimal_voltage_deviation_real_data():
    model = load_model()
    active_profile, reactive_profile = load_profiles()
    input_data = get_input_data()
    tap_positions = get_tap_positions()

    results_per_tap = run_powerflow_all_taps(model, tap_positions, input_data, active_profile, reactive_profile)

    voltage_scores = {}

    for tap, result in results_per_tap.items():
        df = aggregate_voltage_results(result["output_data"], result["timestamps"])

        deviation = ((df["Max_Voltage"] - 1).abs() + (df["Min_Voltage"] - 1).abs()).mean()

        voltage_scores[tap] = deviation

    expected_best = min(voltage_scores, key=voltage_scores.get)

    computed_best = compute_best_tap_voltage(results_per_tap)

    assert computed_best == expected_best


def test_minimal_voltage_single_tap(monkeypatch):
    from power_system_simulation.optimal_tap_position import minimal_voltage_deviation as mvd

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
