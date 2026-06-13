"""Tests for the N-1 contingency analysis module."""

import copy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from power_grid_model import ComponentType
from power_grid_model.utils import json_deserialize

from power_system_simulation.grid_model import construct_model, create_batch_update, run_power_flow
from power_system_simulation.n1_calculation import (
    N1_COLUMNS,
    InvalidLineError,
    LineNotConnectedError,
    run_n1_analysis,
)

# ── Fixtures ──


@pytest.fixture
def grid_data():
    """Load the small test network (same topology as lv_validation_test_data.json).

    Topology:
        source_10 on node_0
        transformer_11: node_0 -> node_1

        Feeder 1 (line 16):
          line_16: 1->2, line_17: 2->3 (load 12), line_18: 2->4, line_19: 4->5 (load 13)

        Feeder 2 (line 20):
          line_20: 1->6, line_21: 6->7 (load 14), line_22: 6->8, line_23: 8->9 (load 15)

        Ring closure (disconnected):
          line_24: 4->8 (from_status=1, to_status=0)
    """
    json_path = Path(__file__).parent / "lv_validation_test_data.json"
    return json_deserialize(json_path.read_text())


@pytest.fixture
def profiles():
    """Create synthetic active/reactive load profiles for the 4 sym_loads (12, 13, 14, 15).

    Returns (active_profile, reactive_profile).
    3 timestamps at 1-hour intervals with varied load to produce non-trivial power flow.
    """
    timestamps = pd.date_range("2025-01-01", periods=3, freq="h")
    load_ids = [12, 13, 14, 15]

    p_values = np.array(
        [
            [2000.0, 3000.0, 2500.0, 1500.0],
            [4000.0, 5000.0, 3500.0, 2500.0],
            [3000.0, 4000.0, 3000.0, 2000.0],
        ]
    )
    q_values = np.array(
        [
            [200.0, 300.0, 250.0, 150.0],
            [400.0, 500.0, 350.0, 250.0],
            [300.0, 400.0, 300.0, 200.0],
        ]
    )

    active = pd.DataFrame(p_values, index=timestamps, columns=load_ids)
    reactive = pd.DataFrame(q_values, index=timestamps, columns=load_ids)
    return active, reactive


# ── Error handling tests ──


def test_n1_invalid_line_id(grid_data, profiles):
    """Non-existent line ID raises InvalidLineError."""
    active, reactive = profiles
    with pytest.raises(InvalidLineError, match="not a valid line"):
        run_n1_analysis(grid_data, active, reactive, failed_line_id=999)


def test_n1_transformer_id_raises(grid_data, profiles):
    """Passing the transformer ID (11) raises InvalidLineError because it is not a line."""
    active, reactive = profiles
    with pytest.raises(InvalidLineError, match="not a valid line"):
        run_n1_analysis(grid_data, active, reactive, failed_line_id=11)


def test_n1_source_id_raises(grid_data, profiles):
    """Passing the source ID (10) raises InvalidLineError."""
    active, reactive = profiles
    with pytest.raises(InvalidLineError, match="not a valid line"):
        run_n1_analysis(grid_data, active, reactive, failed_line_id=10)


def test_n1_line_not_connected(grid_data, profiles):
    """Line 24 (to_status=0) raises LineNotConnectedError."""
    active, reactive = profiles
    with pytest.raises(LineNotConnectedError, match="not connected at both sides"):
        run_n1_analysis(grid_data, active, reactive, failed_line_id=24)


def test_n1_line_from_status_zero_raises(grid_data, profiles):
    """A line with from_status=0 raises LineNotConnectedError."""
    active, reactive = profiles
    # Manually set line 17's from_status to 0
    grid_data[ComponentType.line]["from_status"][1] = 0  # line 17 is at index 1
    with pytest.raises(LineNotConnectedError, match="not connected at both sides"):
        run_n1_analysis(grid_data, active, reactive, failed_line_id=17)


# ── Empty result tests ──


