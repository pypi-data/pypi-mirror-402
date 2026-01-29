"""Example using user's existing workflow."""

import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.graph import create_workflow
from langgraph_viz import visualize


if __name__ == "__main__":
    print("=" * 60)
    print("Visualizing Your Existing Workflow")
    print("=" * 60)
    
    # Create your existing workflow
    app = create_workflow()
    
    print("\n🎨 Starting visualization server...")
    print("📊 Browser will open on port 8766")
    print("💡 Using different port to support multiple visualizers\n")
    
    # Visualize it! Using port 8766 to avoid conflicts with other examples
    with visualize(app, port=8766) as viz_app:
        # Example query
        query = "Create a simple Python calculator app"
        
        print(f"Query: {query}\n")
        
        config = {"configurable": {"thread_id": "viz-test"}}
        
        # Stream execution
        for event in viz_app.stream({"query": query}, config):
            print(f"Event: {event}")
        
        # Keep server running for inspection
        print("\n✓ Execution complete. Server still running...")
        print("Press Ctrl+C to exit")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
    
    print("\n✓ Visualization complete!")
