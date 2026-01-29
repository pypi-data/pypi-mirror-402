"""
Quick verification script to test the package visually.
This doesn't auto-open the browser but still runs the server.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph_viz import visualize


class TestState(TypedDict):
    count: int
    logs: list


def increment_node(state: TestState) -> TestState:
    """Increment counter."""
    state["count"] = state.get("count", 0) + 1
    state["logs"] = state.get("logs", [])
    state["logs"].append(f"Incremented to {state['count']}")
    return state


def double_node(state: TestState) -> TestState:
    """Double the counter."""
    state["count"] = state.get("count", 0) * 2
    state["logs"] = state.get("logs", [])
    state["logs"].append(f"Doubled to {state['count']}")
    return state


if __name__ == "__main__":
    # Build workflow
    workflow = StateGraph(TestState)
    workflow.add_node("increment", increment_node)
    workflow.add_node("double", double_node)
    workflow.set_entry_point("increment")
    workflow.add_edge("increment", "double")
    workflow.add_edge("double", END)
    
    app = workflow.compile()
    
    print("=" * 60)
    print("Quick Verification Test")
    print("=" * 60)
    print("\nStarting server (browser will NOT auto-open)")
    print("To view visualization, open: http://localhost:9000\n")
    
    # Use visualizer with auto_open=False for testing
    with visualize(app, port=9000, auto_open=False) as viz_app:
        print("Running workflow...")
        result = viz_app.invoke({"count": 5})
        print(f"\nResult: {result}")
        print(f"Expected: count=12, logs=['Incremented to 6', 'Doubled to 12']")
        print(f"Actual:   count={result['count']}, logs={result['logs']}")
        
        # Verify
        assert result["count"] == 12, f"Expected 12, got {result['count']}"
        assert len(result["logs"]) == 2, f"Expected 2 logs, got {len(result['logs'])}"
        
        print("\n✅ Workflow executed correctly!")
        print("✅ Server is running with state visualization")
        print("\nYou can manually open http://localhost:9000 to see the visualization")
        print("Press Ctrl+C to exit...")
        
        # Keep running so user can check browser
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
    
    print("✓ Test complete!")
