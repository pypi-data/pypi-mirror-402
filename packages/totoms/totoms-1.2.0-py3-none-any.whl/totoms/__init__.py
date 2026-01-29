"""
Toto API Controller - Python framework for building microservices.

Provides:
- TotoMicroservice: Main orchestrator for microservice initialization and lifecycle
- TotoAPIController: FastAPI-based REST API framework
- TotoMessageBus: Message broker for event-driven architecture
- TotoControllerConfig: Base configuration class for secrets management
"""

# Core classes
from totoms.TotoMicroservice import (
    TotoMicroservice,
    TotoMicroserviceConfiguration,
    APIConfiguration,
    MessageBusConfiguration,
    MessageBusHandlerConfig,
    MessageBusTopicConfig,
)

from totoms.api.TotoAPIController import (
    TotoAPIController,
    HTTPMethod,
)

from totoms.api.APIControllerProps import APIControllerProps
from totoms.api.APIControllerOptions import APIControllerOptions

from totoms.evt.TotoMessageBus import (
    TotoMessageBus,
    MessageHandlerRegistration,
)

from totoms.evt.MessageBusConfig import (
    MessageBusConfiguration as MessageBusConfigType,
    TopicIdentifier,
    MessageHandlerRegistrationOptions,
)

from totoms.evt.TotoMessage import TotoMessage
from totoms.evt.TotoMessageHandler import (
    TotoMessageHandler,
    ProcessingResponse,
    ProcessingStatus,
)
from totoms.evt.MessageDestination import MessageDestination

from totoms.model.TotoConfig import TotoControllerConfig
from totoms.model.TotoEnvironment import (
    TotoEnvironment,
    AWSConfiguration,
    GCPConfiguration,
    AzureConfiguration,
)
from totoms.model.Hyperscaler import Hyperscaler
from totoms.model.PathOptions import PathOptions

# Logger
from totoms.TotoLogger import TotoLogger

# Utilities
from totoms.secrets.SecretsManager import SecretsManager

# Storage
from totoms.storage.CloudStorage import CloudStorage

# Exceptions
from totoms.model.exceptions.ValidationError import ValidationError

__all__ = [
    # Microservice
    "TotoMicroservice",
    "TotoMicroserviceConfiguration",
    "APIConfiguration",
    "MessageBusConfiguration",
    "MessageBusHandlerConfig",
    "MessageBusTopicConfig",
    # API Controller
    "TotoAPIController",
    "HTTPMethod",
    "APIControllerProps",
    "APIControllerOptions",
    # Message Bus
    "TotoMessageBus",
    "MessageHandlerRegistration",
    "TopicIdentifier",
    "MessageHandlerRegistrationOptions",
    # Messages
    "TotoMessage",
    "TotoMessageHandler",
    "ProcessingResponse",
    "ProcessingStatus",
    "MessageDestination",
    # Configuration
    "TotoControllerConfig",
    "TotoEnvironment",
    "AWSConfiguration",
    "GCPConfiguration",
    "AzureConfiguration",
    "Hyperscaler",
    "PathOptions",
    # Logger
    "TotoLogger",
    # Secrets
    "SecretsManager",
    # Storage
    "CloudStorage",
    # Exceptions
    "ValidationError",
]
