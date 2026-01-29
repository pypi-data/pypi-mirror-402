"""Utility functions for mission handling."""

from __future__ import annotations

from typing import Optional, Tuple


def extract_src_ids(msg) -> Tuple[Optional[int], Optional[int]]:
    """Extract source system and component IDs from MAVLink message.
    
    Args:
        msg: MAVLink message
        
    Returns:
        Tuple of (system_id, component_id)
    """
    sys_id = None
    comp_id = None
    
    # Try get_srcSystem() method
    getter = getattr(msg, "get_srcSystem", None)
    if callable(getter):
        try:
            sys_id = getter()
        except Exception:
            sys_id = None
    
    # Try get_srcComponent() method
    getter = getattr(msg, "get_srcComponent", None)
    if callable(getter):
        try:
            comp_id = getter()
        except Exception:
            comp_id = None
    
    # Fallback to _header attribute
    header = getattr(msg, "_header", None)
    if sys_id is None and header is not None:
        sys_id = getattr(header, "srcSystem", None)
    if comp_id is None and header is not None:
        comp_id = getattr(header, "srcComponent", None)
    
    return sys_id, comp_id