def test_n1_no_alternative_returns_empty(grid_data, profiles):
    """Line 17 (2->3) has no alternative: node 3 is a leaf with no ring closure."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=17)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_n1_empty_table_has_correct_columns(grid_data, profiles):
    """Empty result table still has the correct column names."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=17)
    assert list(result.columns) == N1_COLUMNS


@pytest.mark.parametrize("line_id", [19, 21, 23])
def test_n1_leaf_lines_have_no_alternative(grid_data, profiles, line_id):
    """Lines ending at leaf nodes (19, 21, 23) have no alternative."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=line_id)
    assert len(result) == 0
    assert list(result.columns) == N1_COLUMNS


# ── Valid result tests ──


def test_n1_with_alternative_line_18(grid_data, profiles):
    """Failing line 18 (2->4) should produce one alternative: line 24."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=18)
    assert len(result) == 1
    assert result["Alternative_Line_ID"].iloc[0] == 24


@pytest.mark.parametrize("line_id", [16, 18, 20, 22])
def test_n1_ring_lines_have_alternative_24(grid_data, profiles, line_id):
    """All lines on the ring path (16, 18, 20, 22) have line 24 as the only alternative."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=line_id)
    assert len(result) == 1
    assert result["Alternative_Line_ID"].iloc[0] == 24


def test_n1_result_has_correct_columns(grid_data, profiles):
    """Result table has the expected column names."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=18)
    assert list(result.columns) == N1_COLUMNS


def test_n1_result_max_loading_positive(grid_data, profiles):
    """Max loading should be positive (loads are non-zero)."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=18)
    assert result["Max_Loading"].iloc[0] > 0


def test_n1_result_line_id_is_valid(grid_data, profiles):
    """The line ID with max loading must be a valid line in the grid."""
    active, reactive = profiles
    line_ids = set(grid_data[ComponentType.line]["id"])
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=18)
    assert result["Max_Loading_Line_ID"].iloc[0] in line_ids


def test_n1_result_timestamp_is_valid(grid_data, profiles):
    """The max loading timestamp must be one of the profile timestamps."""
    active, reactive = profiles
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=18)
    assert result["Max_Loading_Timestamp"].iloc[0] in active.index


# ── Cross-validation: verify result matches manual computation ──


def test_n1_result_matches_manual_power_flow(grid_data, profiles):
    """Cross-validate: manually run power flow for the same scenario and compare."""
    active, reactive = profiles

    # Scenario: fail line 18, reconnect line 24
    modified = copy.deepcopy(grid_data)
    mod_lines = modified[ComponentType.line]

    idx_18 = int(np.where(mod_lines["id"] == 18)[0][0])
    mod_lines["from_status"][idx_18] = 0
    mod_lines["to_status"][idx_18] = 0

    idx_24 = int(np.where(mod_lines["id"] == 24)[0][0])
    mod_lines["to_status"][idx_24] = 1

    model = construct_model(modified)
    update_data, timestamps = create_batch_update(active, reactive)
    output = run_power_flow(model, modified, update_data)

    # Compute expected max loading
    loading = output[ComponentType.line]["loading"]
    result_line_ids = output[ComponentType.line]["id"][0]
    max_flat = int(np.argmax(loading))
    exp_ts_idx, exp_line_col = np.unravel_index(max_flat, loading.shape)
    expected_loading = float(loading[exp_ts_idx, exp_line_col])
    expected_line_id = int(result_line_ids[exp_line_col])
    expected_timestamp = timestamps[exp_ts_idx]

    # Run N-1 analysis
    result = run_n1_analysis(grid_data, active, reactive, failed_line_id=18)

    assert result["Alternative_Line_ID"].iloc[0] == 24
    np.testing.assert_allclose(result["Max_Loading"].iloc[0], expected_loading, rtol=1e-10)
    assert result["Max_Loading_Line_ID"].iloc[0] == expected_line_id
    assert result["Max_Loading_Timestamp"].iloc[0] == expected_timestamp
