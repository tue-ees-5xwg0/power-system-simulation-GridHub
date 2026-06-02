"""
Power grid simulation module using power-grid-model as the calculation core.

Provides functionality to:
- Construct a PGM model from input data
- Create batch update datasets from load profiles
- Run time-series (batch) power flow calculations
- Aggregate results into voltage and line summary tables
"""

from pathlib import Path

import numpy as np
import pandas as pd
from power_grid_model import ComponentType, DatasetType, PowerGridModel, initialize_array
from power_grid_model.utils import json_deserialize
from power_grid_model.validation import assert_valid_batch_data, assert_valid_input_data


class ProfileMismatchError(Exception):
    """Raised when active and reactive load profiles have mismatching timestamps or load IDs."""


def load_input_data(json_path: str | Path) -> dict:
    """Load PGM input data from a JSON file.

    Args:
        json_path: Path to the PGM-format JSON file.

    Returns:
        Dictionary of numpy structured arrays (PGM input dataset).
    """
    json_path = Path(json_path)
    json_str = json_path.read_text()
    return json_deserialize(json_str)


def construct_model(input_data: dict) -> PowerGridModel:
    """Validate input data and construct a PowerGridModel.

    Args:
        input_data: PGM input dataset dictionary.

    Returns:
        A constructed PowerGridModel instance.

    Raises:
        ValidationException: If the input data is invalid.
    """
    assert_valid_input_data(input_data=input_data, calculation_type=None, symmetric=True)
    return PowerGridModel(input_data)


def create_batch_update(
    active_profile: pd.DataFrame,
    reactive_profile: pd.DataFrame,
) -> tuple[dict, np.ndarray]:
    """Create a PGM batch update dataset from active and reactive load profiles.

    Both DataFrames must have matching timestamps (index) and load IDs (columns).

    Args:
        active_profile: DataFrame with timestamps as index and load IDs as columns,
                        values are active power in W.
        reactive_profile: DataFrame with timestamps as index and load IDs as columns,
                          values are reactive power in var.

    Returns:
        A tuple of (update_data dict, timestamps array).

    Raises:
        ProfileMismatchError: If timestamps or load IDs do not match.
    """
    if not active_profile.index.equals(reactive_profile.index):
        raise ProfileMismatchError("Active and reactive profiles have mismatching timestamps.")

    if not (active_profile.columns == reactive_profile.columns).all():
        raise ProfileMismatchError("Active and reactive profiles have mismatching load IDs.")

    n_timestamps = len(active_profile)
    load_ids = active_profile.columns.to_numpy(dtype=np.int32)
    n_loads = len(load_ids)

    sym_load_update = initialize_array(DatasetType.update, ComponentType.sym_load, (n_timestamps, n_loads))
    for i in range(n_timestamps):
        sym_load_update[i]["id"] = load_ids
        sym_load_update[i]["p_specified"] = active_profile.iloc[i].to_numpy()
        sym_load_update[i]["q_specified"] = reactive_profile.iloc[i].to_numpy()

    update_data = {ComponentType.sym_load: sym_load_update}
    timestamps = active_profile.index.to_numpy()
    return update_data, timestamps


def run_power_flow(
    model: PowerGridModel,
    input_data: dict,
    update_data: dict,
) -> dict:
    """Validate batch data and run time-series power flow calculation.

    Args:
        model: A constructed PowerGridModel.
        input_data: The original PGM input dataset (needed for batch validation).
        update_data: The batch update dataset from create_batch_update.

    Returns:
        Output data dictionary with results per component type.

    Raises:
        ValidationException: If the batch dataset is invalid.
    """
    assert_valid_batch_data(
        input_data=input_data,
        update_data=update_data,
        calculation_type=None,
        symmetric=True,
    )
    return model.calculate_power_flow(update_data=update_data, symmetric=True)


