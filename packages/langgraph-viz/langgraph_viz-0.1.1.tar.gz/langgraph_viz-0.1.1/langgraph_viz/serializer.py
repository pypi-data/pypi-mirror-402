"""State serialization utilities for LangGraph states."""

import json
from dataclasses import is_dataclass, asdict
from typing import Any, Dict
from datetime import datetime
from enum import Enum


class StateSerializer:
    """Serializes LangGraph state objects to JSON-safe format."""

    def serialize(self, state: Any) -> Any:
        """
        Recursively serialize state to JSON-safe format.
        
        Args:
            state: State object to serialize
            
        Returns:
            JSON-serializable representation
        """
        # Handle None
        if state is None:
            return None

        # Handle primitive types
        if isinstance(state, (str, int, float, bool)):
            return state

        # Handle datetime
        if isinstance(state, datetime):
            return state.isoformat()

        # Handle enums
        if isinstance(state, Enum):
            return state.value

        # Handle LangChain message objects specially
        if hasattr(state, "__class__") and state.__class__.__module__.startswith("langchain"):
            # Check if it's a message object
            if hasattr(state, "type"):
                msg_dict = {}
                
                # Get message type
                msg_dict["type"] = state.type
                
                # Get content (may be empty for tool calls)
                if hasattr(state, "content"):
                    msg_dict["content"] = state.content
                
                # Handle tool calls (AIMessage with tool_calls)
                if hasattr(state, "tool_calls") and state.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "name": tc.get("name", "unknown"),
                            "args": tc.get("args", {}),
                            "id": tc.get("id", "")
                        }
                        for tc in state.tool_calls
                    ]
                
                # Handle tool messages (ToolMessage)
                if state.type == "tool":
                    if hasattr(state, "name"):
                        msg_dict["tool_name"] = state.name
                    if hasattr(state, "tool_call_id"):
                        msg_dict["tool_call_id"] = state.tool_call_id
                
                # Handle additional kwargs
                if hasattr(state, "additional_kwargs") and state.additional_kwargs:
                    msg_dict["additional_kwargs"] = self.serialize(state.additional_kwargs)
                
                return msg_dict
        
        # Handle Pydantic models
        if hasattr(state, "model_dump"):
            return self.serialize(state.model_dump())

        # Handle dataclasses
        if is_dataclass(state):
            return self.serialize(asdict(state))

        # Handle dictionaries
        if isinstance(state, dict):
            return {str(k): self.serialize(v) for k, v in state.items()}

        # Handle lists and tuples
        if isinstance(state, (list, tuple)):
            return [self.serialize(item) for item in state]

        # Handle sets
        if isinstance(state, set):
            return [self.serialize(item) for item in state]

        # Fallback to string representation for unknown types
        try:
            return str(state)
        except Exception:
            return f"<{type(state).__name__}>"

    def to_json(self, state: Any) -> str:
        """
        Serialize state and convert to JSON string.
        
        Args:
            state: State object to serialize
            
        Returns:
            JSON string representation
        """
        serialized = self.serialize(state)
        return json.dumps(serialized, indent=2)
