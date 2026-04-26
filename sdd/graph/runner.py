"""Build and run the SDD LangGraph pipeline with MemorySaver checkpointing."""

from __future__ import annotations

import json
import time
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from sdd.graph.nodes import (
    node_analysis,
    node_critic,
    node_evidence,
    node_finalize,
    node_research,
    node_writer,
)
from sdd.graph.routing import route_after_critic
from sdd.graph.state import PipelineState


def build_graph() -> StateGraph:
    """Construct the SDD pipeline graph with all nodes and edges."""
    graph = StateGraph(PipelineState)

    graph.add_node("research", node_research)
    graph.add_node("evidence", node_evidence)
    graph.add_node("analysis", node_analysis)
    graph.add_node("writer", node_writer)
    graph.add_node("critic", node_critic)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("research")
    graph.add_edge("research", "evidence")
    graph.add_edge("evidence", "analysis")
    graph.add_edge("analysis", "writer")
    graph.add_edge("writer", "critic")
    graph.add_conditional_edges("critic", route_after_critic)
    graph.add_edge("finalize", END)

    return graph


def run_pipeline(inputs: dict, thread_id: str = "default") -> dict:
    """Compile graph and stream execution, writing events to output/pipeline_events.jsonl."""
    graph = build_graph()
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    events_path = Path("output/pipeline_events.jsonl")
    events_path.parent.mkdir(exist_ok=True)

    config = {"configurable": {"thread_id": thread_id}}
    final_state: dict = {}

    with events_path.open("a") as events_file:
        for chunk in app.stream(inputs, config=config, stream_mode="updates"):
            node_name, state_delta = next(iter(chunk.items()))
            event = {"event": node_name, "details": state_delta, "ts": time.time()}
            events_file.write(json.dumps(event, default=str) + "\n")
            final_state.update(state_delta)

    return final_state
