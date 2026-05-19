from power_system_simulation.graph_processing import (
    EdgeAlreadyDisabledError,
    GraphCycleError,
    GraphNotFullyConnectedError,
    GraphProcessor,
    IDNotFoundError,
    IDNotUniqueError,
    InputLengthDoesNotMatchError,
)


# Test condition 1.1: vertex_ids are not unique. (IDNotUniqueError)
def test_IDNotUniqueError_VertexIDs():
    vertex_ids = [0, 1, 1]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotUniqueError was not raised while vertex_ids are not unique.")
    except IDNotUniqueError:
        pass

# Test condition 1.2: edge_ids are not unique. (IDNotUniqueError)
def test_IDNotUniqueError_EdgeIDs():
    vertex_ids = [0, 1, 2]
    edge_ids = [10, 10]
    edge_vertex_id_pairs = [(0, 1), (1, 2)]
    edge_enabled = [True, True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotUniqueError was not raised while edge_ids are not unique.")
    except IDNotUniqueError:
        pass

# Test condition 2: edge_vertex_id_pairs is not the same length as edge_ids. (InputLengthDoesNotMatchError)
def test_InputLengthDoesNotMatchError_EdgeVertexPairsLengthMismatch():
    vertex_ids = [0, 1, 2]
    edge_ids = [10, 11]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True, False]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("InputLengthDoesNotMatchError was not raised while edge_vertex_id_pairs and edge_ids lengths do not match.") # noqa: E501
    except InputLengthDoesNotMatchError:
        pass

# Test condition 3.0: edge_vertex_id_pairs contains valid vertex ids. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_Correct():
    vertex_ids = [0, 1, 2]
    edge_ids = [10, 11]
    edge_vertex_id_pairs = [(0, 1), (1, 2)]
    edge_enabled = [True, True]
    source_vertex_id = 0

    graph = GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert isinstance(graph, GraphProcessor)

# Test condition 3.1: edge_vertex_id_pairs does not contain tuples. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_NotTuple():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [0]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while edge_vertex_id_pairs does not contain tuples.")
    except IDNotFoundError:
        pass

# Test condition 3.2: edge_vertex_id_pairs does not contain tuples of length 2. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_WrongLength():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1, 2)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while tuples in edge_vertex_id_pairs have incorrect length.") # noqa: E501
    except IDNotFoundError:
        pass

# Test condition 3.3: edge_vertex_id_pairs does not contain tuples of integers. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_NonInt1():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [("1", 0)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while tuples in edge_vertex_id_pairs contain non-integer values.") # noqa: E501
    except IDNotFoundError:
        pass

# Test condition 3.4: edge_vertex_id_pairs does not contain tuples of integers. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_NonInt2():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, "1")]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while tuples in edge_vertex_id_pairs contain non-integer values.") # noqa: E501
    except IDNotFoundError:
        pass

#Test condition 3.5: edge_vertex_id_pairs does not contain valid vertex ids. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_IdNotFound1():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(3, 0)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while edge_vertex_id_pairs does not contain valid vertex ids.") # noqa: E501
    except IDNotFoundError:
        pass

# Test condition 3.6: edge_vertex_id_pairs does not contain valid vertex ids. (IDNotFoundError)
def test_IDNotFoundError_EdgeVertex_IdNotFound2():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 3)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while edge_vertex_id_pairs does not contain valid vertex ids.") # noqa: E501
    except IDNotFoundError:
        pass

