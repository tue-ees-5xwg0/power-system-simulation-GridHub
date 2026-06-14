"""
This module contains the implementation of the EV penetration level function
as described in Assignment 3.
Randomly assigns EV charging profiles to houses based on a user-specified
penetration level, runs a time-series power flow, and returns the standard
voltage and line aggregation tables from Assignment 2.
"""

import numpy as np
import pandas as pd
from power_grid_model import ComponentType

from power_system_simulation.graph_processing import GraphProcessor
from power_system_simulation.grid_model import (
    aggregate_line_results,
    aggregate_voltage_results,
    construct_model,
    create_batch_update,
    run_power_flow,
)
from power_system_simulation.lv_validation import validate_lv_grid_data


class InvalidPenetrationLevelError(ValueError):
    """Raised when penetration_level is outside [0, 1]."""


def build_graph(input_data: dict) -> GraphProcessor:
    """Construct a GraphProcessor from a PGM input dataset.

    Includes the MV/LV transformer and all lines as edges so the
    GraphProcessor models the full grid topology from the MV source node
    down through the transformer to the LV feeders.

    The MV-side (from_node) of the transformer is used as the source vertex,
    making downstream direction calculations relative to the grid root.

    Args:
        input_data: PGM input dataset dict with NumPy structured arrays.

    Returns:
        A fully validated GraphProcessor instance.

    Raises:
        GraphNotFullyConnectedError: if the enabled edges do not span all nodes.
        GraphCycleError: if the enabled topology contains a cycle.
    """
    nodes = input_data[ComponentType.node]
    lines = input_data[ComponentType.line]
    transformer = input_data[ComponentType.transformer][0]
    vertex_ids = [int(n) for n in nodes["id"]]
    edge_ids = [int(transformer["id"])]
    edge_vertex_id_pairs: list[tuple[int, int]]
    edge_vertex_id_pairs = [(int(transformer["from_node"]), int(transformer["to_node"]))]
    edge_enabled: list[bool]
    edge_enabled = [bool(transformer["from_status"] and transformer["to_status"])]

    edge_ids += [int(i) for i in lines["id"]]

    edge_vertex_id_pairs += [(int(fn), int(tn)) for fn, tn in zip(lines["from_node"], lines["to_node"], strict=False)]

    edge_enabled += [
        bool(int(fs) == 1 and int(ts) == 1) for fs, ts in zip(lines["from_status"], lines["to_status"], strict=False)
    ]

    return GraphProcessor(
        vertex_ids=vertex_ids,
        edge_ids=edge_ids,
        edge_vertex_id_pairs=edge_vertex_id_pairs,
        edge_enabled=edge_enabled,
        source_vertex_id=int(transformer["from_node"]),
    )


def map_houses_per_feeder(
    input_data: dict,
    feeder_ids: list[int],
) -> dict[int, list[int]]:
    """Return a mapping from feeder line ID to the sym_load IDs downstream of it.

    Uses the grid graph to find all nodes reachable from each feeder root,
    then collects the sym_loads whose node is in that downstream set.

    Args:
        input_data: PGM input dataset dict.
        feeder_ids: Line IDs that form the root of each LV feeder.

    Returns:
        Dict mapping each feeder line ID to a list of downstream sym_load IDs.
        Feeders with no downstream loads map to an empty list.
    """
    graph_processor = build_graph(input_data)

    load_ids = input_data[ComponentType.sym_load]["id"].astype(int)
    load_nodes = input_data[ComponentType.sym_load]["node"].astype(int)

    feeder_loads: dict[int, list[int]] = {}

    for feeder_id in map(int, feeder_ids):
        downstream_nodes = set(graph_processor.find_downstream_vertices(feeder_id))

        feeder_loads[feeder_id] = [
            int(lid) for lid, nid in zip(load_ids, load_nodes, strict=False) if nid in downstream_nodes
        ]

    return feeder_loads


def assign_ev_penetration(
    input_data: dict,
    feeder_ids: list[int],
    active_load_profile: pd.DataFrame,
    reactive_load_profile: pd.DataFrame,
    ev_active_profile: pd.DataFrame,
    penetration_level: float,
    random_seed: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assign EV charging profiles to houses and run a time-series power flow.

    The number of EVs per feeder is:
        n_ev_per_feeder = floor(penetration_level * total_houses / n_feeders)

    Within each feeder, houses are randomly selected without replacement.
    Each selected house receives a unique EV profile drawn without replacement
    from the pool. EV active power is added to the existing household load;
    reactive power is unchanged (EVs are modelled as unity power factor).

    If a feeder has fewer houses than the per-feeder target, the selection
    is clamped to the number of available houses in that feeder.

    Args:
        input_data:            PGM input dataset (NumPy structured arrays).
        feeder_ids:            Line IDs forming the root of each LV feeder.
        active_load_profile:   DataFrame (timestamps x sym_load IDs) in W.
        reactive_load_profile: DataFrame (timestamps x sym_load IDs) in var.
        ev_active_profile:     DataFrame (timestamps x profile index) in W.
                               Must have at least as many columns as sym_loads.
        penetration_level:     Fraction [0, 1] of houses to receive an EV.
        random_seed:           Optional seed for reproducible house and profile selection.

    Returns:
        (voltage_df, line_df) — the two standard aggregation tables from Assignment 2.

    Raises:
        InvalidPenetrationLevelError: penetration_level outside [0, 1].
        NotEnoughEVProfilesError:     Fewer EV profiles than sym_loads.
        EVTimestampMismatchError:     EV profile timestamps differ from load timestamps.
        ProfileMismatchError:         Timestamp or load ID mismatch in load profiles.
        InvalidFeederError:           Feeder IDs invalid or not on transformer LV bus.
        ComponentCountError:          Grid does not have exactly one transformer/source.
        TopologyError:                Grid is disconnected or contains cycles.
    """
    if not 0.0 <= penetration_level <= 1.0:
        raise InvalidPenetrationLevelError(f"Penetration_level must be between 0 and 1, got {penetration_level}.")

    validate_lv_grid_data(
        input_data,
        feeder_ids,
        active_load_profile,
        reactive_load_profile,
        ev_active_profile,
    )

    feeder_loads = map_houses_per_feeder(input_data, feeder_ids)

    # floor() via int() is fine here because penetration_level and counts are non-negative
    feeder_evs = int(penetration_level * len(active_load_profile.columns) / len(feeder_ids))

    randomise = np.random.default_rng(random_seed)

    house_selection: list[int] = []
    for loads in feeder_loads.values():
        if (num_selected := min(feeder_evs, len(loads))) > 0:
            house_selection += randomise.choice(loads, size=num_selected, replace=False).tolist()

    ev_columns = randomise.choice(ev_active_profile.columns, size=len(house_selection), replace=False)

    modified_active = active_load_profile.copy()
    modified_active[house_selection] += ev_active_profile[ev_columns].to_numpy()

    model = construct_model(input_data)
    update_data, timestamps = create_batch_update(modified_active, reactive_load_profile)
    output_data = run_power_flow(model, input_data, update_data)

    return (
        aggregate_voltage_results(output_data, timestamps),
        aggregate_line_results(output_data, timestamps),
    )
