"""Event collection and normalization for LangGraph execution."""

import time
from typing import Any, Dict, Callable, AsyncIterator, Iterator
from collections.abc import AsyncIterator as AsyncIteratorType


class EventCollector:
    """Intercepts and normalizes LangGraph events."""

    def __init__(self, on_event: Callable[[Dict[str, Any]], None]):
        """
        Initialize EventCollector.
        
        Args:
            on_event: Callback for normalized events
        """
        self.on_event = on_event

    def wrap_stream(self, original_stream_fn: Callable) -> Callable:
        """
        Wrap a stream function to intercept events.
        
        Args:
            original_stream_fn: Original stream function
            
        Returns:
            Wrapped stream function
        """

        def wrapped_stream(*args, **kwargs):
            """Synchronous stream wrapper."""
            for chunk in original_stream_fn(*args, **kwargs):
                # Normalize and emit event
                event = self._normalize_event(chunk)
                if event:
                    self.on_event(event)
                
                # Pass through original chunk
                yield chunk

        return wrapped_stream

    def wrap_async_stream(self, original_stream_fn: Callable) -> Callable:
        """
        Wrap an async stream function to intercept events.
        
        Args:
            original_stream_fn: Original async stream function
            
        Returns:
            Wrapped async stream function
        """

        async def wrapped_stream(*args, **kwargs):
            """Asynchronous stream wrapper."""
            async for chunk in original_stream_fn(*args, **kwargs):
                # Normalize and emit event
                event = self._normalize_event(chunk)
                if event:
                    self.on_event(event)
                
                # Pass through original chunk
                yield chunk

        return wrapped_stream

    def wrap_invoke(self, original_invoke_fn: Callable) -> Callable:
        """
        Wrap an invoke function to capture final state.
        
        Args:
            original_invoke_fn: Original invoke function
            
        Returns:
            Wrapped invoke function
        """

        def wrapped_invoke(*args, **kwargs):
            """Synchronous invoke wrapper."""
            result = original_invoke_fn(*args, **kwargs)
            
            # Emit final state event
            event = {
                "type": "on_chain_end",
                "node": "final",
                "data": {"output": result},
                "timestamp": time.time(),
            }
            self.on_event(event)
            
            return result

        return wrapped_invoke

    def wrap_async_invoke(self, original_invoke_fn: Callable) -> Callable:
        """
        Wrap an async invoke function to capture final state.
        
        Args:
            original_invoke_fn: Original async invoke function
            
        Returns:
            Wrapped async invoke function
        """

        async def wrapped_invoke(*args, **kwargs):
            """Asynchronous invoke wrapper."""
            result = await original_invoke_fn(*args, **kwargs)
            
            # Emit final state event
            event = {
                "type": "on_chain_end",
                "node": "final",
                "data": {"output": result},
                "timestamp": time.time(),
            }
            self.on_event(event)
            
            return result

        return wrapped_invoke

    def _normalize_event(self, chunk: Any) -> Dict[str, Any]:
        """
        Normalize a LangGraph event to standard format.
        
        Args:
            chunk: Raw event from LangGraph
            
        Returns:
            Normalized event dictionary
        """
        # Handle tuple format (node_name, data) - most common in LangGraph streams
        if isinstance(chunk, tuple) and len(chunk) == 2:
            node_name, data = chunk
            return {
                "type": "on_chain_end",
                "node": str(node_name),
                "data": {"output": data},
                "timestamp": time.time(),
            }
        
        # Handle dict format with node as key
        if isinstance(chunk, dict):
            # Standard LangGraph event format
            if "event" in chunk or "name" in chunk:
                return {
                    "type": chunk.get("event", "unknown"),
                    "node": chunk.get("name", "unknown"),
                    "data": chunk.get("data", {}),
                    "timestamp": chunk.get("timestamp", time.time()),
                }
            
            # Simple dict format where key is the node name
            # e.g., {"router": {...state...}}
            if len(chunk) == 1:
                node_name = list(chunk.keys())[0]
                node_data = chunk[node_name]
                return {
                    "type": "on_chain_end",
                    "node": node_name,
                    "data": {"output": node_data},
                    "timestamp": time.time(),
                }
        
        # Handle list format (common in MessageGraph or when multiple outputs)
        if isinstance(chunk, list):
             return {
                "type": "on_chain_end",
                "node": "unknown", # Hard to map to a node if it's just a list
                "data": {"output": chunk},
                "timestamp": time.time(),
            }
        
        # Fallback for unknown formats
        return {
            "type": "unknown",
            "node": "unknown",
            "data": {"raw": str(chunk)},
            "timestamp": time.time(),
        }

    def emit(self, event: Dict[str, Any]) -> None:
        """
        Manually emit an event.
        
        Args:
            event: Event to emit
        """
        self.on_event(event)
