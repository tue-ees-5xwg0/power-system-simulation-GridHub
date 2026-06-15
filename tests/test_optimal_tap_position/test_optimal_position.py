import json
from pathlib import Path

import pandas as pd
import pytest

from power_system_simulation.optimal_tap_position.optimal_position import get_optimal_tap
from power_system_simulation.optimal_tap_position.powerflow_calculation import run_powerflow_all_taps

# ---- Paths (adapted to YOUR structure) ----
TESTS_DIR = Path(__file__).resolve().parents[1]       # /tests
DATA_DIR = TESTS_DIR / "data"                         # /tests/data


def load_model():
    model_path = TESTS_DIR / "lv_validation_test_data.json"
    with open(model_path) as f:
        return json.load(f)


def load_profiles():
    active = pd.read_parquet(DATA_DIR / "active_power_profiel.parquet")
    reactive = pd.read_parquet(DATA_DIR / "reactive_power_profile.parquet")
    return active, reactive


def get_input_data():
    return {
        "mv_source_node": 0,
        "lv_busbar": 1,
        "transformer": 11,
        "lv_feeders": [16, 20],
        "source": 10
    }


def get_tap_positions():
    return [1, 2, 3, 4, 5]


# ✅ REAL DATA TEST — LOSSES
def test_get_optimal_tap_losses_real_data():

    model = load_model()
    active_profile, reactive_profile = load_profiles()
    input_data = get_input_data()
    tap_positions = get_tap_positions()

    results_per_tap = run_powerflow_all_taps(
        model,
        tap_positions,
        input_data,
        active_profile,
        reactive_profile
    )

    # Compute expected manually
    losses_per_tap = {}
    for tap, result in results_per_tap.items():
        # ⚠️ If this fails, check the actual key in your result
        losses_per_tap[tap] = result["losses"]

    expected_best = min(losses_per_tap, key=losses_per_tap.get)

    computed_best = get_optimal_tap(
        model,
        tap_positions,
        "losses",
        input_data,
        active_profile,
        reactive_profile
    )

    assert computed_best == expected_best


# ✅ REAL DATA TEST — VOLTAGE
def test_get_optimal_tap_voltage_real_data():

    model = load_model()
    active_profile, reactive_profile = load_profiles()
    input_data = get_input_data()
    tap_positions = get_tap_positions()

    results_per_tap = run_powerflow_all_taps(
        model,
        tap_positions,
        input_data,
        active_profile,
        reactive_profile
    )

    voltage_scores = {}
    for tap, result in results_per_tap.items():
        # ⚠️ If this fails, check actual key name
        voltage_scores[tap] = result["voltage_deviation"]

    expected_best = min(voltage_scores, key=voltage_scores.get)

    computed_best = get_optimal_tap(
        model,
        tap_positions,
        "voltage",
        input_data,
        active_profile,
        reactive_profile
    )

    assert computed_best == expected_best


# ✅ KEEP THIS TEST
def test_get_optimal_tap_invalid():

    with pytest.raises(ValueError):
        get_optimal_tap(None, [0], "invalid", None, None, None)
