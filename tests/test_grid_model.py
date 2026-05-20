"""Tests for the power grid simulation module."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from power_grid_model import ComponentType, DatasetType, LoadGenType, initialize_array
from power_grid_model.utils import json_serialize
from power_grid_model.validation import ValidationException

from power_system_simulation.grid_model import (
    ProfileMismatchError,
    aggregate_line_results,
    aggregate_voltage_results,
    construct_model,
    create_batch_update,
    load_input_data,
    run_power_flow,
)


def _make_small_grid_input() -> dict:
    """Create a minimal valid PGM input dataset.

    Network:
        node_1 (10.5kV) --- line_3 --- node_2 (10.5kV)
          |
        source_4
                                        sym_load_5 on node_2
                                        sym_load_6 on node_2
    """
    node = initialize_array(DatasetType.input, ComponentType.node, 2)
    node["id"] = [1, 2]
    node["u_rated"] = [10.5e3, 10.5e3]

    line = initialize_array(DatasetType.input, ComponentType.line, 1)
    line["id"] = [3]
    line["from_node"] = [1]
    line["to_node"] = [2]
    line["from_status"] = [1]
    line["to_status"] = [1]
    line["r1"] = [0.25]
    line["x1"] = [0.2]
    line["c1"] = [10e-6]
    line["tan1"] = [0.0]
    line["i_n"] = [1000]

    source = initialize_array(DatasetType.input, ComponentType.source, 1)
    source["id"] = [4]
    source["node"] = [1]
    source["status"] = [1]
    source["u_ref"] = [1.0]

    sym_load = initialize_array(DatasetType.input, ComponentType.sym_load, 2)
    sym_load["id"] = [5, 6]
    sym_load["node"] = [2, 2]
    sym_load["status"] = [1, 1]
    sym_load["type"] = [LoadGenType.const_power, LoadGenType.const_power]
    sym_load["p_specified"] = [1e6, 0.5e6]
    sym_load["q_specified"] = [0.2e6, 0.1e6]

    return {
        ComponentType.node: node,
        ComponentType.line: line,
        ComponentType.source: source,
        ComponentType.sym_load: sym_load,
    }


def _make_profiles(n_timestamps: int = 4) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """Create matching active/reactive load profiles for the small grid.

    Returns (active_profile, reactive_profile, timestamps)
    """
    timestamps = pd.date_range("2024-01-01", periods=n_timestamps, freq="h")
    load_ids = [5, 6]

    p_values = np.array(
        [
            [1.0e6, 0.5e6],
            [1.2e6, 0.6e6],
            [0.8e6, 0.4e6],
            [1.1e6, 0.55e6],
        ]
    )
    q_values = np.array(
        [
            [0.2e6, 0.1e6],
            [0.24e6, 0.12e6],
            [0.16e6, 0.08e6],
            [0.22e6, 0.11e6],
        ]
    )

    active_profile = pd.DataFrame(p_values, index=timestamps, columns=load_ids)
    reactive_profile = pd.DataFrame(q_values, index=timestamps, columns=load_ids)
    return active_profile, reactive_profile, timestamps.to_numpy()


# ── Tests for load_input_data ──


def test_load_input_data():
    """Test loading a PGM JSON file into a dict of numpy arrays."""
    input_data = _make_small_grid_input()
    json_str = json_serialize(input_data)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_str)
        tmp_path = f.name

    loaded = load_input_data(tmp_path)
    assert ComponentType.node in loaded
    assert ComponentType.line in loaded
    assert ComponentType.sym_load in loaded
    assert len(loaded[ComponentType.node]) == 2
    Path(tmp_path).unlink()


# ── Tests for construct_model ──


def test_construct_model_valid():
    """Test that a valid input produces a PowerGridModel."""
    input_data = _make_small_grid_input()
    model = construct_model(input_data)
    assert model is not None


def test_construct_model_invalid_raises():
    """Test that invalid input data raises ValidationException."""
    input_data = _make_small_grid_input()
    # Set an invalid rated voltage (0 or negative)
    input_data[ComponentType.node]["u_rated"] = [0.0, 10.5e3]
    with pytest.raises(ValidationException):
        construct_model(input_data)


# ── Tests for create_batch_update ──


def test_create_batch_update_valid():
    """Test creating a batch update from matching profiles."""
    active_profile, reactive_profile, timestamps = _make_profiles()
    update_data, ts = create_batch_update(active_profile, reactive_profile)

    assert ComponentType.sym_load in update_data
    sym_load_update = update_data[ComponentType.sym_load]
    assert sym_load_update.shape == (4, 2)
    np.testing.assert_array_equal(ts, timestamps)


def test_create_batch_update_mismatching_timestamps():
    """Test that mismatching timestamps raise ProfileMismatchError."""
    active_profile, reactive_profile, _ = _make_profiles()
    # Shift reactive timestamps by 1 hour
    reactive_profile.index = reactive_profile.index + pd.Timedelta(hours=1)
    with pytest.raises(ProfileMismatchError, match="timestamps"):
        create_batch_update(active_profile, reactive_profile)


def test_create_batch_update_mismatching_load_ids():
    """Test that mismatching load IDs raise ProfileMismatchError."""
    active_profile, reactive_profile, _ = _make_profiles()
    # Rename a column in reactive profile
    reactive_profile.columns = [5, 99]
    with pytest.raises(ProfileMismatchError, match="load IDs"):
        create_batch_update(active_profile, reactive_profile)


# ── Tests for run_power_flow ──


def test_run_power_flow_valid():
    """Test batch power flow on valid data returns results."""
    input_data = _make_small_grid_input()
    model = construct_model(input_data)
    active_profile, reactive_profile, _ = _make_profiles()
    update_data, _ = create_batch_update(active_profile, reactive_profile)

    output = run_power_flow(model, input_data, update_data)
    assert ComponentType.node in output
    assert ComponentType.line in output
    # Should have 4 batches
    assert output[ComponentType.node]["u_pu"].shape[0] == 4


def test_run_power_flow_invalid_batch_raises():
    """Test that an invalid batch dataset raises ValidationException."""
    input_data = _make_small_grid_input()
    model = construct_model(input_data)
    active_profile, reactive_profile, _ = _make_profiles()
    update_data, _ = create_batch_update(active_profile, reactive_profile)
    # Corrupt the update by setting a non-existent load ID
    update_data[ComponentType.sym_load][0]["id"][0] = 9999
    with pytest.raises(ValidationException):
        run_power_flow(model, input_data, update_data)


# ── Tests for aggregate_voltage_results ──


def test_aggregate_voltage_results():
    """Test that voltage aggregation returns correct structure and values."""
    input_data = _make_small_grid_input()
    model = construct_model(input_data)
    active_profile, reactive_profile, timestamps = _make_profiles()
    update_data, ts = create_batch_update(active_profile, reactive_profile)
    output = run_power_flow(model, input_data, update_data)

    voltage_df = aggregate_voltage_results(output, ts)

    assert len(voltage_df) == 4
    assert voltage_df.index.name == "Timestamp"
    assert "Max_Voltage" in voltage_df.columns
    assert "Max_Voltage_Node" in voltage_df.columns
    assert "Min_Voltage" in voltage_df.columns
    assert "Min_Voltage_Node" in voltage_df.columns

    # Source node (id=1) should always have max voltage (closest to reference)
    assert (voltage_df["Max_Voltage_Node"] == 1).all()
    # Load node (id=2) should always have min voltage (voltage drop due to load)
    assert (voltage_df["Min_Voltage_Node"] == 2).all()
    # Max should be >= min
    assert (voltage_df["Max_Voltage"].values >= voltage_df["Min_Voltage"].values).all()


# ── Tests for aggregate_line_results ──


def test_aggregate_line_results():
    """Test that line aggregation returns correct structure and values."""
    input_data = _make_small_grid_input()
    model = construct_model(input_data)
    active_profile, reactive_profile, timestamps = _make_profiles()
    update_data, ts = create_batch_update(active_profile, reactive_profile)
    output = run_power_flow(model, input_data, update_data)

    line_df = aggregate_line_results(output, ts)

    assert len(line_df) == 1  # one line in the grid
    assert line_df.index.name == "Line_ID"
    assert 3 in line_df.index  # line id is 3
    assert "Total_Loss" in line_df.columns
    assert "Max_Loading" in line_df.columns
    assert "Max_Loading_Timestamp" in line_df.columns
    assert "Min_Loading" in line_df.columns
    assert "Min_Loading_Timestamp" in line_df.columns

    # Energy loss should be positive
    assert line_df.loc[3, "Total_Loss"] > 0
    # Max loading >= min loading
    assert line_df.loc[3, "Max_Loading"] >= line_df.loc[3, "Min_Loading"]


def test_aggregate_line_results_trapezoidal():
    """Test that the trapezoidal rule is correctly applied for energy loss."""
    input_data = _make_small_grid_input()
    model = construct_model(input_data)

    # Use only 2 timestamps for easy manual verification
    timestamps = pd.date_range("2024-01-01", periods=2, freq="h")
    load_ids = [5, 6]

    active_profile = pd.DataFrame(
        [[1.0e6, 0.5e6], [1.0e6, 0.5e6]],
        index=timestamps,
        columns=load_ids,
    )
    reactive_profile = pd.DataFrame(
        [[0.2e6, 0.1e6], [0.2e6, 0.1e6]],
        index=timestamps,
        columns=load_ids,
    )

    update_data, ts = create_batch_update(active_profile, reactive_profile)
    output = run_power_flow(model, input_data, update_data)

    line_df = aggregate_line_results(output, ts)

    # With constant load, p_loss is the same at both timestamps
    # Trapezoidal integral over 1 hour = p_loss * 3600s
    # energy_kwh = p_loss * 3600 / 3.6e6 = p_loss / 1000
    p_from = output[ComponentType.line]["p_from"]
    p_to = output[ComponentType.line]["p_to"]
    expected_loss_w = p_from[0, 0] + p_to[0, 0]  # constant
    expected_kwh = expected_loss_w * 3600.0 / 3.6e6

    np.testing.assert_allclose(line_df.loc[3, "Total_Loss"], expected_kwh, rtol=1e-6)


# ── Integration test: full pipeline with provided test data ──


def test_full_pipeline():
    """End-to-end test: load data -> construct -> batch -> run -> aggregate."""
    input_data = _make_small_grid_input()

    # Serialize and reload via JSON
    json_str = json_serialize(input_data)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_str)
        tmp_path = f.name

    loaded = load_input_data(tmp_path)
    model = construct_model(loaded)

    active_profile, reactive_profile, timestamps = _make_profiles()
    update_data, ts = create_batch_update(active_profile, reactive_profile)
    output = run_power_flow(model, loaded, update_data)

    voltage_df = aggregate_voltage_results(output, ts)
    line_df = aggregate_line_results(output, ts)

    assert len(voltage_df) == 4
    assert len(line_df) == 1
    assert voltage_df.loc[voltage_df.index[0], "Max_Voltage"] > 0

    Path(tmp_path).unlink()