# Test condition 4: edge_enabled is not the same length as edge_ids. (InputLengthDoesNotMatchError)
def test_InputLengthDoesNotMatchError_EdgeEnabledLengthMismatch():
    vertex_ids = [0, 1, 2]
    edge_ids = [10, 11]
    edge_vertex_id_pairs = [(0, 1), (1, 2)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("InputLengthDoesNotMatchError was not raised while edge_enabled is not the same length as edge_ids.") # noqa: E501
    except InputLengthDoesNotMatchError:
        pass

# Test condition 5.0: source_vertex_id is a valid vertex id. (IDNotFoundError)
def test_IDNotFoundError_SourceVertex_Correct():
    vertex_ids = [0, 1, 2]
    edge_ids = [10, 11]
    edge_vertex_id_pairs = [(0, 1), (1, 2)]
    edge_enabled = [True, True]
    source_vertex_id = 1

    graph = GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert isinstance(graph, GraphProcessor)

# Test condition 5.1: source_vertex_id is not an integer. (IDNotFoundError)
def test_IDNotFoundError_SourceVertex_NonInt():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = "0"

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while source_vertex_id is not an integer.")
    except IDNotFoundError:
        pass

# Test condition 5.2: source_vertex_id does not exist in vertex_ids. (IDNotFoundError)
def test_IDNotFoundError_SourceVertex_IdNotFound():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = 3

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised while source_vertex_id does not exist in vertex_ids.")
    except IDNotFoundError:
        pass

# Test condition 6: the graph is not fully connected. (GraphNotFullyConnectedError)
def test_GraphNotFullyConnectedError():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("GraphNotFullyConnectedError was not raised while the graph is not fully connected.")
    except GraphNotFullyConnectedError:
        pass

# Test condition 7: the graph contains cycles. (GraphCycleError)
def test_GraphCycleError():
    vertex_ids = [0, 1, 2]
    edge_ids = [10, 11, 12]
    edge_vertex_id_pairs = [(0, 1), (1, 2), (2, 0)]
    edge_enabled = [True, True, True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("GraphCycleError was not raised while the graph contains cycles.")
    except GraphCycleError:
        pass

# **Testing for function: find_alternative_edges**
# Initialize a graph to test find_alternative_edges function.
def initialize_test_graph():
    """vertex_0 (source) --edge_1(enabled)-- vertex_2 --edge_9(enabled)-- vertex_10
                 |                               |
                 |                           edge_7(disabled)
                 |                               |
                 -----------edge_3(enabled)-- vertex_4
                 |                               |
                 |                           edge_8(disabled)
                 |                               |
                 -----------edge_5(enabled)-- vertex_6"""
    vertex_ids = [0, 2, 4, 6, 10]
    edge_ids = [1, 3, 5, 7, 8, 9]
    edge_vertex_id_pairs = [(0, 2), (0, 4), (0, 6), (2, 4), (4, 6), (2, 10)]
    edge_enabled = [True, True, True, False, False, True]
    source_vertex_id = 0

    return GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)

# Test case 1: disabled_edge_id does not exist. (IDNotFoundError)
def test_IDNotFoundError_DisabledEdge_NotFound():
    graph = initialize_test_graph()

    try:
        graph.find_alternative_edges(12)
        raise AssertionError("IDNotFoundError was not raised while disabled_edge_id does not exist.")
    except IDNotFoundError:
        pass

# Test case 2: disabled_edge_id is already disabled. (EdgeAlreadyDisabledError)
def test_EdgeAlreadyDisabledError():
    graph = initialize_test_graph()

    try:
        graph.find_alternative_edges(7)
        raise AssertionError("EdgeAlreadyDisabledError was not raised while disabled_edge_id is already disabled.")
    except EdgeAlreadyDisabledError:
        pass

# Test case 3: one alternative edge to make the graph fully connected again. (return list with one edge id)
def test_OneAlternativeEdge():
    graph = initialize_test_graph()

    assert graph.find_alternative_edges(1) == [7]

# Test case 4: one alternative edge to make the graph fully connected again. (return list with one edge id)
def test_OneAlternativeEdge_2():
    graph = initialize_test_graph()

    assert graph.find_alternative_edges(5) == [8]

# Test case 5: two alternative edges to make the graph fully connected again. (return list with two edge ids)
def test_TwoAlternativeEdges():
    graph = initialize_test_graph()

    assert graph.find_alternative_edges(3) == [7, 8]

# Test case 6: no alternative edge to make the graph fully connected again. (return empty list)
def test_NoAlternativeEdge():
    graph = initialize_test_graph()

    assert graph.find_alternative_edges(9) == []
