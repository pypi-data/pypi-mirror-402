"""Main wrapper for LangGraph visualization."""

import webbrowser
import inspect
from typing import Any, Optional, Callable

from .state_tracker import StateTracker, CaptureConfig
from .event_collector import EventCollector
from .server import VisualizerServer


class WrappedApp:
    """Wrapper around LangGraph app that intercepts execution."""

    def __init__(self, app: Any, state_tracker: StateTracker):
        """
        Initialize wrapped app.
        
        Args:
            app: Original LangGraph app
            state_tracker: StateTracker instance
        """
        self.app = app
        self.state_tracker = state_tracker
        self.event_collector = EventCollector(
            on_event=lambda event: state_tracker.update(event)
        )
        
        # Wrap methods
        self._wrap_methods()

    def _wrap_methods(self):
        """Wrap app methods to intercept events."""
        # Wrap stream
        if hasattr(self.app, "stream"):
            original_stream = self.app.stream
            if inspect.iscoroutinefunction(original_stream):
                self.stream = self.event_collector.wrap_async_stream(original_stream)
            else:
                self.stream = self.event_collector.wrap_stream(original_stream)
        
        # Wrap invoke using stream to capture events if possible
        if hasattr(self.app, "invoke"):
            # If we have stream, use it to emulate invoke with events
            if hasattr(self.app, "stream"):
                self.invoke = self._create_streaming_invoke(self.app.stream, self.app.invoke)
            else:
                original_invoke = self.app.invoke
                if inspect.iscoroutinefunction(original_invoke):
                    self.invoke = self.event_collector.wrap_async_invoke(original_invoke)
                else:
                    self.invoke = self.event_collector.wrap_invoke(original_invoke)
        
        # Wrap astream (async stream)
        if hasattr(self.app, "astream"):
            self.astream = self.event_collector.wrap_async_stream(self.app.astream)
        
        # Wrap ainvoke (async invoke)
        if hasattr(self.app, "ainvoke"):
            # If we have astream, use it
            if hasattr(self.app, "astream"):
                self.ainvoke = self._create_async_streaming_invoke(self.app.astream, self.app.ainvoke)
            else:
                self.ainvoke = self.event_collector.wrap_async_invoke(self.app.ainvoke)

    def _create_streaming_invoke(self, stream_fn: Callable, original_invoke: Callable) -> Callable:
        """Create an invoke wrapper that consumes stream events."""
        def wrapped_invoke(input: Any, config: Optional[dict] = None, **kwargs) -> Any:
            # We must use the original invoke to ensure identical return values and behavior
            # (e.g. state persistence, side effects that might rely on invoke paths).
            # However, we ALSO want events. 
            
            # Constraint: We need (1) Node Names (from 'updates') and (2) Full State (from 'values').
            # We also need to return the FINAL Full State (raw dict/object) to the caller.
            
            # Force dual-mode streaming
            # Note: We prioritize kwargs entries if present, but we override stream_mode
            kwargs["stream_mode"] = ["updates", "values"]
            
            iterator = stream_fn(input, config, **kwargs)
            
            current_node = "__start__"
            final_state = None
            
            import time
            
            for chunk in iterator:
                # Chunk is (mode, data)
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    mode, data = chunk
                    
                    if mode == "updates":
                        # data is {"node_name": output}
                        # Capture the node name for the NEXT values event
                        if isinstance(data, dict) and data:
                            # Typically implies the node that just finished
                            current_node = list(data.keys())[0]
                            
                    elif mode == "values":
                        # data is the Full State
                        final_state = data
                        
                        # Emit event
                        # We construct the event manually to ensure it has the full state in the 'output' field
                        # which _extract_state expects.
                        event = {
                            "type": "on_chain_end",
                            "node": current_node,
                            "data": {"output": data}, # 'output' is the full state dict
                            "timestamp": time.time(),
                        }
                        
                        # Direct update to state tracker
                        self.state_tracker.update(event)
                        
                        # Note: current_node stays as is until next 'updates' changes it.
                        # This implies 'values' immediately follows 'updates'.
                        # For the initial value (start), current_node is "__start__".
                else:
                    # Fallback for unexpected chunk format
                    pass

            # Return the final state raw object (usually a dict from 'values')
            # This restores behavior compatibility with app.invoke()
            return final_state

        return wrapped_invoke

    def _create_async_streaming_invoke(self, astream_fn: Callable, original_ainvoke: Callable) -> Callable:
        """Create an async invoke wrapper that consumes stream events."""
        async def wrapped_ainvoke(input: Any, config: Optional[dict] = None, **kwargs) -> Any:
            async for chunk in astream_fn(input, config, **kwargs):
                 event = self.event_collector._normalize_event(chunk)
                 if event:
                     self.event_collector.on_event(event)
            
            return self.state_tracker.current_state

        return wrapped_ainvoke

    def __getattr__(self, name: str):
        """Proxy unknown attributes to original app."""
        return getattr(self.app, name)


class GraphVisualizer:
    """Context manager and decorator for visualizing LangGraph execution."""

    def __init__(
        self,
        app: Any,
        port: int = 8765,
        auto_open: bool = True,
        capture_config: Optional[CaptureConfig] = None,
    ):
        """
        Initialize GraphVisualizer.
        
        Args:
            app: Compiled LangGraph app
            port: Port for visualization server (default: 8765)
            auto_open: Auto-open browser window (default: True)
            capture_config: State capture configuration
        """
        self.app = app
        self.port = port
        self.auto_open = auto_open
        self.state_tracker = StateTracker(capture_config or CaptureConfig())
        self.server = VisualizerServer(self.app, self.port, self.state_tracker)
        self.wrapped_app: Optional[WrappedApp] = None

    def __enter__(self):
        """Enter context manager - start server and wrap app."""
        # Start server
        self.server.start()
        
        # Open browser
        if self.auto_open:
            try:
                webbrowser.open(f"http://localhost:{self.port}")
            except Exception as e:
                print(f"Could not auto-open browser: {e}")
                print(f"Please open http://localhost:{self.port} manually")
        
        # Wrap app
        self.wrapped_app = WrappedApp(self.app, self.state_tracker)
        return self.wrapped_app

    def __exit__(self, *args):
        """Exit context manager - stop server."""
        self.server.stop()

    def wrap(self):
        """
        Wrap app without context manager (decorator pattern).
        
        Returns:
            Wrapped app with visualization enabled
        """
        # Start server
        self.server.start()
        
        # Open browser
        if self.auto_open:
            try:
                webbrowser.open(f"http://localhost:{self.port}")
            except Exception as e:
                print(f"Could not auto-open browser: {e}")
                print(f"Please open http://localhost:{self.port} manually")
        
        # Wrap and return
        self.wrapped_app = WrappedApp(self.app, self.state_tracker)
        return self.wrapped_app



def visualize(
    app: Any,
    port: int = 8765,
    auto_open: bool = True,
    capture_config: Optional[CaptureConfig] = None,
) -> GraphVisualizer:
    """
    Convenience function to create a GraphVisualizer.
    
    Args:
        app: Compiled LangGraph app
        port: Port for visualization server (default: 8765)
        auto_open: Auto-open browser window (default: True)
        capture_config: State capture configuration
        
    Returns:
        GraphVisualizer instance
        
    Usage:
        # Context manager style
        with visualize(app) as viz_app:
            viz_app.stream({"query": "test"})
        
        # Decorator style
        viz = visualize(app)
        viz_app = viz.wrap()
        viz_app.stream({"query": "test"})
    """
    return GraphVisualizer(app, port, auto_open, capture_config)
