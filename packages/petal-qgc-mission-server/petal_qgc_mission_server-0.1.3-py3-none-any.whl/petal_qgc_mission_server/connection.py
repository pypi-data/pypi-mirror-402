"""MAVLink connection wrapper using MavLinkExternalProxy."""

from __future__ import annotations

import logging
import queue
from typing import Any, Dict, Optional

from . import logger

try:
    from pymavlink import mavutil
    from pymavlink.dialects.v20 import common
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed to run the simulator") from exc

from petal_app_manager.proxies.external import MavLinkExternalProxy


class MavlinkConnection:
    """Wrapper that uses MavLinkExternalProxy for MAVLink communication."""

    def __init__(
        self,
        mavlink_proxy: MavLinkExternalProxy,
        *,
        system_id: int = 1,
        component_id: int = 1,
        message_filter: Optional[set[str]] = None,
    ):
        """Initialize MAVLink connection.
        
        Args:
            mavlink_proxy: The MavLinkExternalProxy instance
            system_id: MAVLink system ID
            component_id: MAVLink component ID
            message_filter: Optional set of message types to filter (only these will be queued)
        """
        self.source_system = system_id
        self.source_component = component_id
        if mavlink_proxy is None:
            raise RuntimeError("MavLinkExternalProxy is required for MAVLink communication.")
        self.mavlink_proxy = mavlink_proxy
        self._handler_key = "mav"
        self._inbound_messages: queue.Queue[Any] = queue.Queue()
        self._message_filter = message_filter
        
        # Message statistics
        self._stats = {
            'received': 0,
            'queued': 0,
            'discarded': 0,
        }
        
        # Create a MAVLink instance for message encoding
        self.mav = common.MAVLink(None)
        self.mav.srcSystem = self.source_system
        self.mav.srcComponent = self.source_component
        self.connection_label = "external_proxy"
        logger.info("Using MavLinkExternalProxy for MAVLink communication")
        
        # Register single handler for all MAVLink messages
        self.mavlink_proxy.register_handler(self._handler_key, self._handle_inbound_message)

    def send_message(self, msg: Any) -> None:
        """Send a MAVLink message.
        
        Args:
            msg: The MAVLink message to send
        """
        try:
            self.mavlink_proxy.send("mav", msg)
            if logger.isEnabledFor(logging.DEBUG):
                msg_type = getattr(msg, "get_type", lambda: None)()
                if msg_type:
                    logger.debug(f"Sent {msg_type}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def _handle_inbound_message(self, msg: Any) -> None:
        """Handle inbound MAVLink messages with optional filtering.
        
        Args:
            msg: The received MAVLink message
        """
        self._stats['received'] += 1
        try:
            # Get message type
            msg_type = getattr(msg, 'get_type', lambda: None)()
            
            # Filter: only queue messages in the filter set (if provided)
            if self._message_filter is None or msg_type in self._message_filter:
                self._inbound_messages.put_nowait(msg)
                self._stats['queued'] += 1
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Queued {msg_type}")
            else:
                self._stats['discarded'] += 1
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Discarded {msg_type} (not in filter)")
        except Exception as exc:
            logger.warning("Failed to process inbound MAVLink message: %s", exc)

    def receive_message(self, blocking: bool = False, timeout: Optional[float] = None):
        """Receive a MAVLink message from the queue.
        
        Args:
            blocking: If True, block until a message is available
            timeout: Optional timeout in seconds (only used if blocking=True)
            
        Returns:
            The received message, or None if no message available
        """
        try:
            if blocking:
                if timeout is None:
                    return self._inbound_messages.get()
                return self._inbound_messages.get(timeout=timeout)
            return self._inbound_messages.get_nowait()
        except queue.Empty:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get message statistics.
        
        Returns:
            Dictionary with message statistics
        """
        return self._stats.copy()
    
    def close(self) -> None:
        """Close the connection and unregister handlers."""
        try:
            self.mavlink_proxy.unregister_handler(self._handler_key, self._handle_inbound_message)
        except Exception:
            logger.info("Handler already unregistered or proxy unavailable for MAVLink connection close")
