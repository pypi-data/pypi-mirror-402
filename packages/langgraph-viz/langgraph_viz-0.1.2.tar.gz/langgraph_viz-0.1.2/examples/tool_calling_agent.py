"""Example: Tool-Calling Agent with Dynamic Tool Selection.

This example demonstrates:
- Agent with access to multiple external tools
- Dynamic tool selection based on query analysis
- Tool invocation and result processing
- Multi-tool workflows for complex tasks
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import datetime
import random


# Define agent state
class ToolAgentState(TypedDict):
    """State for tool-calling agent."""
    user_query: str  # User's request
    required_tools: List[str]  # Tools needed for this task
    tool_results: Dict[str, Any]  # Results from tool calls
    current_tool: str  # Currently executing tool
    final_answer: str  # Final response to user
    execution_log: List[str]  # Log of actions taken


# Mock tool implementations
class Tools:
    """Collection of tools available to the agent."""
    
    @staticmethod
    def calculator(expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expressions."""
        try:
            # Safe evaluation of simple math expressions
            result = eval(expression, {"__builtins__": {}}, {})
            return {
                "tool": "calculator",
                "expression": expression,
                "result": result,
                "success": True
            }
        except Exception as e:
            return {
                "tool": "calculator",
                "expression": expression,
                "error": str(e),
                "success": False
            }
    
    @staticmethod
    def web_search(query: str) -> Dict[str, Any]:
        """Simulate web search (mock results)."""
        results = [
            {
                "title": f"Result about {query}",
                "snippet": f"This is a relevant snippet about {query}. It contains useful information for answering questions.",
                "url": f"https://example.com/{query.replace(' ', '-')}"
            },
            {
                "title": f"Guide to {query}",
                "snippet": f"Comprehensive guide covering everything about {query}. Updated recently with latest information.",
                "url": f"https://guides.com/{query.replace(' ', '-')}"
            }
        ]
        return {
            "tool": "web_search",
            "query": query,
            "results": results,
            "count": len(results),
            "success": True
        }
    
    @staticmethod
    def datetime_tool(operation: str) -> Dict[str, Any]:
        """Get current date/time or perform date calculations."""
        now = datetime.datetime.now()
        
        if operation == "current":
            return {
                "tool": "datetime",
                "operation": operation,
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": now.timestamp(),
                "success": True
            }
        elif operation == "tomorrow":
            tomorrow = now + datetime.timedelta(days=1)
            return {
                "tool": "datetime",
                "operation": operation,
                "date": tomorrow.strftime("%Y-%m-%d"),
                "day_of_week": tomorrow.strftime("%A"),
                "success": True
            }
        return {"tool": "datetime", "error": "Unknown operation", "success": False}
    
    @staticmethod
    def file_analyzer(filename: str) -> Dict[str, Any]:
        """Analyze file properties (mock)."""
        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".md": "Markdown",
            ".json": "JSON",
            ".txt": "Text"
        }
        
        ext = "." + filename.split(".")[-1] if "." in filename else ""
        file_type = extensions.get(ext, "Unknown")
        
        return {
            "tool": "file_analyzer",
            "filename": filename,
            "extension": ext,
            "file_type": file_type,
            "size_bytes": random.randint(100, 10000),
            "line_count": random.randint(10, 500),
            "success": True
        }
    
    @staticmethod
    def unit_converter(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """Convert between units (mock implementation)."""
        conversions = {
            ("celsius", "fahrenheit"): lambda x: (x * 9/5) + 32,
            ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
            ("km", "miles"): lambda x: x * 0.621371,
            ("miles", "km"): lambda x: x / 0.621371,
            ("kg", "lbs"): lambda x: x * 2.20462,
            ("lbs", "kg"): lambda x: x / 2.20462,
        }
        
        key = (from_unit.lower(), to_unit.lower())
        if key in conversions:
            result = conversions[key](value)
            return {
                "tool": "unit_converter",
                "input_value": value,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "result": round(result, 2),
                "success": True
            }
        return {
            "tool": "unit_converter",
            "error": f"Conversion from {from_unit} to {to_unit} not supported",
            "success": False
        }


def analyze_request(state: ToolAgentState) -> ToolAgentState:
    """Analyze the user request and determine which tools are needed."""
    print(f"\n🧠 ANALYZER: Understanding user request...")
    
    query = state["user_query"].lower()
    print(f"   Query: '{state['user_query']}'")
    
    tools_needed = []
    
    # Simple keyword-based tool detection
    if any(word in query for word in ["calculate", "math", "+", "-", "*", "/"]):
        tools_needed.append("calculator")
    
    if any(word in query for word in ["search", "find", "look up", "what is"]):
        tools_needed.append("web_search")
    
    if any(word in query for word in ["time", "date", "today", "tomorrow", "when"]):
        tools_needed.append("datetime")
    
    if any(word in query for word in ["file", "analyze", "extension"]):
        tools_needed.append("file_analyzer")
    
    if any(word in query for word in ["convert", "celsius", "fahrenheit", "km", "miles"]):
        tools_needed.append("unit_converter")
    
    if not tools_needed:
        tools_needed.append("web_search")  # Default tool
    
    state["required_tools"] = tools_needed
    state["tool_results"] = {}
    state["execution_log"] = []
    
    print(f"   🔧 Tools needed: {', '.join(tools_needed)}")
    print(f"   ✅ Analysis complete")
    
    return state


def call_tools(state: ToolAgentState) -> ToolAgentState:
    """Execute all required tools."""
    print(f"\n🔨 TOOL EXECUTOR: Calling tools...")
    
    query = state["user_query"]
    tools = state.get("required_tools", [])
    results = state.get("tool_results", {})
    log = state.get("execution_log", [])
    
    for tool_name in tools:
        print(f"\n   🔧 Executing: {tool_name}")
        state["current_tool"] = tool_name
        
        # Call appropriate tool with context from query
        if tool_name == "calculator":
            # Extract math expression from query
            expr = query.replace("calculate", "").replace("what is", "").strip()
            # Simple cleanup
            for word in ["the", "of", "result", "answer"]:
                expr = expr.replace(word, "")
            expr = expr.strip()
            result = Tools.calculator(expr)
        
        elif tool_name == "web_search":
            # Extract search query
            search_query = query.replace("search for", "").replace("find", "").replace("look up", "").strip()
            result = Tools.web_search(search_query)
        
        elif tool_name == "datetime":
            # Determine operation
            if "tomorrow" in query:
                result = Tools.datetime_tool("tomorrow")
            else:
                result = Tools.datetime_tool("current")
        
        elif tool_name == "file_analyzer":
            # Extract filename
            words = query.split()
            filename = next((w for w in words if "." in w), "example.py")
            result = Tools.file_analyzer(filename)
        
        elif tool_name == "unit_converter":
            # Parse conversion request (simplified)
            if "celsius" in query and "fahrenheit" in query:
                value = 25  # Example value
                result = Tools.unit_converter(value, "celsius", "fahrenheit")
            elif "km" in query and "miles" in query:
                value = 10  # Example value
                result = Tools.unit_converter(value, "km", "miles")
            else:
                result = {"tool": "unit_converter", "error": "Could not parse conversion", "success": False}
        
        else:
            result = {"tool": tool_name, "error": "Unknown tool", "success": False}
        
        # Store result
        results[tool_name] = result
        
        # Log execution
        if result.get("success"):
            print(f"      ✓ Success: {result}")
            log.append(f"✓ {tool_name}: Success")
        else:
            print(f"      ✗ Error: {result.get('error')}")
            log.append(f"✗ {tool_name}: {result.get('error')}")
    
    state["tool_results"] = results
    state["execution_log"] = log
    
    print(f"\n   ✅ All tools executed")
    
    return state


def process_results(state: ToolAgentState) -> ToolAgentState:
    """Process tool results and generate final answer."""
    print(f"\n📊 PROCESSOR: Synthesizing results...")
    
    query = state["user_query"]
    results = state.get("tool_results", {})
    
    # Build answer from tool results
    answer_parts = [f"Based on your request: '{query}'\\n"]
    
    for tool_name, result in results.items():
        if result.get("success"):
            if tool_name == "calculator":
                answer_parts.append(
                    f"\\n🔢 Calculator: {result['expression']} = {result['result']}"
                )
            
            elif tool_name == "web_search":
                answer_parts.append(
                    f"\\n🔍 Web Search: Found {result['count']} results for '{result['query']}':"
                )
                for idx, res in enumerate(result['results'][:2], 1):
                    answer_parts.append(f"   {idx}. {res['title']} - {res['snippet']}")
            
            elif tool_name == "datetime":
                if result['operation'] == "current":
                    answer_parts.append(
                        f"\\n📅 Current Time: {result['datetime']}"
                    )
                elif result['operation'] == "tomorrow":
                    answer_parts.append(
                        f"\\n📅 Tomorrow: {result['date']} ({result['day_of_week']})"
                    )
            
            elif tool_name == "file_analyzer":
                answer_parts.append(
                    f"\\n📄 File Analysis: {result['filename']} is a {result['file_type']} file "
                    f"({result['size_bytes']} bytes, ~{result['line_count']} lines)"
                )
            
            elif tool_name == "unit_converter":
                answer_parts.append(
                    f"\\n🔄 Conversion: {result['input_value']} {result['from_unit']} = "
                    f"{result['result']} {result['to_unit']}"
                )
        else:
            answer_parts.append(f"\\n❌ {tool_name}: {result.get('error', 'Failed')}")
    
    state["final_answer"] = "\\n".join(answer_parts)
    
    print(f"   ✅ Final answer generated")
    print(f"   📝 Used {len(results)} tool(s)")
    
    return state


def create_tool_agent():
    """Create the tool-calling agent workflow."""
    workflow = StateGraph(ToolAgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_request)
    workflow.add_node("call_tools", call_tools)
    workflow.add_node("process", process_results)
    
    # Define flow
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "call_tools")
    workflow.add_edge("call_tools", "process")
    workflow.add_edge("process", END)
    
    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


