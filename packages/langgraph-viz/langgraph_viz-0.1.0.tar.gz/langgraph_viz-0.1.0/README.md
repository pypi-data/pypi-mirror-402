# LangGraph Viz

**Real-time browser-based visualization for LangGraph workflows.**

Debug and understand your LangGraph agents with live state inspection, graph visualization, and execution timeline.

![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- 🔴 **Live Graph Visualization** - See your workflow graph with real-time node highlighting
- 📊 **State Inspector** - View full state and diffs at each execution step
- ⏱️ **Event Timeline** - Scrub through execution history with playback controls
- 🔌 **Zero Config** - Works with any compiled LangGraph app
- 🚀 **Minimal Overhead** - Designed for development debugging

## Installation

```bash
pip install langgraph-viz
```

## Quick Start

```python
from langgraph_viz import visualize
from your_app import app  # Your compiled LangGraph

# Context manager style - auto opens browser
with visualize(app) as viz_app:
    result = viz_app.invoke({"query": "Hello world"})

# Or start server manually
viz = visualize(app, auto_open=False)
viz.server.start()
# ... run your app ...
viz.server.stop()
```

Open `http://localhost:8765` to see the visualization.

## How It Works

1. **Wrap your app** - `visualize()` wraps your LangGraph app to intercept execution events
2. **Start the server** - A FastAPI server streams events via WebSocket
3. **View in browser** - A React frontend renders the graph, timeline, and state

## Configuration

```python
visualize(
    app,
    port=8765,           # Server port (default: 8765)
    auto_open=True,      # Auto-open browser (default: True)
)
```

## Requirements

- Python 3.9+
- LangGraph >= 0.0.1
- A modern web browser

## Development

```bash
# Clone the repo
git clone https://github.com/yourusername/langgraph-viz.git
cd langgraph-viz

# Install dev dependencies
pip install -e ".[dev]"

# Build frontend (requires Node.js)
cd frontend && npm install && npm run build && cd ..

# Run tests
pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.
