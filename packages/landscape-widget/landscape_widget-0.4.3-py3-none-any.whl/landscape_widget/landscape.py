# Copyright (C) 2023-2024 BlueLightAI, Inc. All Rights Reserved.
#
# Any use, distribution, or modification of this software is subject to the
# terms of the BlueLightAI Software License Agreement.

"""An interactive graph rendering widget for Jupyter notebooks."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable
from typing import List as lst
from typing import NewType

from ipywidgets import DOMWidget
from traitlets import Bool, Dict, Float, Int, List, TraitError, Unicode, validate

from ._frontend import module_name, module_version

Selection = NewType("Selection", lst[int])
SelectionListener = Callable[[Selection], Any]

# example of the expected data structure
_default_graph = {
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


class Landscape(DOMWidget):
    """An interactive graph visualization."""

    _model_name = Unicode("LandscapeModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode("LandscapeView").tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    # TODO: custom graph type with optimized serialization?
    # we do not support changing graph once loaded
    graph = Dict(_default_graph).tag(sync=True)

    # these may be changed live, Python -> JS
    colors = Dict(None, allow_none=True).tag(sync=True)
    node_labels = Dict(None, allow_none=True).tag(sync=True)
    node_hover_labels = Dict(None, allow_none=True).tag(sync=True)
    node_attrs = Dict(None, allow_none=True).tag(sync=True)
    rich_node_hover_template = Unicode("").tag(sync=True)

    # these may be updated bidirectionally
    selected_level = Int(None, allow_none=True).tag(sync=True)
    avg_degree = Float(None, allow_none=True).tag(sync=True)
    selected_points = List([]).tag(sync=True)

    # this controls the state of the "expand graph" button in the controls
    # does not affect the layout directly; you must set up a listener for
    # changes and adjust the layout in the listener
    # updated JS -> Python
    is_expanded_layout = Bool(False).tag(sync=True)

    # must be set at instantiation
    sigma_settings = Dict({}).tag(sync=True)
    layout_config = Dict({}).tag(sync=True)
    show_buttons = Dict(None, allow_none=True).tag(sync=True)

    # may be updated live, Python -> JS
    background_color = Unicode(None, allow_none=True).tag(sync=True)

    def __init__(self, *args, **kwargs):
        self._is_init = True
        layout = kwargs.get("layout")
        if layout is None:
            layout = {"height": "400px", "width": "500px"}
        if layout.get("height") is None:
            layout["height"] = "400px"
        if layout.get("width") is None:
            layout["width"] = "500px"
        kwargs["layout"] = layout
        super().__init__(*args, **kwargs)
        self.point_selection_update_listeners = {}
        self.observe(
            self._run_point_selection_update_listeners, names="selected_points"
        )
        self._call_select_listeners: bool = True
        self._is_init: bool = False

    @validate("graph")
    def _valid_graph(self, proposal):
        if not self._is_init:
            raise TraitError("graph may only be set at widget construction time")
        for _, graph in proposal["value"].items():
            if "nodes" not in graph:
                raise TraitError("nodes not present")
            if "edges" not in graph:
                raise TraitError("edges not present")
        return proposal["value"]

    @validate("node_labels", "node_hover_labels")
    def _valid_node_labels(self, proposal):
        for level, labels in proposal["value"].items():
            if level not in self.graph:
                raise TraitError(f"level {level} not in graph")
            if not all(isinstance(k, int) for k in labels):
                raise TraitError("node keys must be integers")
            if not all(isinstance(v, str) for v in labels.values()):
                raise TraitError("labels must be strings")
        return proposal["value"]

    @validate("node_attrs")
    def _valid_node_attrs(self, proposal):
        for level, attrs in proposal["value"].items():
            if level not in self.graph:
                raise TraitError(f"level {level} not in graph")
            if not all(isinstance(k, int) for k in attrs):
                raise TraitError("node keys must be integers")
            if not all(isinstance(v, dict) for v in attrs.values()):
                raise TraitError("node_attrs must be dicts")
        return proposal["value"]

    @validate("selected_level")
    def _valid_selected_level(self, proposal):
        level = proposal["value"]
        if level not in self.graph:
            raise TraitError(f"selected_level {level} not in graph")
        return level

    @validate("avg_degree")
    def _valid_avg_degree(self, proposal):
        avg_degree = proposal["value"]
        if avg_degree < 0:
            raise TraitError("avg_degree must be >=0")
        return avg_degree

    @validate("show_buttons")
    def _valid_show_buttons(self, proposal):
        if proposal["value"] is None:
            return proposal["value"]

        valid_buttons = {
            "zoomIn",
            "zoomOut",
            "resetZoom",
            "resetLayout",
            "fullScreen",
            "lassoSelect",
            "boxSelect",
            "clearSelection",
            "invertSelection",
            "playPause",
            "downloadSVG",
        }

        show_buttons = proposal["value"]
        if not isinstance(show_buttons, dict):
            raise TraitError("show_buttons must be a dict")

        for key, value in show_buttons.items():
            if key not in valid_buttons:
                raise TraitError(
                    f"Invalid button name: {key}. Must be one of {valid_buttons}"
                )
            if not isinstance(value, bool):
                raise TraitError(f"show_buttons[{key}] must be a boolean")

        return proposal["value"]

    @contextmanager
    def use_selection_listeners(self, call_listeners: bool):
        """Sets up a context in which selection listeners are active or inactive
        based on the call_listeners parameter.
        """
        old_call_listeners = self._call_select_listeners
        self._call_select_listeners = call_listeners
        try:
            yield
        finally:
            self._call_select_listeners = old_call_listeners

    def _run_point_selection_update_listeners(self, update):
        if not self._call_select_listeners:
            return
        selected_points = update["new"]
        for callback in self.point_selection_update_listeners.values():
            callback(selected_points)

    def on_select_points(self, callback: SelectionListener) -> int:
        """Add a function to be run when the user selects nodes in the graph.

        The callback function must take a single argument of type list[int],
        which contains the ids of the selected data points. Whenever the set of
        selected nodes changes, this function will be called. Any return value
        will be ignored.

        Returns an id which can be used to remove a listener function by calling
        remove_node_select_listener().
        """
        if len(self.point_selection_update_listeners) == 0:
            listener_id = 0
        else:
            listener_id = max(self.point_selection_update_listeners.keys()) + 1
        self.point_selection_update_listeners[listener_id] = callback
        return listener_id

    def remove_point_selection_listener(self, listener_id: int):
        """Remove a listener previously added using on_select()"""
        self.point_selection_update_listeners.pop(listener_id)

    def clear_selection(self):
        """Clears the currently selected nodes and points.

        Note that this will trigger any registered listeners (unless called with
        the use_selection_listeners(False) context manager).
        """
        self.selected_points = []

    def dispose_graph(self):
        """Send a custom message to the frontend to trigger graph update."""
        self.send({"event_type": "dispose_graph"})

    def reset_view(self):
        self.send({"event_type": "reset_view"})