if __name__ == "__main__":
    print("=" * 70)
    print("🔧 LangGraph Viz - Tool-Calling Agent")
    print("=" * 70)
    
    from langgraph_viz import visualize
    
    # Create tool agent
    app = create_tool_agent()
    
    print("\\n🎨 Starting visualization server...")
    print("📊 Watch how the agent selects and executes tools!")
    print("💡 Notice the dynamic tool selection based on query analysis\\n")
    
    # Start visualization
    with visualize(app, port=8765) as viz_app:
        # Test queries requiring different tools
        queries = [
            "Calculate 42 * 17 + 89",
            "What's the current time and date?",
            "Search for information about LangGraph",
            "Convert 25 celsius to fahrenheit",
            "Analyze the file example.py",
        ]
        
        for idx, query in enumerate(queries, 1):
            print(f"\\n{'='*70}")
            print(f"Query {idx}: {query}")
            print('='*70)
            
            config = {"configurable": {"thread_id": f"tool-agent-{idx}"}}
            
            # Run agent
            input_state = {"user_query": query}
            
            print(f"\\n🚀 Starting tool agent...\\n")
            for event in viz_app.stream(input_state, config):
                node_name = list(event.keys())[0]
                print(f"      [{node_name}] completed")
            
            # Display results
            final_state = viz_app.get_state(config)
            if final_state and final_state.values:
                state = final_state.values
                print(f"\\n{'─'*70}")
                print("🤖 AGENT RESPONSE:")
                print('─'*70)
                print(state.get("final_answer", "No response"))
                print('─'*70)
                
                print(f"\\n📋 Execution Log:")
                for log_entry in state.get("execution_log", []):
                    print(f"   {log_entry}")
            
            print(f"\\n✅ Query {idx} complete - check visualization!")
            
            # Pause between queries
            if idx < len(queries):
                import time
                time.sleep(2)
        
        print(f"\\n{'='*70}")
        print("🎯 All tool-calling tasks complete!")
        print("💡 Agent capabilities demonstrated:")
        print("   - Calculator for math operations")
        print("   - Web search for information retrieval")
        print("   - DateTime for time-based queries")
        print("   - File analyzer for file operations")
        print("   - Unit converter for conversions")
        print('='*70)
        
        # Keep server running
        print("\\n⏸️  Server running - Press Ctrl+C to exit\\n")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\n\\n👋 Shutting down...")
    
    print("\\n✓ Visualization complete!\\n")
