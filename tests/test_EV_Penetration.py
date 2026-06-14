"""Tests for EV penetration level assignment and time-series power flow."""

import numpy as np
import pandas as pd
import pytest
from power_grid_model import ComponentType, DatasetType, LoadGenType, initialize_array

from power_system_simulation.EV_Penetration import (
    InvalidPenetrationLevelError,
    assign_ev_penetration,
    map_houses_per_feeder,
)
from power_system_simulation.grid_model import ProfileMismatchError


def _build_two_feeder_grid() -> dict:
    """Minimal LV grid: one transformer, two parallel feeders, one load each.

    Topology (enabled edges only):
        MV_node_1 --[transformer_2]--> LV_bus_3
                                           |
                              [line_30]         [line_31]
                                 |                  |
                              node_32            node_33
                                 |                  |
                              [line_34]          [line_35]
                                 |                  |
                              node_36            node_37
                            load_40             load_41

    line_50 is a disabled ring-closer between node_36 and node_37.
    """
    node = initialize_array(DatasetType.input, ComponentType.node, 6)
    node["id"] = [1, 3, 32, 33, 36, 37]
    node["u_rated"] = [10.5e3, 400.0, 400.0, 400.0, 400.0, 400.0]

    source = initialize_array(DatasetType.input, ComponentType.source, 1)
    source["id"] = [10]
    source["node"] = [1]
    source["status"] = [1]
    source["u_ref"] = [1.0]

    transformer = initialize_array(DatasetType.input, ComponentType.transformer, 1)
    transformer["id"] = [2]
    transformer["from_node"] = [1]
    transformer["to_node"] = [3]
    transformer["from_status"] = [1]
    transformer["to_status"] = [1]
    transformer["u1"] = [10.5e3]
    transformer["u2"] = [400.0]
    transformer["sn"] = [630e3]
    transformer["uk"] = [0.04]
    transformer["pk"] = [10e3]
    transformer["i0"] = [0.0]
    transformer["p0"] = [0.0]
    transformer["winding_from"] = [0]
    transformer["winding_to"] = [0]
    transformer["clock"] = [12]
    transformer["tap_side"] = [0]
    transformer["tap_pos"] = [0]
    transformer["tap_min"] = [-5]
    transformer["tap_max"] = [5]
    transformer["tap_nom"] = [0]
    transformer["tap_size"] = [625.0]

    line = initialize_array(DatasetType.input, ComponentType.line, 5)
    line["id"] = [30, 31, 34, 35, 50]
    line["from_node"] = [3, 3, 32, 33, 36]
    line["to_node"] = [32, 33, 36, 37, 37]
    line["from_status"] = [1, 1, 1, 1, 0]
    line["to_status"] = [1, 1, 1, 1, 0]
    line["r1"] = [0.25] * 5
    line["x1"] = [0.2] * 5
    line["c1"] = [10e-6] * 5
    line["tan1"] = [0.0] * 5
    line["i_n"] = [200.0] * 5

    sym_load = initialize_array(DatasetType.input, ComponentType.sym_load, 2)
    sym_load["id"] = [40, 41]
    sym_load["node"] = [36, 37]
    sym_load["status"] = [1, 1]
    sym_load["type"] = [LoadGenType.const_power] * 2
    sym_load["p_specified"] = [1e3, 1e3]
    sym_load["q_specified"] = [200.0, 200.0]

    return {
        ComponentType.node: node,
        ComponentType.source: source,
        ComponentType.transformer: transformer,
        ComponentType.line: line,
        ComponentType.sym_load: sym_load,
    }


