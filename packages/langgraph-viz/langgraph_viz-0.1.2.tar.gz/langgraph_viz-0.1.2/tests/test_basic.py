"""Simple test to verify package works."""

from langgraph_viz import visualize, GraphVisualizer
from langgraph_viz.state_tracker import StateTracker, StateSnapshot
from langgraph_viz.serializer import StateSerializer
from typing import TypedDict
from langgraph.graph import StateGraph, END
from dataclasses import dataclass



class SimpleState(TypedDict):
    """Simple state for testing."""
    count: int
    message: str


def test_serializer():
    """Test state serializer."""
    serializer = StateSerializer()
    
    # Test dict
    assert serializer.serialize({"a": 1}) == {"a": 1}
    
    # Test nested
    nested = {"a": {"b": {"c": 1}}}
    assert serializer.serialize(nested) == nested
    
    # Test dataclass
    @dataclass
    class TestData:
        value: int
    
    data = TestData(value=42)
    assert serializer.serialize(data) == {"value": 42}


def test_state_tracker():
    """Test state tracker."""
    tracker = StateTracker()
    
    # Create test event
    event = {
        "type": "on_chain_end",
        "node": "test_node",
        "data": {"output": {"count": 1, "message": "hello"}},
        "timestamp": 1234567890.0
    }
    
    snapshot = tracker.update(event)
    
    assert snapshot is not None
    assert snapshot.node == "test_node"
    assert snapshot.state["count"] == 1
    assert snapshot.state["message"] == "hello"
    
    # Test diff on second update
    event2 = {
        "type": "on_chain_end",
        "node": "test_node_2",
        "data": {"output": {"count": 2, "message": "hello"}},
        "timestamp": 1234567891.0
    }
    
    snapshot2 = tracker.update(event2)
    assert snapshot2.diff is not None


def test_visualizer_initialization():
    """Test GraphVisualizer can be initialized."""
    # Create minimal workflow
    def simple_node(state: SimpleState) -> SimpleState:
        state["count"] += 1
        return state
    
    workflow = StateGraph(SimpleState)
    workflow.add_node("simple", simple_node)
    workflow.set_entry_point("simple")
    workflow.add_edge("simple", END)
    
    app = workflow.compile()
    
    # Test initialization
    viz = GraphVisualizer(app, port=9999, auto_open=False)
    assert viz.app == app
    assert viz.port == 9999
    assert viz.auto_open == False


def test_visualize_function():
    """Test visualize convenience function."""
    def simple_node(state: SimpleState) -> SimpleState:
        state["count"] += 1
        return state
    
    workflow = StateGraph(SimpleState)
    workflow.add_node("simple", simple_node)
    workflow.set_entry_point("simple")
    workflow.add_edge("simple", END)
    
    app = workflow.compile()
    
    # Test function
    viz = visualize(app, port=9998, auto_open=False)
    assert isinstance(viz, GraphVisualizer)


if __name__ == "__main__":
    print("Running tests...")
    
    test_serializer()
    print("✓ Serializer tests passed")
    
    test_state_tracker()
    print("✓ State tracker tests passed")
    
    test_visualizer_initialization()
    print("✓ Visualizer initialization tests passed")
    
    test_visualize_function()
    print("✓ visualize() function tests passed")
    
    print("\n✅ All tests passed!")
