"""TypedDict definitions for MuseScore MCP action sequences."""

from typing import Dict, Any, List, TypedDict


class ActionSequenceItem(TypedDict):
    """A single action in a sequence."""
    action: str
    params: Dict[str, Any]


ActionSequence = List[ActionSequenceItem]