def _build_load_profiles(n_ts: int = 4) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flat household load profiles for load_40 and load_41.

    Returns (active_W, reactive_var) — unpack with * when passing to assign_ev_penetration.
    """
    idx = pd.date_range("2024-01-01", periods=n_ts, freq="h")
    p = pd.DataFrame(np.full((n_ts, 2), 1000.0), index=idx, columns=[40, 41])
    q = pd.DataFrame(np.full((n_ts, 2), 200.0), index=idx, columns=[40, 41])
    return p, q


def _build_ev_pool(n_ts: int = 4, n_profiles: int = 4) -> pd.DataFrame:
    """EV charging pool with traceable per-column power values.

    Column i carries a constant 500*(i+1) W, so which profile was assigned
    to which house can be verified by inspecting the resulting load values.
    """
    idx = pd.date_range("2024-01-01", periods=n_ts, freq="h")
    cols = {i: np.full(n_ts, 500.0 * (i + 1)) for i in range(n_profiles)}
    return pd.DataFrame(cols, index=idx)


FEEDER_IDS = [30, 31]


def test_feeder_mapping_assigns_correct_loads():
    """map_houses_per_feeder must return {feeder_id: [downstream load IDs]}."""
    mapping = map_houses_per_feeder(_build_two_feeder_grid(), FEEDER_IDS)

    assert mapping[30] == [40]
    assert mapping[31] == [41]


def test_feeder_mapping_single_feeder_subset():
    """Querying a subset of feeders only returns results for those feeders."""
    mapping = map_houses_per_feeder(_build_two_feeder_grid(), [30])

    assert list(mapping.keys()) == [30]
    assert mapping[30] == [40]


def test_penetration_above_one_rejection():
    """Penetration level above 1.0 must raise InvalidPenetrationLevelError."""
    with pytest.raises(InvalidPenetrationLevelError):
        assign_ev_penetration(
            _build_two_feeder_grid(),
            FEEDER_IDS,
            *_build_load_profiles(),
            _build_ev_pool(),
            penetration_level=1.5,
        )


def test_negative_penetration_rejection():
    """Negative penetration level must raise InvalidPenetrationLevelError."""
    with pytest.raises(InvalidPenetrationLevelError):
        assign_ev_penetration(
            _build_two_feeder_grid(),
            FEEDER_IDS,
            *_build_load_profiles(),
            _build_ev_pool(),
            penetration_level=-0.5,
        )


def test_too_few_ev_profiles():
    """A pool with fewer columns than sym_loads must be rejected before the power flow."""
    with pytest.raises(ProfileMismatchError):
        assign_ev_penetration(
            _build_two_feeder_grid(),
            FEEDER_IDS,
            *_build_load_profiles(),
            _build_ev_pool(n_profiles=1),
            penetration_level=0.5,
        )


def test_mismatched_ev_timestamps():
    """EV pool with different timestamps than the load profiles must be rejected."""
    wrong_time = _build_ev_pool()
    wrong_time.index = wrong_time.index + pd.Timedelta(weeks=1)

    with pytest.raises(ProfileMismatchError):
        assign_ev_penetration(
            _build_two_feeder_grid(),
            FEEDER_IDS,
            *_build_load_profiles(),
            wrong_time,
            penetration_level=0.5,
        )


def test_output_has_correct_columns_and_index():
    """Both aggregation tables must match the Assignment 2 output schema."""
    voltage_df, line_stats = assign_ev_penetration(
        _build_two_feeder_grid(),
        FEEDER_IDS,
        *_build_load_profiles(),
        _build_ev_pool(),
        penetration_level=1.0,
        random_seed=0,
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


def test_zero_penetration_produces_valid_output():
    """Penetration level 0 must still run the power flow and return non-empty tables."""
    voltage_df, line_stats = assign_ev_penetration(
        _build_two_feeder_grid(),
        FEEDER_IDS,
        *_build_load_profiles(),
        _build_ev_pool(),
        penetration_level=0.0,
        random_seed=0,
    )

    assert not voltage_df.empty
    assert not line_stats.empty


def test_higher_penetration_does_not_reduce_line_loading():
    """Adding EVs to the grid can only maintain or increase the maximum line loading."""
    grid = _build_two_feeder_grid()
    p, q = _build_load_profiles()
    ev = _build_ev_pool()

    _, base = assign_ev_penetration(grid, FEEDER_IDS, p, q, ev, penetration_level=0.0, random_seed=0)
    _, full = assign_ev_penetration(grid, FEEDER_IDS, p, q, ev, penetration_level=1.0, random_seed=0)

    # >= because a very small EV contribution may not change loading beyond float precision
    assert full["Max_Loading"].max() >= base["Max_Loading"].max()


def test_higher_penetration_increases_energy_loss():
    """Total resistive losses must be strictly higher at full EV penetration than at zero."""
    grid = _build_two_feeder_grid()
    p, q = _build_load_profiles()
    ev = _build_ev_pool()

    _, base = assign_ev_penetration(grid, FEEDER_IDS, p, q, ev, penetration_level=0.0, random_seed=0)
    _, full = assign_ev_penetration(grid, FEEDER_IDS, p, q, ev, penetration_level=1.0, random_seed=0)

    # Strictly > because I2R losses grow with any increase in current
    assert full["Total_Loss"].sum() > base["Total_Loss"].sum()


def test_fixed_seed_gives_identical_results():
    """Calling the function twice with the same seed must return bitwise-equal DataFrames."""
    shared_args = {
        "input_data": _build_two_feeder_grid(),
        "feeder_ids": FEEDER_IDS,
        "active_load_profile": _build_load_profiles()[0],
        "reactive_load_profile": _build_load_profiles()[1],
        "ev_active_profile": _build_ev_pool(),
        "penetration_level": 1.0,
        "random_seed": 42,
    }

    voltage_df1, line_stats1 = assign_ev_penetration(**shared_args)
    voltage_df2, line_stats2 = assign_ev_penetration(**shared_args)

    pd.testing.assert_frame_equal(voltage_df1, voltage_df2)
    pd.testing.assert_frame_equal(line_stats1, line_stats2)


def test_input_profile_is_not_modified():
    """The caller's active profile DataFrame must be identical before and after the call."""
    p, q = _build_load_profiles()
    p_copy = p.copy()

    assign_ev_penetration(
        _build_two_feeder_grid(),
        FEEDER_IDS,
        p,
        q,
        _build_ev_pool(),
        penetration_level=1.0,
        random_seed=0,
    )

    pd.testing.assert_frame_equal(p, p_copy)
