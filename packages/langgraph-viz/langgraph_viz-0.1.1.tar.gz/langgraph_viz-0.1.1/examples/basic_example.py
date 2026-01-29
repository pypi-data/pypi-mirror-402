"""Example: Basic LangGraph workflow with visualization."""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# Define state
class AgentState(TypedDict):
    """State for our simple agent."""
    query: str
    step_count: int
    result: str
    thoughts: list


def router_node(state: AgentState) -> AgentState:
    """Analyze the query and decide what to do."""
    print(f"Router: Processing query '{state['query']}'")
    state["step_count"] = state.get("step_count", 0) + 1
    state["thoughts"] = state.get("thoughts", [])
    state["thoughts"].append("Router is analyzing the query")
    
    # Simple routing logic
    if "weather" in state["query"].lower():
        state["route"] = "weather"
    elif "math" in state["query"].lower():
        state["route"] = "math"
    else:
        state["route"] = "general"
    
    return state


def weather_node(state: AgentState) -> AgentState:
    """Handle weather queries."""
    print("Weather: Getting weather info")
    state["step_count"] = state.get("step_count", 0) + 1
    state["thoughts"].append("Weather node is processing")
    state["result"] = f"The weather for your query is sunny! ☀️"
    return state


def math_node(state: AgentState) -> AgentState:
    """Handle math queries."""
    print("Math: Solving math problem")
    state["step_count"] = state.get("step_count", 0) + 1
    state["thoughts"].append("Math node is calculating")
    state["result"] = f"The answer to your math question is 42! 🔢"
    return state


def general_node(state: AgentState) -> AgentState:
    """Handle general queries."""
    print("General: Processing general query")
    state["step_count"] = state.get("step_count", 0) + 1
    state["thoughts"].append("General node is responding")
    state["result"] = f"Here's a general response to '{state['query']}' 💬"
    return state


def route_decision(state: AgentState) -> str:
    """Determine which node to go to next."""
    route = state.get("route", "general")
    print(f"Routing to: {route}")
    return route


# Build the graph
def create_example_workflow():
    """Create a simple example workflow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("weather", weather_node)
    workflow.add_node("math", math_node)
    workflow.add_node("general", general_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "weather": "weather",
            "math": "math",
            "general": "general",
        }
    )
    
    # All specialized nodes go to END
    workflow.add_edge("weather", END)
    workflow.add_edge("math", END)
    workflow.add_edge("general", END)
    
    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph Visualizer - Example Workflow")
    print("=" * 60)
    
    # Import visualizer
    from langgraph_viz import visualize
    
    # Create workflow
    app = create_example_workflow()
    
    # Visualize it!
    print("\n🎨 Starting visualization server...")
    print("📊 Browser should open automatically with live visualization\n")
    
    with visualize(app, port=8765) as viz_app:
        # Test different queries
        test_queries = [
            "What's the weather like today?",
            "Solve this math problem: 2 + 2",
            "Tell me something interesting"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print('='*60)
            
            config = {"configurable": {"thread_id": f"test-{hash(query)}"}}
            
            # Stream the execution
            for event in viz_app.stream({"query": query}, config):
                node_name = list(event.keys())[0]
                print(f"✓ Completed node: {node_name}")
            
            print(f"\nDone! Check the browser for visualization.\n")
            
            # Pause between queries
            import time
            time.sleep(2)
    
    print("\n" + "="*60)
    print("✓ Visualization complete!")
    print("="*60)
