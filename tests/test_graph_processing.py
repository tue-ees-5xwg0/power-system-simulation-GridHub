import pytest

from power_system_simulation.graph_processing import (
    EdgeAlreadyDisabledError,
    GraphCycleError,
    GraphNotFullyConnectedError,
    GraphProcessor,
    IDNotFoundError,
    IDNotUniqueError,
    InputLengthDoesNotMatchError,
)


# Initialize a graph ficture to test find_downstream_vertices and find_alternative_edges function.
@pytest.fixture
def test_graph():
    """
    vertex_0 (source) --edge_1(enabled)-- vertex_2 --edge_9(enabled)-- vertex_10
                 |                               |
                 |                           edge_7(disabled)
                 |                               |
                 -----------edge_3(enabled)-- vertex_4
                 |                               |
                 |                           edge_8(disabled)
                 |                               |
                 -----------edge_5(enabled)-- vertex_6
    """
    return GraphProcessor(
        vertex_ids=[0, 2, 4, 6, 10],
        edge_ids=[1, 3, 5, 7, 8, 9],
        edge_vertex_id_pairs=[(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)],
        edge_enabled=[True, True, True, False, False, True],
        source_vertex_id=0,
    )


# Test condition 1.1: vertex_ids are not unique. (IDNotUniqueError)
def test_IDNotUniqueError_VertexIDs() -> None:
    with pytest.raises(IDNotUniqueError, match="Entries in vertex_ids are not unique."):
        GraphProcessor(
            vertex_ids=[0, 1, 1], edge_ids=[10], edge_vertex_id_pairs=[(0, 1)], edge_enabled=[True], source_vertex_id=0
        )


# Test condition 1.2: edge_ids are not unique. (IDNotUniqueError)
def test_IDNotUniqueError_EdgeIDs() -> None:
    with pytest.raises(IDNotUniqueError, match="Entries in edge_ids are not unique."):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10, 10],
            edge_vertex_id_pairs=[(0, 1), (1, 2)],
            edge_enabled=[True, True],
            source_vertex_id=0,
        )


# Test condition 2: edge_vertex_id_pairs is not the same length as edge_ids. (InputLengthDoesNotMatchError)
def test_InputLengthDoesNotMatchError_EdgeVertexPairsLengthMismatch() -> None:
    with pytest.raises(
        InputLengthDoesNotMatchError, match="Both edge_vertex_id_pairs and edge_ids must have the same length."
    ):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10, 11],
            edge_vertex_id_pairs=[(0, 1)],
            edge_enabled=[True, False],
            source_vertex_id=0,
        )


# Test condition 3.0: edge_vertex_id_pairs contains valid vertex ids. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_Correct() -> None:
    GraphProcessor(
        vertex_ids=[0, 1, 2],
        edge_ids=[10, 11],
        edge_vertex_id_pairs=[(0, 1), (1, 2)],
        edge_enabled=[True, True],
        source_vertex_id=0,
    )


# Test condition 3.1: edge_vertex_id_pairs does not contain tuples. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_NotTuple() -> None:
    with pytest.raises(
        IDNotFoundError, match="Invalid entry in edge_vertex_id_pairs: each entry must be a tuple of two vertex ids."
    ):
        GraphProcessor(
            vertex_ids=[0, 1, 2], edge_ids=[10], edge_vertex_id_pairs=[0], edge_enabled=[True], source_vertex_id=0
        )


# Test condition 3.2: edge_vertex_id_pairs does not contain tuples of length 2. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_WrongLength() -> None:
    with pytest.raises(
        IDNotFoundError, match="Invalid entry in edge_vertex_id_pairs: each entry must be a tuple of two vertex ids."
    ):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10],
            edge_vertex_id_pairs=[(0, 1, 2)],
            edge_enabled=[True],
            source_vertex_id=0,
        )


# Test condition 3.3: edge_vertex_id_pairs does not contain tuples of integers. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_NonInt1() -> None:
    with pytest.raises(
        IDNotFoundError, match="Invalid entry in edge_vertex_id_pairs: each vertex id must be an integer."
    ):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10],
            edge_vertex_id_pairs=[("1", 0)],
            edge_enabled=[True],
            source_vertex_id=0,
        )


# Test condition 3.4: edge_vertex_id_pairs does not contain tuples of integers. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_NonInt2() -> None:
    with pytest.raises(
        IDNotFoundError, match="Invalid entry in edge_vertex_id_pairs: each vertex id must be an integer."
    ):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10],
            edge_vertex_id_pairs=[(0, "1")],
            edge_enabled=[True],
            source_vertex_id=0,
        )


# Test condition 3.5: edge_vertex_id_pairs does not contain valid vertex ids. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_IdNotFound1() -> None:
    with pytest.raises(
        IDNotFoundError, match="Invalid entry in edge_vertex_id_pairs: one or more vertex ids do not exist."
    ):
        GraphProcessor(
            vertex_ids=[0, 1, 2], edge_ids=[10], edge_vertex_id_pairs=[(3, 0)], edge_enabled=[True], source_vertex_id=0
        )


# Test condition 3.6: edge_vertex_id_pairs does not contain valid vertex ids. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_IdNotFound2() -> None:
    with pytest.raises(
        IDNotFoundError, match="Invalid entry in edge_vertex_id_pairs: one or more vertex ids do not exist."
    ):
        GraphProcessor(
            vertex_ids=[0, 1, 2], edge_ids=[10], edge_vertex_id_pairs=[(0, 3)], edge_enabled=[True], source_vertex_id=0
        )


