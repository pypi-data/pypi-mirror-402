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
