import networkx as nx
import numpy as np
import pandas as pd
from power_grid_model import ComponentType
from power_grid_model.validation import assert_valid_input_data

from power_system_simulation.grid_model import ProfileMismatchError


class TopologyError(Exception):
    """Raised when the grid topology does not meet requirements."""


class InvalidFeederError(Exception):
    """Raised when the provided feeder IDs are invalid."""


class ComponentCountError(Exception):
    """Raised when the number of certain components is incorrect."""


def _validate_pgm_and_components(input_data: dict) -> None:
    """Checks PGM input validity and required components count."""
    assert_valid_input_data(input_data=input_data, calculation_type=None, symmetric=True)
    if len(input_data.get(ComponentType.transformer, [])) != 1:
        raise ComponentCountError("The LV grid must have exactly one transformer.")
    if len(input_data.get(ComponentType.source, [])) != 1:
        raise ComponentCountError("The LV grid must have exactly one source.")


def _validate_feeders(input_data: dict, lv_feeder_ids: list[int]) -> None:
    """Checks if feeder IDs are valid and connected to the transformer."""
    line_ids = input_data[ComponentType.line]["id"]
    tf_to_node = input_data[ComponentType.transformer]["to_node"][0]

    for f_id in lv_feeder_ids:
        if f_id not in line_ids:
            raise InvalidFeederError(f"Feeder ID {f_id} is not a valid line ID.")
        idx = np.where(line_ids == f_id)[0][0]
        if input_data[ComponentType.line]["from_node"][idx] != tf_to_node:
            raise InvalidFeederError(f"Feeder {f_id} 'from_node' does not match transformer 'to_node'.")


def _build_initial_graph(input_data: dict) -> nx.Graph:
    """Builds a NetworkX graph from active lines and transformers."""
    graph = nx.Graph()
    graph.add_nodes_from(input_data[ComponentType.node]["id"])

    for comp_type in [ComponentType.line, ComponentType.transformer]:
        comp_data = input_data.get(comp_type, [])
        for i in range(len(comp_data)):
            if comp_data["from_status"][i] == 1 and comp_data["to_status"][i] == 1:
                graph.add_edge(comp_data["from_node"][i], comp_data["to_node"][i])
    return graph


def _validate_topology(input_data: dict) -> None:
    """Checks if the grid is fully connected and acyclic."""
    graph = _build_initial_graph(input_data)
    if not nx.is_connected(graph):
        raise TopologyError("The grid is not fully connected in the initial state.")
    if not nx.is_tree(graph):
        raise TopologyError("The grid contains cycles in the initial state.")


def _validate_profile_matching(active: pd.DataFrame, reactive: pd.DataFrame, ev: pd.DataFrame) -> None:
    """Checks if timestamps and load IDs match across profiles."""
    if not active.index.equals(reactive.index) or not active.index.equals(ev.index):
        raise ProfileMismatchError("Profiles have mismatching timestamps.")
    if not active.columns.equals(reactive.columns):
        raise ProfileMismatchError("Active and reactive profiles have mismatching load IDs.")


def _validate_load_ids(input_data: dict, active_profile: pd.DataFrame, ev_profile: pd.DataFrame) -> None:
    """Checks if profile IDs exist in the grid and EV profiles are sufficient."""
    sym_load_ids = set(input_data[ComponentType.sym_load]["id"])
    if not set(active_profile.columns).issubset(sym_load_ids):
        raise ProfileMismatchError("Load profile IDs contain invalid sym_load IDs.")
    if len(ev_profile.columns) < len(sym_load_ids):
        raise ProfileMismatchError("Insufficient EV charging profiles for the given sym_loads.")


def validate_lv_grid_data(
    input_data: dict,
    lv_feeder_ids: list[int],
    active_profile: pd.DataFrame,
    reactive_profile: pd.DataFrame,
    ev_profile: pd.DataFrame,
) -> None:
    """Validates the input data for the LV grid analytics."""
    _validate_pgm_and_components(input_data)
    _validate_feeders(input_data, lv_feeder_ids)
    _validate_topology(input_data)
    _validate_profile_matching(active_profile, reactive_profile, ev_profile)
    _validate_load_ids(input_data, active_profile, ev_profile)