# Test condition 4: edge_enabled is not the same length as edge_ids. (InputLengthDoesNotMatchError)
def test_InputLengthDoesNotMatchError_EdgeEnabledLengthMismatch() -> None:
    with pytest.raises(InputLengthDoesNotMatchError, match="Both edge_enabled and edge_ids must have the same length."):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10, 11],
            edge_vertex_id_pairs=[(0, 1), (1, 2)],
            edge_enabled=[True],
            source_vertex_id=0,
        )


# Test condition 5.0: source_vertex_id is a valid vertex id. (IDNotFoundError)
def test_IDNotFoundError_SourceVertex_Correct() -> None:
    GraphProcessor(
        vertex_ids=[0, 1, 2],
        edge_ids=[10, 11],
        edge_vertex_id_pairs=[(0, 1), (1, 2)],
        edge_enabled=[True, True],
        source_vertex_id=1,
    )


# Test condition 5.1: source_vertex_id is not an integer. (IDNotFoundError)
def test_IDNotFoundError_SourceVertex_NonInt() -> None:
    with pytest.raises(IDNotFoundError, match="Invalid id: must be an integer."):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10],
            edge_vertex_id_pairs=[(0, 1)],
            edge_enabled=[True],
            source_vertex_id="0",
        )


# Test condition 5.2: source_vertex_id does not exist in vertex_ids. (IDNotFoundError)
def test_IDNotFoundError_SourceVertex_IdNotFound() -> None:
    with pytest.raises(IDNotFoundError, match="Invalid id: 3 does not exist."):
        GraphProcessor(
            vertex_ids=[0, 1, 2], edge_ids=[10], edge_vertex_id_pairs=[(0, 1)], edge_enabled=[True], source_vertex_id=3
        )


# Test condition 6: the graph is not fully connected. (GraphNotFullyConnectedError)
def test_GraphNotFullyConnectedError() -> None:
    with pytest.raises(GraphNotFullyConnectedError, match="The graph is not fully connected."):
        GraphProcessor(
            vertex_ids=[0, 1, 2], edge_ids=[10], edge_vertex_id_pairs=[(0, 1)], edge_enabled=[True], source_vertex_id=0
        )


# Test condition 7: the graph contains cycles. (GraphCycleError)
def test_GraphCycleError() -> None:
    with pytest.raises(GraphCycleError, match="The graph contains one or more cycles."):
        GraphProcessor(
            vertex_ids=[0, 1, 2],
            edge_ids=[10, 11, 12],
            edge_vertex_id_pairs=[(0, 1), (1, 2), (2, 0)],
            edge_enabled=[True, True, True],
            source_vertex_id=0,
        )


# **Testing for function: find_downstream_vertices**
# Test case 1: edge_id does not exist. (IDNotFoundError)
def test_IDNotFoundError_Edge_NotFound(test_graph) -> None:
    with pytest.raises(IDNotFoundError, match="Invalid id: 12 does not exist."):
        test_graph.find_downstream_vertices(12)


# Test case 2: edge_id is disabled return empty list.
def test_DisabledEdge_ReturnEmpty(test_graph):
    assert test_graph.find_downstream_vertices(7) == []


# Test case 3: edge_id is enabled return multiple downstream vertices (chain).
def test_Downstream_Edge1(test_graph):
    assert set(test_graph.find_downstream_vertices(1)) == {2, 10}


# Test case 4: edge_id is enabled return single downstream vertex.
def test_Downstream_Edge9(test_graph):
    assert test_graph.find_downstream_vertices(9) == [10]


# Test case 5: edge_id is enabled return single downstream vertex (branch).
def test_Downstream_Edge3(test_graph):
    assert test_graph.find_downstream_vertices(3) == [4]


# Test case 6: edge_id is enabled return single downstream vertex (leaf in branch).
def test_Downstream_Edge5(test_graph):
    assert test_graph.find_downstream_vertices(5) == [6]


# **Testing for function: find_alternative_edges**
# Test case 1: disabled_edge_id does not exist. (IDNotFoundError)
def test_IDNotFoundError_DisabledEdge_NotFound(test_graph) -> None:
    with pytest.raises(IDNotFoundError, match="Invalid id: 12 does not exist."):
        test_graph.find_alternative_edges(12)


# Test case 2: disabled_edge_id is already disabled. (EdgeAlreadyDisabledError)
def test_EdgeAlreadyDisabledError(test_graph) -> None:
    with pytest.raises(EdgeAlreadyDisabledError, match="Edge 7 is already disabled."):
        test_graph.find_alternative_edges(7)


# Test case 3: one alternative edge to make the graph fully connected again. (return list with one edge id)
def test_OneAlternativeEdge(test_graph):
    assert test_graph.find_alternative_edges(1) == [7]


# Test case 4: one alternative edge to make the graph fully connected again. (return list with one edge id)
def test_OneAlternativeEdge_2(test_graph):
    assert test_graph.find_alternative_edges(5) == [8]


# Test case 5: two alternative edges to make the graph fully connected again. (return list with two edge ids)
def test_TwoAlternativeEdges(test_graph):
    assert test_graph.find_alternative_edges(3) == [7, 8]


# Test case 6: no alternative edge to make the graph fully connected again. (return empty list)
def test_NoAlternativeEdge(test_graph):
    assert test_graph.find_alternative_edges(9) == []
