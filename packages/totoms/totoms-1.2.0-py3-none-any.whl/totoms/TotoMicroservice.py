"""
TotoMicroservice - Main orchestrator for Toto microservices.

Coordinates:
- Configuration loading
- API controller initialization
- Message bus setup
- Message handler registration
- API endpoint registration
- Service startup
"""
from dataclasses import dataclass, field
from typing import Any, Awaitable, Type, List, Optional, Callable
import asyncio

from fastapi import Request

from totoms.TotoLogger import TotoLogger
from totoms.model.TotoEnvironment import TotoEnvironment
from totoms.model.TotoConfig import TotoControllerConfig
from totoms.secrets.SecretsManager import SecretsManager
from totoms.api.TotoAPIController import TotoAPIController
from totoms.api.APIControllerProps import APIControllerProps
from totoms.api.APIControllerOptions import APIControllerOptions
from totoms.evt.TotoMessageBus import TotoMessageBus
from totoms.model.TotoAPIEndpoint import APIEndpoint

from totoms.evt.MessageBusConfig import (
    MessageBusConfiguration,
    TopicIdentifier,
)
from totoms.evt.TotoMessageHandler import TotoMessageHandler

@dataclass
class APIConfiguration:
    """Configuration for API endpoints."""
    api_endpoints: Optional[List[APIEndpoint]] = field(default_factory=list)

@dataclass
class MessageBusHandlerConfig:
    """Configuration for a message handler."""
    handler_class: Type[TotoMessageHandler]


@dataclass
class MessageBusTopicConfig:
    """Configuration for a message bus topic."""
    logical_name: str
    secret: str


@dataclass
class MessageBusConfig:
    """Configuration for the message bus."""
    topics: Optional[List[MessageBusTopicConfig]] = field(default_factory=list)
    message_handlers: Optional[List[MessageBusHandlerConfig]] = field(default_factory=list)


@dataclass
class TotoMicroserviceConfiguration:
    """
    Configuration for initializing a TotoMicroservice.
    
    Attributes:
        service_name: Name of the microservice
        base_path: Optional base path for all API endpoints (e.g., '/api/v1')
        environment: TotoEnvironment specifying hyperscaler and region
        custom_config: Custom configuration class (must inherit from TotoControllerConfig)
        api_configuration: Configuration for API endpoints (optional)
        message_bus_configuration: Configuration for message bus (optional)
    """
    service_name: str
    environment: TotoEnvironment
    custom_config: Type[TotoControllerConfig]
    base_path: Optional[str] = None
    api_configuration: Optional[APIConfiguration] = None
    message_bus_configuration: Optional[MessageBusConfiguration] = None


