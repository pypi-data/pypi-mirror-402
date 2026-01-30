"""Basic tests for Landscape widget class."""

import pytest
from traitlets import TraitError

from landscape_widget import Landscape

default_graph = {
    0: {
        "nodes": [
            {"points": [0], "size": 4},
            {"points": [1], "size": 4},
            {"points": [2], "size": 4},
            {"points": [3], "size": 4},
        ],
        "edges": [
            {"s": 0, "t": 1, "w": 1},
            {"s": 1, "t": 2, "w": 0.75},
            {"s": 2, "t": 3, "w": 0.5},
            {"s": 0, "t": 3, "w": 0.25},
        ],
    },
    1: {
        "nodes": [
            {"points": [0, 1], "size": 4},
            {"points": [2, 3], "size": 4},
        ],
        "edges": [{"s": 0, "t": 1, "w": 1}],
    },
    2: {
        "nodes": [
            {"points": [0, 1, 2, 3], "size": 4},
        ],
        "edges": [],
    },
}


def test_instantiate_widget_default():
    _ = Landscape()


def test_instantiate_widget_one_level():
    graph = {0: default_graph[0]}
    _ = Landscape(graph=graph)


def test_instantiate_widget_multi_level():
    _ = Landscape(graph=default_graph)


def test_set_landscape_node_labels_all_nodes_all_levels():
    landscape = Landscape(graph=default_graph)
    landscape.node_labels = {
        0: {
            0: "node 0",
            1: "node 1",
            2: "node 2",
            3: "node 3",
        },
        1: {
            0: "node 0",
            1: "node 1",
        },
        2: {
            0: "node 0",
        },
    }


def test_set_landscape_node_labels_all_nodes_one_level():
    landscape = Landscape(graph=default_graph)
    landscape.node_labels = {1: {0: "node 0", 1: "node 1"}}


def test_set_landscape_node_labels_some_nodes_one_level():
    landscape = Landscape(graph=default_graph)
    landscape.node_labels = {0: {1: "node 1", 3: "node 3"}}


def test_set_landscape_node_hover_labels_all_nodes_all_levels():
    landscape = Landscape(graph=default_graph)
    landscape.node_hover_labels = {
        0: {
            0: "node 0",
            1: "node 1",
            2: "node 2",
            3: "node 3",
        },
        1: {
            0: "node 0",
            1: "node 1",
        },
        2: {
            0: "node 0",
        },
    }


def test_set_landscape_node_hover_labels_all_nodes_one_level():
    landscape = Landscape(graph=default_graph)
    landscape.node_hover_labels = {1: {0: "node 0", 1: "node 1"}}


def test_set_landscape_node_hover_labels_some_nodes_one_level():
    landscape = Landscape(graph=default_graph)
    landscape.node_hover_labels = {0: {1: "node 1", 3: "node 3"}}


def test_set_landscape_node_colors():
    landscape = Landscape(graph=default_graph)
    landscape.colors = {
        0: ["#000", "#000", "#000", "#000"],
        1: ["#000", "#000"],
        2: ["#000"],
    }


def test_landscape_selected_level():
    landscape = Landscape(graph=default_graph)
    landscape.selected_level = 2
    landscape.selected_level = 0
    with pytest.raises(TraitError):
        landscape.selected_level = 5


def test_landscape_avg_degree():
    landscape = Landscape(graph=default_graph)
    landscape.avg_degree = 2
    landscape.avg_degree = 0
    with pytest.raises(TraitError):
        landscape.avg_degree = -1


def test_landscape_point_selection():
    landscape = Landscape(graph=default_graph)
    selection_log = []

    def selection_listener(x):
        selection_log.append(x)

    landscape.on_select_points(selection_listener)
    landscape.selected_points = [1]
    landscape.selected_points = [2]
    with landscape.use_selection_listeners(False):
        landscape.selected_points = [1, 2, 3]
    landscape.selected_points = [0, 1, 3]
    landscape.selected_points = []
    assert selection_log == [[1], [2], [0, 1, 3], []]
