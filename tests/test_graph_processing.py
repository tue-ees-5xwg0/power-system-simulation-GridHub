from power_system_simulation.graph_processing import GraphProcessor, IDNotFoundError, InputLengthDoesNotMatchError


def test_IDNotFoundError_EdgeVertex_Correct():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = 0

    graph = GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert isinstance(graph, GraphProcessor)

def test_IDNotFoundError_EdgeVertex_NotTuple():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [0]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass


def test_InputLengthDoesNotMatchError_EdgeVertexLengthMismatch():
    vertex_ids = [0, 1, 2]
    edge_ids = [10, 11]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True, False]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("InputLengthDoesNotMatchError was not raised")
    except InputLengthDoesNotMatchError:
        pass


def test_IDNotFoundError_EdgeVertex_WrongLength():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1, 2)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass


def test_IDNotFoundError_EdgeVertex_NonInt1():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [("1", 0)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass

def test_IDNotFoundError_EdgeVertex_NonInt2():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, "1")]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass

def test_IDNotFoundError_EdgeVertex_IdNotFound1():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(3, 0)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass

def test_IDNotFoundError_EdgeVertex_IdNotFound2():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 3)]
    edge_enabled = [True]
    source_vertex_id = 0

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass


def test_IDNotFoundError_SourceVertex_Correct():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = 1

    graph = GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
    assert isinstance(graph, GraphProcessor)


def test_IDNotFoundError_SourceVertex_NonInt():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = "0"

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass


def test_IDNotFoundError_SourceVertex_IdNotFound():
    vertex_ids = [0, 1, 2]
    edge_ids = [10]
    edge_vertex_id_pairs = [(0, 1)]
    edge_enabled = [True]
    source_vertex_id = 3

    try:
        GraphProcessor(vertex_ids, edge_ids, edge_vertex_id_pairs, edge_enabled, source_vertex_id)
        raise AssertionError("IDNotFoundError was not raised")
    except IDNotFoundError:
        pass

