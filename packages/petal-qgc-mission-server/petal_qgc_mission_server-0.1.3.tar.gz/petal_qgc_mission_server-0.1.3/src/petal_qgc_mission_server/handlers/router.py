"""Message router for MAVLink messages."""

from __future__ import annotations

from typing import Any, Callable, Dict

from .. import logger


class MessageRouter:
    """Route MAVLink messages to appropriate handlers."""
    
    def __init__(self):
        """Initialize message router."""
        self._handlers: Dict[str, Callable] = {}
    
    def register(self, msg_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type.
        
        Args:
            msg_type: The message type (e.g., 'HEARTBEAT', 'MISSION_COUNT')
            handler: The handler function to call
        """
        self._handlers[msg_type] = handler
    
    def route(self, msg) -> bool:
        """Route a message to its handler.
        
        Args:
            msg: The MAVLink message
            
        Returns:
            True if handled, False otherwise
        """
        try:
            msg_type = msg.get_type()
        except Exception:
            return False
        
        handler = self._handlers.get(msg_type)
        if handler:
            try:
                handler(msg)
                return True
            except Exception:
                logger.exception(f"Error handling message type {msg_type}")
                return False
        return False
    
    def get_handled_message_types(self) -> set[str]:
        """Get the set of message types that are handled.
        
        Returns:
            Set of message type names
        """
        return set(self._handlers.keys())
