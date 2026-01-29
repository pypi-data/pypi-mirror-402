"""
Configuration options for TotoAPIController.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class APIControllerOptions:
    """
    Configuration options for the TotoAPIController.
    
    Attributes:
        debug_mode: Whether to enable debug logging (default: False)
        base_path: Base path to prepend to all API paths, e.g., '/api/v1' (default: None)
        port: Port on which the Flask app will listen (default: 8080)
    """
    debug_mode: bool = False
    base_path: Optional[str] = None
    port: int = 8080
