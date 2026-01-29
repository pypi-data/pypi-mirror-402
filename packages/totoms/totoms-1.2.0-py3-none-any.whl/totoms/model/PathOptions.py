"""
Path options for configuring API endpoints.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PathOptions:
    """
    Options to configure an API path.
    
    Attributes:
        content_type: The Content-Type header to include in the response (optional)
        no_auth: Whether to skip authentication validation for this path (default: False)
        ignore_base_path: Whether to ignore the base path configuration for this path (default: False)
    """
    content_type: Optional[str] = None
    no_auth: bool = False
    ignore_base_path: bool = False
