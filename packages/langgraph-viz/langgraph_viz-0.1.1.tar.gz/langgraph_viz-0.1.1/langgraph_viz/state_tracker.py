"""State tracking and diff computation for LangGraph execution."""

import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from deepdiff import DeepDiff

from .serializer import StateSerializer


@dataclass
class StateSnapshot:
    """Represents a snapshot of state at a specific point in execution."""

    timestamp: float
    node: str
    state: Dict[str, Any]
    diff: Optional[Dict[str, Any]] = None
    event_type: str = "state_update"


@dataclass
class CaptureConfig:
    """Configuration for state capture behavior."""

    include_private: bool = False
    max_depth: int = 10
    exclude_keys: List[str] = None

    def __post_init__(self):
        if self.exclude_keys is None:
            self.exclude_keys = []


class StateTracker:
    """Tracks state evolution and computes diffs between states."""

    def __init__(self, capture_config: Optional[CaptureConfig] = None):
        """
        Initialize StateTracker.
        
        Args:
            capture_config: Configuration for state capture
        """
        self.history: List[StateSnapshot] = []
        self.current_state: Dict[str, Any] = {}
        self.config = capture_config or CaptureConfig()
        self.subscribers: List[Callable[[StateSnapshot], None]] = []
        self.serializer = StateSerializer()

    def update(self, event: Dict[str, Any]) -> Optional[StateSnapshot]:
        """
        Update state based on a LangGraph event.
        
        Args:
            event: Event from LangGraph execution
            
        Returns:
            StateSnapshot if state changed, None otherwise
        """
        # Extract state from event based on event type
        new_state = self._extract_state(event)
        
        if new_state is None:
            return None

        # Serialize the state
        serialized_state = self.serializer.serialize(new_state)

        # Compute diff from previous state
        diff = self._compute_diff(self.current_state, serialized_state)

        # Create snapshot
        snapshot = StateSnapshot(
            timestamp=event.get("timestamp", time.time()),
            node=event.get("node", "unknown"),
            state=serialized_state,
            diff=diff,
            event_type=event.get("type", "state_update"),
        )

        # Update tracking
        self.history.append(snapshot)
        self.current_state = serialized_state

        # Notify subscribers
        self._notify_subscribers(snapshot)

        return snapshot

    def _extract_state(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract state from event based on event type."""
        # Handle different LangGraph event types
        if event.get("type") == "on_chain_end":
            if "data" in event and "output" in event["data"]:
                return event["data"]["output"]
        
        # Handle stream events
        if "data" in event:
            data = event["data"]
            if isinstance(data, dict):
                # Look for state-like structures
                if "state" in data:
                    return data["state"]
                # Return the data itself if it looks like state
                return data
        
        return None

    def _compute_diff(
        self, old_state: Dict[str, Any], new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute diff between old and new state.
        
        Args:
            old_state: Previous state
            new_state: New state
            
        Returns:
            Dictionary with added, removed, and modified keys
        """
        if not old_state:
            # If new_state is a dict, get keys
            if isinstance(new_state, dict):
                return {
                    "added": list(new_state.keys()),
                    "removed": [],
                    "modified": {},
                }
            # If new_state is a list/other, defer to DeepDiff or mark as modified/added
            # Actually simplest is to fallback to DeepDiff if it's not a dict,
            # or treat the whole thing as an addition/change?
            # DeepDiff handles empty old_state gracefully.
            pass

        diff = DeepDiff(
            old_state,
            new_state,
            ignore_order=True,
            report_repetition=True,
            view="tree",
        )

        result = {"added": [], "removed": [], "modified": {}}

        # Extract added items
        if "dictionary_item_added" in diff:
            for item in diff["dictionary_item_added"]:
                path = str(item.path(output_format="list"))
                result["added"].append(path)
        if "iterable_item_added" in diff:
            for item in diff["iterable_item_added"]:
                path = str(item.path(output_format="list"))
                result["added"].append(path)

        # Extract removed items
        if "dictionary_item_removed" in diff:
            for item in diff["dictionary_item_removed"]:
                path = str(item.path(output_format="list"))
                result["removed"].append(path)
        if "iterable_item_removed" in diff:
            for item in diff["iterable_item_removed"]:
                path = str(item.path(output_format="list"))
                result["removed"].append(path)

        # Extract modified items
        if "values_changed" in diff:
            for item in diff["values_changed"]:
                path = str(item.path(output_format="list"))
                result["modified"][path] = {
                    "old": item.t1,
                    "new": item.t2,
                }

        return result

    def subscribe(self, callback: Callable[[StateSnapshot], None]) -> None:
        """
        Subscribe to state updates.
        
        Args:
            callback: Function to call on state updates
        """
        self.subscribers.append(callback)

    def _notify_subscribers(self, snapshot: StateSnapshot) -> None:
        """Notify all subscribers of a state update."""
        for callback in self.subscribers:
            try:
                callback(snapshot)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get serialized history for transmission.
        
        Returns:
            List of snapshot dictionaries
        """
        return [
            {
                "timestamp": snap.timestamp,
                "node": snap.node,
                "state": snap.state,
                "diff": snap.diff,
                "event_type": snap.event_type,
            }
            for snap in self.history
        ]

    def reset(self) -> None:
        """Reset tracker state."""
        self.history.clear()
        self.current_state = {}
