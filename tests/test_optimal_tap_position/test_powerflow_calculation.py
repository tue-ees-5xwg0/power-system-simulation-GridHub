from pathlib import Path

import pandas as pd

from power_system_simulation.grid_model import load_input_data
from power_system_simulation.optimal_tap_position.powerflow_calculation import run_powerflow_all_taps

TEST_DIR = Path(__file__).resolve().parent


def load_model():
    return load_input_data(TEST_DIR / "input_network_data.json")


def load_profiles():
    active = pd.read_parquet(TEST_DIR / "active_power_profile.parquet")
    reactive = pd.read_parquet(TEST_DIR / "reactive_power_profile.parquet")
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


def test_run_powerflow_all_taps_real_data():

    model = load_model()
    active_profile, reactive_profile = load_profiles()
    input_data = get_input_data()
    tap_positions = get_tap_positions()

    results = run_powerflow_all_taps(
        model,
        tap_positions,
        input_data,
        active_profile,
        reactive_profile
    )

    # basic checks
    assert isinstance(results, dict)
    assert len(results) == len(tap_positions)

    for tap in tap_positions:
        assert tap in results
        assert "output_data" in results[tap]
        assert "timestamps" in results[tap]

        # basic checks
        assert len(results[tap]["timestamps"]) == len(active_profile)

def test_run_powerflow_all_taps_none_branch(monkeypatch):

    import pandas as pd

    # minimal valid profiles
    df = pd.DataFrame([[1.0]], columns=[12])

    input_data = {
        "transformer": {"tap_pos": [0]}
    }

    tap_positions = [1]

    # mock heavy functions
    monkeypatch.setattr(
        "power_system_simulation.optimal_tap_position.powerflow_calculation.construct_model",
        lambda x: None
    )
    monkeypatch.setattr(
        "power_system_simulation.optimal_tap_position.powerflow_calculation.run_power_flow",
        lambda **kwargs: {}
    )
    monkeypatch.setattr(
        "power_system_simulation.optimal_tap_position.powerflow_calculation.create_batch_update",
        lambda **kwargs: ({}, [0])
    )

    results = run_powerflow_all_taps(
        model=None,
        tap_positions=tap_positions,
        input_data=input_data,
        active_profile=df,
        reactive_profile=df,
    )

    assert 1 in results
