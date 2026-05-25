"""
This module contains the implementation of assignment 1: Graph Processing.
The main class in the module is GraphProcessor, which processes a graph and provides two functions:
    1. find_downstream_vertices: Returns a list of all downstream vertices.
    2. find_alternative_edges: Returns a list of all alternative edges.
The GraphProcessor class makes use of the networkx package to help process the graph.
"""

import networkx as nx


class IDNotFoundError(Exception):
    pass


class InputLengthDoesNotMatchError(Exception):
    pass


class IDNotUniqueError(Exception):
    pass


class GraphNotFullyConnectedError(Exception):
    pass


class GraphCycleError(Exception):
    pass


class EdgeAlreadyDisabledError(Exception):
    pass


class GraphProcessor:
    """
    This class processes a graph and provides two functions:
    1. find_downstream_vertices: given an edge id, return all the vertices which
       are in the downstream of the edge, with respect to the source vertex.
       Returns a list of all downstream vertices.
    2. find_alternative_edges: given an enabled edge, if the edge is going
       to be disabled, which (currently disabled) edge can be enabled to ensure
       that the graph is again fully connected and acyclic?
       Returns a list of all alternative edges.
    """

    def __init__(
        self,
        vertex_ids: list[int],
        edge_ids: list[int],
        edge_vertex_id_pairs: list[tuple[int, int]],
        edge_enabled: list[bool],
        source_vertex_id: int,
    ) -> None:
        """
        Initialize a graph processor object with an undirected graph.
        Only the edges which are enabled are taken into account.
        Check if the input is valid and raise exceptions if not.
        The following conditions should be checked:
            1. vertex_ids and edge_ids should be unique. (IDNotUniqueError)
            2. edge_vertex_id_pairs should have the same length as edge_ids. (InputLengthDoesNotMatchError)
            3. edge_vertex_id_pairs should contain valid vertex ids. (IDNotFoundError)
            4. edge_enabled should have the same length as edge_ids. (InputLengthDoesNotMatchError)
            5. source_vertex_id should be a valid vertex id. (IDNotFoundError)
            6. The graph should be fully connected. (GraphNotFullyConnectedError)
            7. The graph should not contain cycles. (GraphCycleError)
        If one certain condition is not satisfied, the error in the parentheses should be raised.

        Args:
            vertex_ids: list of vertex ids
            edge_ids: list of edge ids
            edge_vertex_id_pairs: list of tuples of two integer
                Each tuple is a vertex id pair of the edge.
            edge_enabled: list of bools indicating of an edge is enabled or not
            source_vertex_id: vertex id of the source in the graph
        """
        # Run first 5 condition checks
        self._condition_1(vertex_ids, edge_ids)
        self._condition_2(edge_ids, edge_vertex_id_pairs)
        self._condition_3(vertex_ids, edge_vertex_id_pairs)
        self._condition_4(edge_ids, edge_enabled)
        self._condition_5(vertex_ids, source_vertex_id)


        # Initiate graph with only the enabled edges
        self.graph = nx.Graph()
        self.graph.add_nodes_from(vertex_ids)

        for (vertex1, vertex2), enabled in zip(edge_vertex_id_pairs, edge_enabled, strict=False):
            if enabled:
                self.graph.add_edge(vertex1, vertex2)

        # Run remaining condition checks
        self._condition_6()
        self._condition_7()

        # Create 'self' object
        self.edge_ids = edge_ids
        self.source_vertex_id = source_vertex_id
        self.edge_enabled = edge_enabled
        self.edge_vertex_id_pairs = edge_vertex_id_pairs

        # Create combined edge data to support find_alternative_edges function
        self.combined_edge_data = list(zip(edge_ids, edge_enabled, edge_vertex_id_pairs, strict=False))

    # Condition 1: vertex_ids and edge_ids should be unique
    def _condition_1(self, vertex_ids: list[int], edge_ids: list[int]) -> None:
        # Condition 1.1: verify vertex_ids are unique
        if len(set(vertex_ids)) != len(vertex_ids):
            raise IDNotUniqueError("Entries in vertex_ids are not unique.")

        # Condition 1.2: verify edge_ids are unique
        if len(set(edge_ids)) != len(edge_ids):
            raise IDNotUniqueError("Entries in edge_ids are not unique.")

    # Condition 2: edge_vertex_id_pairs should have the same length as edge_ids
    def _condition_2(self, edge_ids: list[int], edge_vertex_id_pairs: list[tuple[int, int]]) -> None:
        if len(edge_vertex_id_pairs) != len(edge_ids):
            raise InputLengthDoesNotMatchError("Both edge_vertex_id_pairs and edge_ids must have the same length.")

    # Condition 3: edge_vertex_id_pairs should contain valid vertex ids
    def _condition_3(self, vertex_ids: list[int],edge_vertex_id_pairs: list[tuple[int, int]]) -> None:
        for vertex_id_pair in edge_vertex_id_pairs:
            if not isinstance(vertex_id_pair, tuple) or len(vertex_id_pair) != 2:
                raise IDNotFoundError("Invalid entry in edge_vertex_id_pairs: each " \
                "entry must be a tuple of two vertex ids.")

            vertex_id_1, vertex_id_2 = vertex_id_pair

            if not isinstance(vertex_id_1, int) or not isinstance(vertex_id_2, int):
                raise IDNotFoundError("Invalid entry in edge_vertex_id_pairs: each vertex id must be an integer.")

            if vertex_id_1 not in vertex_ids or vertex_id_2 not in vertex_ids:
                raise IDNotFoundError("Invalid entry in edge_vertex_id_pairs: one or more vertex ids do not exist.")

    # Condition 4: edge_enabled should have the same length as edge_ids
    def _condition_4(self, edge_ids: list[int], edge_enabled: list[bool]) -> None:
        if len(edge_enabled) != len(edge_ids):
            raise InputLengthDoesNotMatchError("Both edge_enabled and edge_ids must have the same length.")

    # Condition 5: source_vertex_id should be a valid vertex id
    def _condition_5(self, vertex_ids: list[int], source_vertex_id: int) -> None:
        if not isinstance(source_vertex_id, int):
            raise IDNotFoundError("Invalid source_vertex_id: must be an integer.")

        if source_vertex_id not in vertex_ids:
            raise IDNotFoundError(f"Invalid source_vertex_id: vertex {source_vertex_id} does not exist.")

    # Condition 6: The graph should be fully connected
    def _condition_6(self) -> None:
        if not nx.is_connected(self.graph):
            raise GraphNotFullyConnectedError("The graph is not fully connected.")

    # Condition 7: The graph should not contain cycles
    def _condition_7(self) -> None:
        if not nx.is_tree(self.graph):
            raise GraphCycleError("The graph contains one or more cycles.")

    def find_downstream_vertices(self, edge_id: int) -> list[int]:
        """
        Given an edge id, return all the vertices which are in the downstream of the edge,
            with respect to the source vertex.
            Including the downstream vertex of the edge itself!

        Only enabled edges should be taken into account in the analysis.
        If the given edge_id is a disabled edge, it should return empty list.
        If the given edge_id does not exist, it should raise IDNotFoundError.


        For example, given the following graph (all edges enabled):

            vertex_0 (source) --edge_1-- vertex_2 --edge_3-- vertex_4

        Call find_downstream_vertices with edge_id=1 will return [2, 4]
        Call find_downstream_vertices with edge_id=3 will return [4]

        Args:
            edge_id: edge id to be searched

        Returns:
            A list of all downstream vertices.
        """
        # Check if the given edge_id exists
        if edge_id not in self.edge_ids:
            raise IDNotFoundError(f"Invalid edge_id: edge {edge_id} does not exist.")

        # Find index of given edge_id in edge_ids list
        edge_id_index = self.edge_ids.index(edge_id)

        # Check if the given edge_id is a disabled edge and if so return empty list
        if not self.edge_enabled[edge_id_index]:
            return []

        # Find the vertex id pair of the given edge_id
        vertex1, vertex2 = self.edge_vertex_id_pairs[edge_id_index]

        # Make copy of graph to avoid modifying original
        copied_graph = self.graph.copy()

        # Remove edge corresponding to given edge_id
        copied_graph.remove_edge(vertex1, vertex2)

        # Find connected components and return component that doesn't contain source vertex id as downstream vertices
        for component in nx.connected_components(copied_graph):
            if self.source_vertex_id not in component:
                return list(component)

    def find_alternative_edges(self, disabled_edge_id: int) -> list[int]:
        """
        Given an enabled edge, do the following analysis:
            If the edge is going to be disabled,
                which (currently disabled) edge can be enabled to ensure
                that the graph is again fully connected and acyclic?
            Return a list of all alternative edges.
        If the disabled_edge_id is not a valid edge id, it should raise IDNotFoundError.
        If the disabled_edge_id is already disabled, it should raise EdgeAlreadyDisabledError.
        If there are no alternative to make the graph fully connected again, it should return empty list.

        For example, given the following graph:

        vertex_0 (source) --edge_1(enabled)-- vertex_2 --edge_9(enabled)-- vertex_10
                 |                               |
                 |                           edge_7(disabled)
                 |                               |
                 -----------edge_3(enabled)-- vertex_4
                 |                               |
                 |                           edge_8(disabled)
                 |                               |
                 -----------edge_5(enabled)-- vertex_6

        Call find_alternative_edges with disabled_edge_id=1 will return [7]
        Call find_alternative_edges with disabled_edge_id=3 will return [7, 8]
        Call find_alternative_edges with disabled_edge_id=5 will return [8]
        Call find_alternative_edges with disabled_edge_id=9 will return []

        Args:
            disabled_edge_id: edge id (which is currently enabled) to be disabled

        Returns:
            A list of alternative edge ids.
        """
        # Check if disabled_edge_id is a valid edge id
        if disabled_edge_id not in self.edge_ids:
            raise IDNotFoundError(f"Invalid disabled_edge_id: edge {disabled_edge_id} does not exist.")

        # Check if disabled_edge_id is already disabled
        disabled_edge_index = self.edge_ids.index(disabled_edge_id)
        if not self.edge_enabled[disabled_edge_index]:
            raise EdgeAlreadyDisabledError(f"Edge {disabled_edge_id} is already disabled.")

        # Store disabled_edge_id vertex pair
        vertex1, vertex2 = self.edge_vertex_id_pairs[disabled_edge_index]

        # Find the component that contains vertex1 after disabling the edge
        self.graph.remove_edge(vertex1, vertex2)
        disabled_edge_component = nx.node_connected_component(self.graph, vertex1)
        self.graph.add_edge(vertex1, vertex2)

        # Return the disabled edge ids which connect a vertex in the component to a vertex outside the component
        return [
            edge_id
            for edge_id, enabled, (vertex_a, vertex_b) in self.combined_edge_data
            if not enabled and (vertex_a in disabled_edge_component) != (vertex_b in disabled_edge_component)
        ]
