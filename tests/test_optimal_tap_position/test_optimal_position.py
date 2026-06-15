from pathlib import Path

import pandas as pd
import pytest

from power_system_simulation.grid_model import load_input_data
from power_system_simulation.optimal_tap_position.optimal_position import get_optimal_tap
from power_system_simulation.optimal_tap_position.powerflow_calculation import run_powerflow_all_taps

# path to folder
TEST_DIR = Path(__file__).resolve().parent


def load_model():
    model_path = TEST_DIR / "input_network_data.json"
    return load_input_data(model_path)


def load_profiles():
    active = pd.read_parquet(TEST_DIR / "active_power_profile.parquet")
    reactive = pd.read_parquet(TEST_DIR / "reactive_power_profile.parquet")
    return active, reactive


def get_input_data():
    return {"mv_source_node": 0, "lv_busbar": 1, "transformer": 11, "lv_feeders": [16, 20], "source": 10}


def get_tap_positions():
    return [1, 2, 3, 4, 5]


# test using real data for minimal energy loss criterion
def test_get_optimal_tap_losses_real_data():
    model = load_model()
    active_profile, reactive_profile = load_profiles()
    input_data = get_input_data()
    tap_positions = get_tap_positions()

    results_per_tap = run_powerflow_all_taps(model, tap_positions, input_data, active_profile, reactive_profile)

    # compute expected result manually
    losses_per_tap = {}

    for tap, result in results_per_tap.items():
        output_data = result["output_data"]
        timestamps = result["timestamps"]

        # use your aggregation function
        from power_system_simulation.grid_model import aggregate_line_results

        line_df = aggregate_line_results(output_data, timestamps)

        total_loss = line_df["Total_Loss"].sum()
        losses_per_tap[tap] = total_loss

    expected_best = min(losses_per_tap, key=losses_per_tap.get)

    # run function
    computed_best = get_optimal_tap(model, tap_positions, "losses", input_data, active_profile, reactive_profile)

    assert computed_best == expected_best


# test using real data for minimal voltage deviation criterion
def test_get_optimal_tap_voltage_real_data():
    model = load_model()
    active_profile, reactive_profile = load_profiles()
    input_data = get_input_data()
    tap_positions = get_tap_positions()

    results_per_tap = run_powerflow_all_taps(model, tap_positions, input_data, active_profile, reactive_profile)

    voltage_scores = {}

    for tap, result in results_per_tap.items():
        output_data = result["output_data"]
        timestamps = result["timestamps"]

        from power_system_simulation.grid_model import aggregate_voltage_results

        voltage_df = aggregate_voltage_results(output_data, timestamps)

        # deviation from 1 p.u.
        deviation = ((voltage_df["Max_Voltage"] - 1).abs() + (voltage_df["Min_Voltage"] - 1).abs()).mean()

        voltage_scores[tap] = deviation

    expected_best = min(voltage_scores, key=voltage_scores.get)

    computed_best = get_optimal_tap(model, tap_positions, "voltage", input_data, active_profile, reactive_profile)

    assert computed_best == expected_best


# invalid criterion should raise error
def test_get_optimal_tap_invalid():
    with pytest.raises(ValueError):
        get_optimal_tap(None, [0], "invalid", None, None, None)
