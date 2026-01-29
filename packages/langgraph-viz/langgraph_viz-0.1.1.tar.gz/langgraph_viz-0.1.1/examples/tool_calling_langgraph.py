"""Example: Real LLM Tool-Calling with LangGraph Visualizer.

This example demonstrates:
- Actual LLM making tool-calling decisions
- Real-time visualization of tool invocations
- Conditional routing based on LLM decisions
- Integration with Ollama Cloud
"""

from typing import Annotated
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
import os
from langchain_openai import ChatOpenAI
from typing import TypedDict
from langchain_core.tools import tool

# Load environment variables
load_dotenv(override=True)

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("OLLAMA_CLOUD_MODEL"),
    base_url=os.getenv("OLLAMA_CLOUD_URL"),
    api_key=os.getenv("OLLAMA_CLOUD_API_KEY"),
)

# Define tools
@tool
def get_weather(city: str) -> str:
    """Returns the current weather for a given city."""
    print(f"  🌤️  Tool called: get_weather(city='{city}')")
    return f"The weather in {city} is currently 72°F and sunny."

@tool
def multiply(a: int, b: int) -> int:
    """Multiplies two integers together."""
    print(f"  🔢 Tool called: multiply(a={a}, b={b})")
    return a * b

tools = [get_weather, multiply]
llm_with_tools = llm.bind_tools(tools)

# Define state
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Build graph
graph_builder = StateGraph(State)

def chatbot(state: State):
    """Chatbot node that invokes LLM with tools."""
    print(f"  🤖 Chatbot: Processing {len(state['messages'])} messages")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_conditional_edges('chatbot', tools_condition)
graph_builder.add_edge('tools', 'chatbot')
graph_builder.add_edge(START, 'chatbot')

# Compile with checkpointer for visualization
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)


if __name__ == "__main__":
    print("=" * 70)
    print("🤖 LangGraph Viz - Real LLM Tool-Calling Demo")
    print("=" * 70)
    
    from langgraph_viz import visualize
    
    print("\n🎨 Starting visualization server...")
    print("📊 Watch the LLM decide when to call tools!")
    print("💡 Notice the conditional routing based on LLM decisions\n")
    
    # Start visualization
    with visualize(graph, port=8767) as viz_graph:
        # Test queries that should trigger different tools
        queries = [
            "What is the weather in San Francisco?",
            "What is 23 multiplied by 17?",
            "Can you get the weather in New York and then multiply 5 by 8?",
        ]
        
        for idx, query in enumerate(queries, 1):
            print(f"\n{'='*70}")
            print(f"Query {idx}: {query}")
            print('='*70)
            
            config = {"configurable": {"thread_id": f"tool-demo-{idx}"}}
            
            # Stream the execution  
            print(f"\n🚀 LLM processing...\n")
            final_response = None
            for event in viz_graph.stream(
                {"messages": [{"role": "user", "content": query}]},
                config
                # Don't override stream_mode - let visualizer use dual-mode streaming
            ):
                # With visualizer, events come as (mode, data) tuples
                # mode can be "updates" or "values"
                if isinstance(event, tuple) and len(event) == 2:
                    mode, data = event
                    if mode == "values" and "messages" in data:
                        # Get the last message
                        last_msg = data["messages"][-1]
                        # Check if it's an AI message without tool calls (final response)
                        if hasattr(last_msg, 'type') and last_msg.type == "ai":
                            if not last_msg.tool_calls:
                                final_response = last_msg.content
            
            if final_response:
                print(f"\n💬 Response: {final_response}")
            
            print(f"\n✅ Query {idx} complete - check visualization!")
            
            # Pause between queries
            if idx < len(queries):
                import time
                time.sleep(2)
        
        print(f"\n{'='*70}")
        print("🎯 All queries complete!")
        print("💡 What you saw in the visualizer:")
        print("   - Chatbot node invokes LLM with tools")
        print("   - LLM decides whether to call tools")
        print("   - Tools_condition routes to 'tools' or END")
        print("   - Tools execute and loop back to chatbot")
        print("   - Final response generated without tool calls")
        print('='*70)
        
        # Keep server running
        print("\n⏸️  Server running on port 8767 - Press Ctrl+C to exit\n")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
    
    print("\n✓ Visualization complete!\n")