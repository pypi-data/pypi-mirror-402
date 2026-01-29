"""
Configuration properties for TotoAPIController.
"""
from dataclasses import dataclass, field
from typing import Optional, Type
from totoms.model.TotoEnvironment import TotoEnvironment
from totoms.model.TotoConfig import TotoControllerConfig


@dataclass
class APIControllerProps:
    """
    Properties required to initialize the TotoAPIController.
    
    Attributes:
        api_name: The name of the API (e.g., 'expenses', 'topics')
        environment: The TotoEnvironment configuration
        config: The TotoControllerConfig instance
    """
    api_name: str
    environment: TotoEnvironment
    config: TotoControllerConfig
