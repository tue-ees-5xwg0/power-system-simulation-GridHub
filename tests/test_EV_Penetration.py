"""Tests for EV penetration level assignment and time-series power flow."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from power_grid_model._core.serialization import json_deserialize

from power_system_simulation.EV_Penetration import (
    InvalidPenetrationLevelError,
    assign_ev_penetration,
    map_houses_per_feeder,
)
from power_system_simulation.grid_model import ProfileMismatchError


@pytest.fixture
def valid_grid_data():
    """Load and deserialise the LV grid from the shared JSON test fixture."""
    json_path = Path(__file__).parent / "lv_validation_test_data.json"
    return json_deserialize(json_path.read_text())


@pytest.fixture
def valid_profiles():
    """Flat load and EV profiles for the 4 sym_loads (12, 13, 14, 15) in the fixture."""
    ts = pd.date_range("2024-01-01", periods=4, freq="h")
    active = pd.DataFrame(
        {12: [1000.0] * 4, 13: [1000.0] * 4, 14: [1000.0] * 4, 15: [1000.0] * 4},
        index=ts,
    )
    reactive = pd.DataFrame(
        {12: [200.0] * 4, 13: [200.0] * 4, 14: [200.0] * 4, 15: [200.0] * 4},
        index=ts,
    )
    # 6 EV profiles — always more than the 4 sym_loads; column i draws 500*(i+1) W
    ev = pd.DataFrame(
        {i: np.full(4, 500.0 * (i + 1)) for i in range(6)},
        index=ts,
    )
    return active, reactive, ev


FEEDER_IDS = [16, 20]


def test_feeder_mapping_assigns_correct_loads(valid_grid_data):
    """Feeder 16 serves loads 12 and 13; feeder 20 serves loads 14 and 15."""
    mapping = map_houses_per_feeder(valid_grid_data, FEEDER_IDS)

    # set() because graph traversal order is not guaranteed
    assert set(mapping[16]) == {12, 13}
    assert set(mapping[20]) == {14, 15}


def test_feeder_mapping_single_feeder_subset(valid_grid_data):
    """Querying only feeder 16 must return only that feeder's loads."""
    mapping = map_houses_per_feeder(valid_grid_data, [16])

    assert list(mapping.keys()) == [16]
    assert set(mapping[16]) == {12, 13}


def test_feeder_mapping_ring_closer_excluded(valid_grid_data):
    """Disabled ring-closer line_24 must not cause loads to appear in both feeders."""
    mapping = map_houses_per_feeder(valid_grid_data, FEEDER_IDS)

    all_loads = [load for loads in mapping.values() for load in loads]
    # No load may appear in more than one feeder
    assert len(all_loads) == len(set(all_loads)), "A load appeared in multiple feeders"


def test_penetration_above_one_rejection(valid_grid_data, valid_profiles):
    """Penetration level above 1.0 must raise InvalidPenetrationLevelError."""
    with pytest.raises(InvalidPenetrationLevelError):
        assign_ev_penetration(valid_grid_data, FEEDER_IDS, *valid_profiles, penetration_level=1.5)


def test_negative_penetration_rejection(valid_grid_data, valid_profiles):
    """Negative penetration level must raise InvalidPenetrationLevelError."""
    with pytest.raises(InvalidPenetrationLevelError):
        assign_ev_penetration(valid_grid_data, FEEDER_IDS, *valid_profiles, penetration_level=-0.5)


def test_too_few_ev_profiles(valid_grid_data, valid_profiles):
    """A pool with fewer columns than sym_loads must raise ProfileMismatchError."""
    active, reactive, ev = valid_profiles
    ev = ev.drop(columns=[5])  # reduce from 6 to 5 — still more than 4, so drop to 3
    ev = ev.drop(columns=[4])
    ev = ev.drop(columns=[3])  # now 3 profiles for 4 sym_loads

    with pytest.raises(ProfileMismatchError):
        assign_ev_penetration(valid_grid_data, FEEDER_IDS, active, reactive, ev, penetration_level=0.5)


