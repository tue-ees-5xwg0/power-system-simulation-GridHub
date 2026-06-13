from pathlib import Path

import pandas as pd
import pytest
from power_grid_model import ComponentType
from power_grid_model.utils import json_deserialize
from power_grid_model.validation import ValidationException

from power_system_simulation.grid_model import ProfileMismatchError
from power_system_simulation.lv_validation import (
    ComponentCountError,
    InvalidFeederError,
    TopologyError,
    validate_lv_grid_data,
)


@pytest.fixture
def valid_grid_data():
    current_dir = Path(__file__).parent
    json_path = current_dir / "lv_validation_test_data.json"

    # Read and deserialize
    json_str = json_path.read_text()
    return json_deserialize(json_str)


@pytest.fixture
def valid_profiles():
    ts = pd.date_range("2024-01-01", periods=2, freq="h")
    # 4 sym_loads in the network: 12, 13, 14, 15
    active = pd.DataFrame({12: [100.0, 150.0], 13: [200.0, 250.0], 14: [100.0, 150.0], 15: [200.0, 250.0]}, index=ts)
    reactive = pd.DataFrame({12: [10.0, 15.0], 13: [20.0, 25.0], 14: [10.0, 15.0], 15: [20.0, 25.0]}, index=ts)
    # Must have at least 4 EV profiles
    ev = pd.DataFrame({0: [3000.0, 3000.0], 1: [0.0, 0.0], 2: [3000.0, 0.0], 3: [0.0, 3000.0]}, index=ts)
    return active, reactive, ev


# Feeders connected to the transformer 'to_node' (node 1) are lines 16 and 20
def test_valid_input_passes(valid_grid_data, valid_profiles):
    active, reactive, ev = valid_profiles
    validate_lv_grid_data(valid_grid_data, [16, 20], active, reactive, ev)


def test_missing_transformer(valid_grid_data, valid_profiles):
    valid_grid_data.pop(ComponentType.transformer)
    with pytest.raises(ComponentCountError, match="exactly one transformer"):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)


def test_invalid_feeder_id(valid_grid_data, valid_profiles):
    with pytest.raises(InvalidFeederError, match="not a valid line ID"):
        validate_lv_grid_data(valid_grid_data, [999], *valid_profiles)


def test_feeder_wrong_node(valid_grid_data, valid_profiles):
    # Change the from_node of line 16 to node 9, detaching it from the transformer
    valid_grid_data[ComponentType.line]["from_node"][0] = 9
    with pytest.raises(InvalidFeederError, match="does not match transformer"):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)


def test_topology_not_connected(valid_grid_data, valid_profiles):
    # Disconnect line 17, severing node 3
    valid_grid_data[ComponentType.line]["to_status"][1] = 0
    with pytest.raises(TopologyError, match="not fully connected"):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)


def test_topology_has_cycle(valid_grid_data, valid_profiles):
    # Line 24 is disconnected by default. Reconnect it to form a ring.
    valid_grid_data[ComponentType.line]["to_status"][8] = 1
    with pytest.raises(TopologyError, match="contains cycles"):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)


def test_mismatching_timestamps(valid_grid_data, valid_profiles):
    active, reactive, ev = valid_profiles
    reactive.index = reactive.index + pd.Timedelta(hours=1)
    with pytest.raises(ProfileMismatchError, match="mismatching timestamps"):
        validate_lv_grid_data(valid_grid_data, [16, 20], active, reactive, ev)


def test_mismatching_load_ids(valid_grid_data, valid_profiles):
    active, reactive, ev = valid_profiles
    reactive.columns = [12, 13, 14, 99]
    with pytest.raises(ProfileMismatchError, match="mismatching load IDs"):
        validate_lv_grid_data(valid_grid_data, [16, 20], active, reactive, ev)


def test_invalid_load_ids_in_profile(valid_grid_data, valid_profiles):
    active, reactive, ev = valid_profiles
    active.columns = [12, 13, 14, 99]
    reactive.columns = [12, 13, 14, 99]
    with pytest.raises(ProfileMismatchError, match="contain invalid sym_load IDs"):
        validate_lv_grid_data(valid_grid_data, [16, 20], active, reactive, ev)


def test_insufficient_ev_profiles(valid_grid_data, valid_profiles):
    active, reactive, ev = valid_profiles
    ev = ev.drop(columns=[3])  # Leave only 3 EV profiles for 4 loads
    with pytest.raises(ProfileMismatchError, match="Insufficient EV charging profiles"):
        validate_lv_grid_data(valid_grid_data, [16, 20], active, reactive, ev)


def test_invalid_pgm_data(valid_grid_data, valid_profiles):
    # Set negative voltage to purposely fail PGM schema validation
    valid_grid_data[ComponentType.node]["u_rated"][0] = -10.0
    with pytest.raises(ValidationException):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)


def test_missing_source(valid_grid_data, valid_profiles):
    valid_grid_data.pop(ComponentType.source)
    with pytest.raises(ComponentCountError, match="exactly one source"):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)


def test_multiple_transformers(valid_grid_data, valid_profiles):
    from power_grid_model import DatasetType, initialize_array

    extra_tf = initialize_array(DatasetType.input, ComponentType.transformer, 2)
    extra_tf[0] = valid_grid_data[ComponentType.transformer][0]
    extra_tf[1] = valid_grid_data[ComponentType.transformer][0]
    extra_tf[1]["id"] = 99
    valid_grid_data[ComponentType.transformer] = extra_tf
    with pytest.raises(ComponentCountError, match="exactly one transformer"):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)


def test_mismatching_ev_timestamps(valid_grid_data, valid_profiles):
    active, reactive, ev = valid_profiles
    ev.index = ev.index + pd.Timedelta(hours=1)
    with pytest.raises(ProfileMismatchError, match="mismatching timestamps"):
        validate_lv_grid_data(valid_grid_data, [16, 20], active, reactive, ev)


def test_transformer_disconnected_causes_topology_error(valid_grid_data, valid_profiles):
    valid_grid_data[ComponentType.transformer]["from_status"][0] = 0
    with pytest.raises(TopologyError, match="not fully connected"):
        validate_lv_grid_data(valid_grid_data, [16, 20], *valid_profiles)