class TotoMicroservice:
    """
    Main orchestrator for Toto microservices.
    
    Handles initialization and startup of:
    - Configuration from secrets manager
    - API controller with Flask
    - Message bus (Pub/Sub or Queue)
    - Message handler registration
    - API endpoint registration
    
    Implemented as a singleton for application-wide access.
    """
    
    _instance: Optional['TotoMicroservice'] = None
    _instance_promise: Optional[asyncio.Task] = None
    _lock = asyncio.Lock()
    
    def __init__(self, microservice_configuration: TotoMicroserviceConfiguration, config: TotoControllerConfig, api_controller: TotoAPIController, message_bus: Optional[TotoMessageBus] = None):
        """
        Private constructor. Use init() class method instead.
        
        Args:
            config: The loaded TotoControllerConfig
            api_controller: The initialized TotoAPIController
            message_bus: Optional TotoMessageBus instance
        """
        self.config = config
        self.api_controller = api_controller
        self.message_bus = message_bus
        self.logger = TotoLogger.get_instance()
        self.microservice_configuration = microservice_configuration
    
    @classmethod
    async def init( cls, init_config: TotoMicroserviceConfiguration ) -> 'TotoMicroservice':
        """
        Initialize and retrieve the singleton TotoMicroservice instance.
        
        This method handles:
        - Loading configuration from secrets manager
        - Creating the API controller
        - Setting up the message bus
        - Registering message handlers
        - Registering API endpoints
        
        Args:
            init_config: TotoMicroserviceConfiguration with initialization parameters
            
        Returns:
            The singleton TotoMicroservice instance
        """
        async with cls._lock:
            if cls._instance:
                return cls._instance
        
        # Initialize the Logger
        logger = TotoLogger.get_instance(init_config.service_name)
        
        logger.log( "INIT", f"Initializing TotoMicroservice: {init_config.service_name}" )
        
        # LOADING SECRETS -----------
        # Create secrets manager for loading secrets
        # --------------------------- 
        secrets_manager = SecretsManager(init_config.environment)
        
        # Instantiate and load the custom configuration
        custom_config = await init_config.custom_config(init_config.environment).load()
        
        # Load topic names from secrets if message bus is configured
        topic_identifiers: Optional[List[TopicIdentifier]] = None
        
        if (init_config.message_bus_configuration and 
            init_config.message_bus_configuration.topics):
            
            logger.log( "INIT", f"Loading {len(init_config.message_bus_configuration.topics)} message bus topics" )
            
            topic_identifiers = []
            for topic_config in init_config.message_bus_configuration.topics:
                
                resource_id = secrets_manager.get_secret(topic_config.secret)
                
                topic_identifiers.append( TopicIdentifier( logical_name=topic_config.logical_name, resource_identifier=resource_id ) )
        
        # API CONTROLLER -----------
        # Create the API Controller
        # --------------------------
        api_controller = TotoAPIController(
            APIControllerProps(
                api_name=init_config.service_name,
                environment=init_config.environment,
                config=custom_config
            ), 
            APIControllerOptions(
                base_path=init_config.base_path or ""
            )
        )
        
        logger.log("INIT", "API Controller initialized")
        
        # MESSAGE BUS --------------
        # Create the Message Bus if configured
        # --------------------------
        message_bus: Optional[TotoMessageBus] = None
        
        if init_config.message_bus_configuration:
            
            message_bus_config = MessageBusConfiguration(
                controller=api_controller,
                custom_config=custom_config,
                environment=init_config.environment,
                topics=topic_identifiers or []
            )
            
            message_bus = TotoMessageBus(message_bus_config)
            
            # Register message handlers
            if init_config.message_bus_configuration.message_handlers:
                
                logger.log("INIT", f"Registering {len(init_config.message_bus_configuration.message_handlers)} message handlers")
                
                for handler_config in init_config.message_bus_configuration.message_handlers:
                    handler_instance = handler_config.handler_class(custom_config, message_bus, init_config.environment)
                    message_bus.register_message_handler(handler_instance)
            
            logger.log("INIT", "Message Bus initialized")
        
        # API ENDPOINTS --------------
        # Register API endpoints if configured
        # ----------------------------
        if init_config.api_configuration and init_config.api_configuration.api_endpoints:
            
            logger.log("INIT",f"Registering {len(init_config.api_configuration.api_endpoints)} API endpoints")
            
            for endpoint_config in init_config.api_configuration.api_endpoints:
                
                logger.log("INIT", f"Registering endpoint: {endpoint_config.method} {endpoint_config.path}")
                
                # Add the endpoint to the controller
                api_controller.path(endpoint_config)
        
        # Create the singleton instance
        cls._instance = cls(init_config, custom_config, api_controller, message_bus)
        
        logger.log("INIT", f"TotoMicroservice '{init_config.service_name}' initialized successfully" )
        
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'TotoMicroservice':
        """
        Get the singleton TotoMicroservice instance.
        
        Returns:
            The singleton instance
            get 
        Raises:
            RuntimeError: If init() has not been called yet
        """
        if not cls._instance:
            raise RuntimeError( "TotoMicroservice not initialized. Call init() first." )
        
        return cls._instance
    
    async def start(self, port: Optional[int] = None) -> None:
        """
        Start the microservice.
        
        Args:
            port: Optional port to listen on (uses configured default if not specified)
        """
        self.logger.log("INFO", "Starting TotoMicroservice")
        
        # Initialize the API controller
        await self.api_controller.init()
        
        # Start listening for requests
        await self.api_controller.listen(port)

def determine_environment() -> TotoEnvironment:
    """Determine the environment from environment variables or defaults."""
    import os
    
    hyperscaler = os.getenv("HYPERSCALER", "aws").lower()
    
    if hyperscaler == "gcp":
        from totoms.model.TotoEnvironment import GCPConfiguration
        
        project_id = os.getenv("GCP_PID")
        
        return GCPConfiguration(project_id=project_id)
    
    elif hyperscaler == "aws":
        from totoms.model.TotoEnvironment import AWSConfiguration
        
        region = os.getenv("AWS_REGION", "eu-north-1")
        environment = os.getenv("ENVIRONMENT", "dev")
        
        return AWSConfiguration(region=region, environment=environment)
    
    else: 
        raise ValueError(f"Unsupported hyperscaler: {hyperscaler}")