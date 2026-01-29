# LangGraph Viz Examples

Welcome to the **LangGraph Viz** examples gallery! These examples demonstrate how to visualize different LangGraph workflow patterns in real-time using the browser-based visualization tool.

## 📚 Examples Overview

| Example | Description | Key Features | Difficulty |
|---------|-------------|--------------|------------|
| [Basic Example](#basic-example) | Simple routing workflow | Conditional routing, basic state | ⭐ Beginner |
| [Chatbot with Memory](#chatbot-with-memory) | Conversational agent | Persistent state, multi-turn conversation | ⭐ Beginner |
| [Multi-Agent Research](#multi-agent-research) | Collaborative agents | Supervisor pattern, agent coordination | ⭐⭐ Intermediate |
| [RAG Pipeline](#rag-pipeline) | Retrieval-augmented generation | Query analysis, self-correction loops | ⭐⭐ Intermediate |
| [Human-in-the-Loop](#human-in-the-loop) | Approval workflows | Interrupts, approval checkpoints | ⭐⭐ Intermediate |
| [Tool-Calling Agent](#tool-calling-agent) | Agent with tools | Dynamic tool selection, tool execution | ⭐⭐⭐ Advanced |
| [Hierarchical Workflow](#hierarchical-workflow) | Nested workflows | Subgraphs, workflow composition | ⭐⭐⭐ Advanced |

## 🚀 Quick Start

### Prerequisites

```bash
pip install langgraph-viz
```

### Running an Example

```bash
cd examples
python chatbot_memory.py
```

The visualization server will start automatically and open in your browser at `http://localhost:8765`.

## 📖 Detailed Examples

### Basic Example

**File:** `basic_example.py`

**What it demonstrates:**
- Simple conditional routing based on query content
- Weather, math, and general response handlers
- Basic state management with TypedDict
- Conditional edges for dynamic routing

**How to run:**
```bash
python examples/basic_example.py
```

**What to look for in visualization:**
- See how different queries route to different nodes
- Watch the router node make decisions
- Observe state changes in the inspector

---

### Chatbot with Memory

**File:** `chatbot_memory.py`

**What it demonstrates:**
- Persistent conversation state using `MemorySaver`
- Multi-turn conversations with state accumulation
- Name detection and context tracking
- How conversation history builds up over time

**How to run:**
```bash
python examples/chatbot_memory.py
```

**What to look for in visualization:**
- Notice how `messages` list grows with each turn
- See `user_name` and `context` being updated
- Watch `turn_count` increment
- Observe how the same `thread_id` maintains conversation state

**Key code snippet:**
```python
# Use consistent thread_id to maintain conversation
config = {"configurable": {"thread_id": "chat-demo-001"}}

# State accumulates across invocations
for user_msg in conversation:
    viz_app.stream({"messages": [{"role": "user", "content": user_msg}]}, config)
```

---

### Multi-Agent Research

**File:** `multi_agent_research.py`

**What it demonstrates:**
- Supervisor pattern coordinating specialized agents
- Dynamic agent selection based on workflow state
- Research → Summarization → Fact-checking pipeline
- Collaborative multi-agent workflow

**How to run:**
```bash
python examples/multi_agent_research.py
```

**What to look for in visualization:**
- Watch the supervisor make routing decisions
- See different agents activate based on supervisor's choice
- Notice the loop back to supervisor after each agent
- Observe how each agent contributes to the final report

**Key code snippet:**
```python
# Supervisor routes to different agents dynamically
workflow.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "researcher": "researcher",
        "summarizer": "summarizer",
        "fact_checker": "fact_checker",
        "finish": "compiler",
    }
)

# Agents return to supervisor for next decision
workflow.add_edge("researcher", "supervisor")
```

---

### RAG Pipeline

**File:** `rag_pipeline.py`

**What it demonstrates:**
- Query analysis and rewriting
- Document retrieval from mock knowledge base
- Relevance checking with quality scoring
- Self-correcting loop: re-retrieves if relevance is low
- Context-aware answer generation

**How to run:**
```bash
python examples/rag_pipeline.py
```

**What to look for in visualization:**
- See query analysis transform the original query
- Watch retrieval attempts in timeline
- Notice the conditional loop when relevance is low
- Observe how the pipeline self-corrects

**Key code snippet:**
```python
# Self-correcting loop based on relevance
def should_reretrieve(state: RAGState) -> str:
    if state.get("needs_reretrieval", False):
        return "retrieve"  # Loop back
    else:
        return "generate"  # Proceed

workflow.add_conditional_edges(
    "check_relevance",
    should_reretrieve,
    {
        "retrieve": "retrieve_documents",  # Re-retrieve
        "generate": "generate_answer",     # Continue
    }
)
```

---

### Human-in-the-Loop

**File:** `human_in_loop.py`

**What it demonstrates:**
- Multiple approval checkpoints in workflow
- Conditional approval loops (production needs 2 approvals)
- Deployment pipeline with tests and verification
- Simulated human approval (auto-approves for demo)

**How to run:**
```bash
python examples/human_in_loop.py
```

**What to look for in visualization:**
- See approval nodes in the timeline
- Watch the loop when multiple approvals needed
- Notice how state preserves approval feedback
- Observe sequential approval checkpoints

**Key patterns:**
```python
# In production, you would use interrupts:
# interrupt("approval_needed")

# Conditional loop for multiple approvals
def needs_more_approvals(state) -> str:
    if state["approvals_received"] < state["approvals_required"]:
        return "request_more"  # Loop back
    return "proceed"
```

---

### Tool-Calling Agent

**File:** `tool_calling_agent.py`

**What it demonstrates:**
- Dynamic tool selection based on query analysis
- Multiple tools: calculator, web search, datetime, file analyzer, unit converter
- Tool invocation and result processing
- Multi-tool workflows for complex requests

**How to run:**
```bash
python examples/tool_calling_agent.py
```

**What to look for in visualization:**
- See how analyzer selects appropriate tools
- Watch different tools execute for different queries
- Notice tool results accumulating in state
- Observe how results are synthesized into final answer

**Available tools:**
- `calculator` - Math expressions
- `web_search` - Information retrieval (mocked)
- `datetime_tool` - Date/time operations
- `file_analyzer` - File property analysis
- `unit_converter` - Unit conversions

---

### Hierarchical Workflow

**File:** `hierarchical_workflow.py`

**What it demonstrates:**
- Main pipeline with embedded subgraphs
- Processing subgraph (clean → transform)
- Analysis subgraph (statistics → insights)
- Modular workflow composition
- Data flowing between parent and child graphs

**How to run:**
```bash
python examples/hierarchical_workflow.py
```

**What to look for in visualization:**
- See main pipeline nodes invoking subgraphs
- Watch processing and analysis subgraphs execute
- Notice how state flows between levels
- Observe the modular, reusable design pattern

**Key code snippet:**
```python
# Create subgraphs
processing_graph = create_processing_subgraph()
analysis_graph = create_analysis_subgraph()

# Main pipeline invokes subgraphs
def run_processing_pipeline(state):
    processing_input = {"raw_data": state["input_data"]}
    result = processing_graph.invoke(processing_input)
    state["processed_data"] = result["transformed_data"]
    return state
```

---

## 🎯 Common Patterns

### Using Checkpointers

All examples use `MemorySaver` for state persistence:

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
```

This enables:
- State persistence across invocations
- Time-travel debugging
- Conversation history
- Workflow resumption

### State Management

Define state with `TypedDict` for type safety:

```python
from typing import TypedDict, List

class MyState(TypedDict):
    messages: List[str]
    counter: int
    result: str
```

### Conditional Edges

Route dynamically based on state:

```python
def router(state: MyState) -> str:
    if state["counter"] > 5:
        return "finish"
    return "continue"

workflow.add_conditional_edges(
    "node_name",
    router,
    {
        "finish": END,
        "continue": "next_node"
    }
)
```

### Visualization Best Practices

1. **Use descriptive node names** - Shows clearly in graph
2. **Add print statements** - Creates execution narrative
3. **Update state incrementally** - Shows progression visually
4. **Use thread_id consistently** - For conversation flows
5. **Add delays between runs** - Easier to observe in visualizer

## 🔧 Customization

### Change Port

**Running multiple visualizers:** If you have multiple LangGraph workflows, you can run visualizers on different ports simultaneously:

```python
# Visualizer 1
with visualize(app1, port=8765) as viz_app1:
    # Your first workflow
    
# Visualizer 2  
with visualize(app2, port=8766) as viz_app2:
    # Your second workflow
```

Each visualizer will open in a separate browser tab on its respective port. The frontend automatically connects to the correct port.

### Disable Auto-Open Browser

```python
with visualize(app, auto_open=False) as viz_app:
    # Manually visit http://localhost:8765
```

### Keep Server Running

```python
with visualize(app) as viz_app:
    # Run your workflow
    result = viz_app.invoke({"query": "test"})
    
    # Keep inspecting
    import time
    while True:
        time.sleep(1)  # Press Ctrl+C to exit
```

## 🐛 Troubleshooting

### Browser doesn't open

- Check if port 8765 is available
- Try a different port: `visualize(app, port=8766)`
- Manually navigate to `http://localhost:8765`

### Graph doesn't display

- Ensure your workflow is compiled: `app = workflow.compile()`
- Check that nodes and edges are properly defined
- Look for errors in the console output

### State not updating

- Verify you're using the same `thread_id` for related invocations
- Check that nodes are returning modified state
- Ensure checkpointer is configured: `workflow.compile(checkpointer=memory)`

### Events not showing in timeline

- Internal nodes (`__start__`, `__end__`) are filtered automatically
- Ensure your nodes are completing successfully
- Check for exceptions in node functions

## 📚 Next Steps

1. **Explore the code** - Each example is well-documented
2. **Modify examples** - Try changing the workflows
3. **Build your own** - Use examples as templates
4. **Read LangGraph docs** - [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
5. **Check out LangChain** - [LangChain Documentation](https://python.langchain.com/)

## 💬 Community

- **Issues**: [GitHub Issues](https://github.com/mk-tdev/langgraph-viz/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mk-tdev/langgraph-viz/discussions)
- **PyPI**: [langgraph-viz](https://pypi.org/project/langgraph-viz/)

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

**Happy Visualizing! 🎨**
