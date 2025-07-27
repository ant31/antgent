import contextlib
from contextvars import ContextVar
from datetime import datetime

import pydot
from pydot import Dot

from antgent.models.visibility import WorkflowStep

# This context variable holds the current parent step.
_current_step_cv: ContextVar[WorkflowStep | None] = ContextVar("current_step", default=None)


@contextlib.asynccontextmanager
async def track_step(name: str):
    """An async context manager to track a step in the execution graph."""
    parent_step = _current_step_cv.get()

    # If there's no parent, we are not in a tracked session.
    # Just run the code without creating a node.
    if parent_step is None:
        yield
        return

    new_step = WorkflowStep(name=name)
    parent_step.children.append(new_step)
    token = _current_step_cv.set(new_step)

    try:
        yield
        new_step.status = "COMPLETED"
    except Exception:
        new_step.status = "FAILED"
        raise
    finally:
        new_step.end_time = datetime.now(tz=None)
        _current_step_cv.reset(token)


def start_tracking(root_node: WorkflowStep):
    """Sets the root node to start tracking."""
    _current_step_cv.set(root_node)


def _get_node_style(status: str) -> dict:
    """Return style attributes based on node status."""
    if status == "COMPLETED":
        return {"fillcolor": "#DFF0D8", "style": "filled", "color": "#3c763d"}
    if status == "FAILED":
        return {"fillcolor": "#F2DEDE", "style": "filled", "color": "#a94442"}
    if status == "RUNNING":
        return {"fillcolor": "#D9EDF7", "style": "filled", "color": "#31708f"}
    return {}


def _add_nodes_edges(graph: "Dot", step: WorkflowStep):
    """Recursively add nodes and edges to the graph."""
    duration_str = ""
    if step.start_time and step.end_time:
        duration = step.end_time - step.start_time
        duration_str = f"\\nDuration: {duration.total_seconds():.2f}s"

    node_label = f"{step.name}\\nStatus: {step.status}{duration_str}"

    node_style = _get_node_style(step.status)

    node = pydot.Node(step.id, label=node_label, **node_style)
    graph.add_node(node)

    for child in step.children:
        _add_nodes_edges(graph, child)
        edge = pydot.Edge(step.id, child.id)
        graph.add_edge(edge)


def create_graph_visualization(root_step: WorkflowStep) -> "Dot":
    """Create a pydot graph from a WorkflowStep tree."""
    if pydot is None:
        raise ImportError(
            "pydot is not installed. To use graph visualization, please run: `uv pip install pydot graphviz`"
        )
    graph = pydot.Dot(graph_type="digraph", rankdir="TB", splines="ortho")
    _add_nodes_edges(graph, root_step)
    return graph
