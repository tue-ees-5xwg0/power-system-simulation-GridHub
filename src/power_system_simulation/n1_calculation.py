"""N-1 contingency analysis for LV grids.

Given a line failure, finds alternative reconnection topologies
(from currently disconnected lines) and runs time-series power flow
for each scenario, returning a summary of maximum loading.
"""

import copy

import numpy as np
import pandas as pd
from power_grid_model import ComponentType

from power_system_simulation.graph_processing import GraphProcessor
from power_system_simulation.grid_model import construct_model, create_batch_update, run_power_flow


class InvalidLineError(Exception):
    """Raised when the given ID is not a valid line ID."""


class LineNotConnectedError(Exception):
    """Raised when the given line is not connected at both sides in the base case."""


# Column names for the N-1 result table
N1_COLUMNS = ["Alternative_Line_ID", "Max_Loading", "Max_Loading_Line_ID", "Max_Loading_Timestamp"]


def _build_graph_processor(input_data: dict) -> GraphProcessor:
    """Build a GraphProcessor from PGM input data.

    Includes all nodes as vertices and all lines + the transformer as edges.
    Edge enabled status is True only when both from_status and to_status are 1.
    """
    nodes = input_data[ComponentType.node]
    lines = input_data[ComponentType.line]
    transformer = input_data[ComponentType.transformer]
    source = input_data[ComponentType.source]

    vertex_ids = [int(x) for x in nodes["id"]]

    edge_ids = [int(x) for x in lines["id"]] + [int(transformer["id"][0])]
    edge_vertex_id_pairs = [(int(fn), int(tn)) for fn, tn in zip(lines["from_node"], lines["to_node"], strict=True)] + [
        (int(transformer["from_node"][0]), int(transformer["to_node"][0]))
    ]
    edge_enabled = [
        bool(fs == 1 and ts == 1) for fs, ts in zip(lines["from_status"], lines["to_status"], strict=True)
    ] + [bool(transformer["from_status"][0] == 1 and transformer["to_status"][0] == 1)]

    source_vertex_id = int(source["node"][0])

    return GraphProcessor(
        vertex_ids=vertex_ids,
        edge_ids=edge_ids,
        edge_vertex_id_pairs=edge_vertex_id_pairs,
        edge_enabled=edge_enabled,
        source_vertex_id=source_vertex_id,
    )


def run_n1_analysis(
    input_data: dict,
    active_profile: pd.DataFrame,
    reactive_profile: pd.DataFrame,
    failed_line_id: int,
) -> pd.DataFrame:
    """Run N-1 contingency analysis for a single line failure.

    Disconnects the specified line, finds which currently-disconnected lines
    can restore full connectivity, and for each alternative runs a time-series
    power flow to determine the worst-case loading.

    Args:
        input_data: PGM input dataset dictionary.
        active_profile: DataFrame of active power per sym_load over time.
        reactive_profile: DataFrame of reactive power per sym_load over time.
        failed_line_id: ID of the line to take out of service.

    Returns:
        DataFrame with one row per alternative reconnection scenario.
        Columns: Alternative_Line_ID, Max_Loading, Max_Loading_Line_ID, Max_Loading_Timestamp.
        Empty (with correct columns) when no alternatives exist.

    Raises:
        InvalidLineError: If failed_line_id is not a valid line ID.
        LineNotConnectedError: If the line is not connected at both sides in the base case.
    """
    lines = input_data[ComponentType.line]
    line_ids = lines["id"]

    # Validate: must be a valid line ID
    if failed_line_id not in line_ids:
        raise InvalidLineError(f"Line ID {failed_line_id} is not a valid line.")

    # Validate: must be connected at both sides
    line_idx = int(np.where(line_ids == failed_line_id)[0][0])
    if lines["from_status"][line_idx] != 1 or lines["to_status"][line_idx] != 1:
        raise LineNotConnectedError(f"Line {failed_line_id} is not connected at both sides in the base case.")

    # Build graph and find alternative edges
    graph = _build_graph_processor(input_data)
    alternatives = graph.find_alternative_edges(failed_line_id)

    if not alternatives:
        return pd.DataFrame(columns=N1_COLUMNS)

    # Create batch update from load profiles (shared across all scenarios)
    update_data, timestamps = create_batch_update(active_profile, reactive_profile)

    rows = []
    for alt_line_id in alternatives:
        # Deep copy input data and modify line statuses
        modified_data = copy.deepcopy(input_data)
        mod_lines = modified_data[ComponentType.line]

        # Disconnect the failed line
        failed_idx = int(np.where(mod_lines["id"] == failed_line_id)[0][0])
        mod_lines["from_status"][failed_idx] = 0
        mod_lines["to_status"][failed_idx] = 0

        # Reconnect the alternative line (set to_status to 1; from_status is already 1)
        alt_idx = int(np.where(mod_lines["id"] == alt_line_id)[0][0])
        mod_lines["to_status"][alt_idx] = 1

        # Build model and run power flow
        model = construct_model(modified_data)
        output = run_power_flow(model, modified_data, update_data)

        # Extract max loading across all lines and all timestamps
        line_results = output[ComponentType.line]
        loading = line_results["loading"]  # (n_timestamps, n_lines)
        result_line_ids = line_results["id"][0]  # same across batches

        max_flat_idx = int(np.argmax(loading))
        max_ts_idx, max_line_col = np.unravel_index(max_flat_idx, loading.shape)

        rows.append(
            {
                "Alternative_Line_ID": int(alt_line_id),
                "Max_Loading": float(loading[max_ts_idx, max_line_col]),
                "Max_Loading_Line_ID": int(result_line_ids[max_line_col]),
                "Max_Loading_Timestamp": timestamps[max_ts_idx],
            }
        )

    return pd.DataFrame(rows, columns=N1_COLUMNS)
