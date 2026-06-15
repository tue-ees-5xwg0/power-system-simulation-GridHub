from pathlib import Path

import pandas as pd

from power_system_simulation.grid_model import aggregate_line_results, load_input_data
from power_system_simulation.optimal_tap_position.minimal_energy_loss import compute_best_tap_losses
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


def test_minimal_energy_loss_real_data():
    model = load_model()
    active_profile, reactive_profile = load_profiles()
    input_data = get_input_data()
    tap_positions = get_tap_positions()

    results_per_tap = run_powerflow_all_taps(model, tap_positions, input_data, active_profile, reactive_profile)

    # compute expected manually
    losses_per_tap = {}

    for tap, result in results_per_tap.items():
        line_df = aggregate_line_results(result["output_data"], result["timestamps"])

        losses_per_tap[tap] = line_df["Total_Loss"].sum()

    expected_best = min(losses_per_tap, key=losses_per_tap.get)

    computed_best = compute_best_tap_losses(results_per_tap)

    assert computed_best == expected_best
