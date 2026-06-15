from pathlib import Path

import pandas as pd
import pytest

from power_system_simulation.grid_model import load_input_data

# base directory for test data
TEST_DIR = Path(__file__).resolve().parent


# load PGM model
@pytest.fixture
def model():
    return load_input_data(TEST_DIR / "input_network_data.json")


# load active & reactive profiles
@pytest.fixture
def profiles():
    active = pd.read_parquet(TEST_DIR / "active_power_profile.parquet")
    reactive = pd.read_parquet(TEST_DIR / "reactive_power_profile.parquet")
    return active, reactive


# input metadata
@pytest.fixture
def input_data():
    return {
        "mv_source_node": 0,
        "lv_busbar": 1,
        "transformer": 11,
        "lv_feeders": [16, 20],
        "source": 10,
    }


# tap positions to test
@pytest.fixture
def tap_positions():
    return [1, 2, 3, 4, 5]
