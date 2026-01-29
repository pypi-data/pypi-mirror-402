"""
Message Bus configuration types.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from totoms.api.TotoAPIController import TotoAPIController
from totoms.model.TotoConfig import TotoControllerConfig
from totoms.model.TotoEnvironment import TotoEnvironment


@dataclass
class TopicIdentifier:
    """
    Identifier for a Pub/Sub topic.
    
    Attributes:
        logical_name: Logical name used in the app (e.g., 'user-updates-topic')
        resource_identifier: Cloud provider's topic identifier (e.g., ARN for AWS, topic name for GCP)
    """
    logical_name: str
    resource_identifier: str

@dataclass
class MessageHandlerRegistrationOptions:
    """
    Options for registering a message handler.
    
    Attributes:
        enable_push_support: Whether to enable PUSH support for this handler (default: False)
    """
    enable_push_support: bool = False


@dataclass
class MessageBusConfiguration:
    """
    Configuration for the TotoMessageBus.
    
    Attributes:
        controller: The TotoAPIController instance
        custom_config: The TotoControllerConfig instance
        environment: The TotoEnvironment configuration
        topics: List of topic identifiers (optional, for Pub/Sub)
    """
    controller: 'TotoAPIController'
    custom_config: TotoControllerConfig
    environment: TotoEnvironment
    topics: Optional[List[TopicIdentifier]] = field(default_factory=list)
