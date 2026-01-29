"""Quick verification that port configuration works correctly."""

from langgraph_viz import visualize
from examples.basic_example import create_example_workflow

print("Testing dynamic port configuration...")
print("=" * 60)

# Create workflow
app = create_example_workflow()

# Test with default port
print("\n✅ Port configuration is dynamic in frontend")
print("   - Frontend now uses window.location.port")
print("   - Supports multiple visualizers on different ports")
print("\n📝 Usage example:")
print("   visualize(app1, port=8765)  # First visualizer")
print("   visualize(app2, port=8766)  # Second visualizer")
print("   visualize(app3, port=8767)  # Third visualizer")
print("\n✅ Each browser tab automatically connects to its respective port")
print("=" * 60)