def aggregate_voltage_results(output_data: dict, timestamps: np.ndarray) -> pd.DataFrame:
    """Aggregate node voltage results per timestamp.

    Args:
        output_data: Output from run_power_flow.
        timestamps: Array of timestamps corresponding to each batch.

    Returns:
        DataFrame indexed by Timestamp with columns:
        - Max_Voltage: maximum p.u. voltage across all nodes
        - Max_Voltage_Node: node ID with the maximum p.u. voltage
        - Min_Voltage: minimum p.u. voltage across all nodes
        - Min_Voltage_Node: node ID with the minimum p.u. voltage
    """
    node_results = output_data[ComponentType.node]
    # node_results shape: (n_timestamps, n_nodes)
    u_pu = node_results["u_pu"]  # (n_timestamps, n_nodes)
    node_ids = node_results["id"]  # (n_timestamps, n_nodes) -- same per batch

    max_idx = np.argmax(u_pu, axis=1)
    min_idx = np.argmin(u_pu, axis=1)
    n_timestamps = len(timestamps)

    rows = []
    for t in range(n_timestamps):
        rows.append(
            {
                "Max_Voltage": u_pu[t, max_idx[t]],
                "Max_Voltage_Node": node_ids[t, max_idx[t]],
                "Min_Voltage": u_pu[t, min_idx[t]],
                "Min_Voltage_Node": node_ids[t, min_idx[t]],
            }
        )

    df = pd.DataFrame(rows, index=pd.Index(timestamps, name="Timestamp"))
    df["Max_Voltage_Node"] = df["Max_Voltage_Node"].astype(np.int32)
    df["Min_Voltage_Node"] = df["Min_Voltage_Node"].astype(np.int32)
    return df


def aggregate_line_results(output_data: dict, timestamps: np.ndarray) -> pd.DataFrame:
    """Aggregate line results: energy loss (kWh) and loading extremes.

    Energy loss is computed using the trapezoidal rule on the total power loss
    (p_from + p_to) over the timeline. The result is converted to kWh.

    Args:
        output_data: Output from run_power_flow.
        timestamps: Array of timestamps corresponding to each batch.

    Returns:
        DataFrame indexed by Line_ID with columns:
        - Total_Loss: total energy loss over the timeline in kWh
        - Max_Loading: maximum loading in p.u. across the timeline
        - Max_Loading_Timestamp: timestamp of the maximum loading
        - Min_Loading: minimum loading in p.u. across the timeline
        - Min_Loading_Timestamp: timestamp of the minimum loading
    """
    line_results = output_data[ComponentType.line]
    # line_results shape: (n_timestamps, n_lines)
    p_from = line_results["p_from"]  # W
    p_to = line_results["p_to"]  # W
    loading = line_results["loading"]  # p.u.
    line_ids = line_results["id"][0]  # same across batches

    # Power loss per line per timestamp in W
    p_loss = p_from + p_to  # (n_timestamps, n_lines)

    # Time differences in seconds for trapezoidal rule
    ts = pd.to_datetime(timestamps)
    dt_seconds = np.diff(ts).astype("timedelta64[s]").astype(np.float64)  # (n_timestamps - 1,)

    # Trapezoidal integration: sum of (p_loss[i] + p_loss[i+1]) / 2 * dt[i] for each line
    # Result in Ws (joules), convert to kWh: / 3.6e6
    n_lines = len(line_ids)
    energy_loss_ws = np.zeros(n_lines)
    for i in range(len(dt_seconds)):
        energy_loss_ws += (p_loss[i] + p_loss[i + 1]) / 2.0 * dt_seconds[i]

    energy_loss_kwh = energy_loss_ws / 3.6e6

    # Loading extremes
    max_loading_idx = np.argmax(loading, axis=0)  # per line
    min_loading_idx = np.argmin(loading, axis=0)  # per line

    rows = []
    for j in range(n_lines):
        rows.append(
            {
                "Line_ID": int(line_ids[j]),
                "Total_Loss": energy_loss_kwh[j],
                "Max_Loading": loading[max_loading_idx[j], j],
                "Max_Loading_Timestamp": timestamps[max_loading_idx[j]],
                "Min_Loading": loading[min_loading_idx[j], j],
                "Min_Loading_Timestamp": timestamps[min_loading_idx[j]],
            }
        )

    df = pd.DataFrame(rows)
    df = df.set_index("Line_ID")
    df.index.name = "Line_ID"
    return df