def test_mismatched_ev_timestamps(valid_grid_data, valid_profiles):
    """EV pool with shifted timestamps must raise ProfileMismatchError."""
    active, reactive, ev = valid_profiles
    ev.index = ev.index + pd.Timedelta(weeks=1)

    with pytest.raises(ProfileMismatchError):
        assign_ev_penetration(valid_grid_data, FEEDER_IDS, active, reactive, ev, penetration_level=0.5)


def test_output_has_correct_columns_and_index(valid_grid_data, valid_profiles):
    """Both aggregation tables must match the Assignment 2 output schema."""
    voltage_df, line_stats = assign_ev_penetration(
        valid_grid_data, FEEDER_IDS, *valid_profiles, penetration_level=1.0, random_seed=0
    )

    assert voltage_df.index.name == "Timestamp"
    assert line_stats.index.name == "Line_ID"

    assert list(voltage_df.columns) == [
        "Max_Voltage",
        "Max_Voltage_Node",
        "Min_Voltage",
        "Min_Voltage_Node",
    ]
    assert list(line_stats.columns) == [
        "Total_Loss",
        "Max_Loading",
        "Max_Loading_Timestamp",
        "Min_Loading",
        "Min_Loading_Timestamp",
    ]
    assert len(voltage_df) == 4
    assert not line_stats.empty


def test_zero_penetration_produces_valid_output(valid_grid_data, valid_profiles):
    """Penetration level 0 must still run the power flow and return non-empty tables."""
    voltage_df, line_stats = assign_ev_penetration(
        valid_grid_data, FEEDER_IDS, *valid_profiles, penetration_level=0.0, random_seed=0
    )

    assert not voltage_df.empty
    assert not line_stats.empty


def test_higher_penetration_does_not_reduce_line_loading(valid_grid_data, valid_profiles):
    """Adding EVs to the grid can only maintain or increase the maximum line loading."""
    active, reactive, ev = valid_profiles

    _, base = assign_ev_penetration(
        valid_grid_data, FEEDER_IDS, active, reactive, ev, penetration_level=0.0, random_seed=0
    )
    _, full = assign_ev_penetration(
        valid_grid_data, FEEDER_IDS, active, reactive, ev, penetration_level=1.0, random_seed=0
    )

    # >= because a very small EV contribution may not change loading beyond float precision
    assert full["Max_Loading"].max() >= base["Max_Loading"].max()


def test_higher_penetration_increases_energy_loss(valid_grid_data, valid_profiles):
    """Total resistive losses must be strictly higher at full EV penetration than at zero."""
    active, reactive, ev = valid_profiles

    _, base = assign_ev_penetration(
        valid_grid_data, FEEDER_IDS, active, reactive, ev, penetration_level=0.0, random_seed=0
    )
    _, full = assign_ev_penetration(
        valid_grid_data, FEEDER_IDS, active, reactive, ev, penetration_level=1.0, random_seed=0
    )

    # Strictly > because I2R losses grow with any increase in current
    assert full["Total_Loss"].sum() > base["Total_Loss"].sum()


def test_fixed_seed_gives_identical_results(valid_grid_data, valid_profiles):
    """Calling the function twice with the same seed must return bitwise-equal DataFrames."""
    active, reactive, ev = valid_profiles
    shared_args = {
        "input_data": valid_grid_data,
        "feeder_ids": FEEDER_IDS,
        "active_load_profile": active,
        "reactive_load_profile": reactive,
        "ev_active_profile": ev,
        "penetration_level": 1.0,
        "random_seed": 42,
    }

    voltage_df1, line_stats1 = assign_ev_penetration(**shared_args)
    voltage_df2, line_stats2 = assign_ev_penetration(**shared_args)

    pd.testing.assert_frame_equal(voltage_df1, voltage_df2)
    pd.testing.assert_frame_equal(line_stats1, line_stats2)


def test_input_profile_is_not_modified(valid_grid_data, valid_profiles):
    """The caller's active profile DataFrame must be identical before and after the call."""
    active, reactive, ev = valid_profiles
    p_snapshot = active.copy()  # frozen reference — compared against active after the call

    assign_ev_penetration(valid_grid_data, FEEDER_IDS, active, reactive, ev, penetration_level=1.0, random_seed=0)

    pd.testing.assert_frame_equal(active, p_snapshot)
