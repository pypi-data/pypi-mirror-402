"""
TotoMessageBus - Message broker for publish/subscribe patterns.

Provides functionality for:
- Publishing messages to Pub/Sub topics or Queues
- Registering message handlers for incoming messages
- Routing messages to appropriate handlers
- Supporting both PUSH (webhooks) and PULL (polling) models
- Integration with multiple hyperscalers (AWS, GCP, Azure)
"""
from typing import Dict, List, Optional, cast
from fastapi import Request

from totoms.TotoLogger import TotoLogger
from totoms.evt.Interfaces import IQueue, IMessageBus, IPubSub
from totoms.evt.impl.SNS import SNSMessageBus
from totoms.model.TotoEnvironment import TotoEnvironment
from totoms.model.Hyperscaler import Hyperscaler
from totoms.evt.MessageBusConfig import (
    MessageBusConfiguration,
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


class MessageHandlerRegistration:
    """
    Registration record for a message handler.
    
    Attributes:
        message_handler: The handler instance
        message_type: The type of messages this handler processes
    """
    
    def __init__(self, message_handler: TotoMessageHandler, message_type: str):
        self.message_handler = message_handler
        self.message_type = message_type


class TotoMessageBus:
    """
    Main message bus class for Toto microservices.
    
    Provides publish/subscribe functionality with:
    - Support for multiple hyperscalers (AWS SNS, GCP Pub/Sub, etc.)
    - Handler registration for different message types
    - Both PUSH and PULL message delivery mechanisms
    - Automatic message routing to appropriate handlers
    """
    
    def __init__(self, config: MessageBusConfiguration):
        """
        Initialize the TotoMessageBus.
        
        Args:
            config: MessageBusConfiguration with controller, config, environment, and topics
        """
        self.config = config
        self.api_controller = config.controller
        self.message_handlers: Dict[str, MessageHandlerRegistration] = {}
        self.message_handler_list: List[MessageHandlerRegistration] = []
        
        self.logger = TotoLogger.get_instance()
        
        # Instantiate the message bus implementation based on hyperscaler
        self.message_bus = self._create_message_bus_impl()
        
        # Register PULL message handler if applicable
        if isinstance(self.message_bus, IQueue):
            self.message_bus.set_message_handler(self.on_pull_message_received)
        
        # Register PUSH message endpoint with API controller
        self.api_controller.register_pub_sub_message_endpoint( "/events", self.on_push_message_received )
    
    def _create_message_bus_impl(self) -> IMessageBus:
        """
        Create the appropriate message bus implementation based on hyperscaler.
        
        Returns:
            An instance of IMessageBus (IPubSub or IQueue implementation)
            
        Raises:
            ValueError: If the hyperscaler is not supported
        """
        hyperscaler = self.config.environment.hyperscaler
        
        if hyperscaler == "aws":
            from totoms.evt.impl.SNS import SNSMessageBus
            self.logger.log("INIT", "Initializing AWS SNS message bus")
            return SNSMessageBus(config=self.config.environment.hyperscaler_configuration)
        
        elif hyperscaler == "gcp":
            from totoms.evt.impl.GCPPubSub import GCPPubSubMessageBus
            self.logger.log("INIT", "Initializing GCP Pub/Sub message bus")
            return GCPPubSubMessageBus(config=self.config.environment.hyperscaler_configuration)
        
        elif hyperscaler == "azure":
            raise ValueError("Azure Service Bus implementation not yet available")
        
        else:
            raise ValueError(
                f"Unsupported hyperscaler '{hyperscaler}' for MessageBus implementation"
            )
    
    def register_message_handler(self, handler: TotoMessageHandler, options: Optional[MessageHandlerRegistrationOptions] = None ) -> None:
        """
        Register a message handler for processing incoming messages.
        
        Args:
            handler: The TotoMessageHandler to register
            options: Optional MessageHandlerRegistrationOptions
        """
        message_type = handler.get_handled_message_type()
        
        registration = MessageHandlerRegistration(handler, message_type)
        
        # Store by message type for quick lookup
        self.message_handlers[message_type] = registration
        
        # Also store in list to maintain order
        self.message_handler_list.append(registration)
        
        self.logger.log( "INIT", f"Registered message handler for message type: {message_type}" )
    
    async def publish_message( self, destination: MessageDestination, message: TotoMessage ) -> None:
        """
        Publish a message to the message bus.
        
        Args:
            destination: The MessageDestination (topic or queue)
            message: The TotoMessage to publish
            
        Raises:
            ValueError: If the destination is invalid for the message bus type
        """
        # Validate destination based on message bus type
        if isinstance(self.message_bus, IPubSub) and not destination.topic:
            raise ValueError("MessageDestination.topic is required for Pub/Sub message buses")
        
        if isinstance(self.message_bus, IQueue) and not destination.queue:
            raise ValueError("MessageDestination.queue is required for Queue message buses")
        
        # Resolve topic names if needed (map logical names to resource identifiers)
        resolved_destination = self._resolve_destination(destination)
        
        self.logger.log(message.cid, f"Publishing message {message.type} to {resolved_destination.topic if resolved_destination.topic is not None else resolved_destination.queue}")
        
        # Publish the message
        await self.message_bus.publish_message(resolved_destination, message)
        
        self.logger.log( "INFO", f"Published message of type '{message.type}' to {resolved_destination}" )
    
    def _resolve_destination(self, destination: MessageDestination) -> MessageDestination:
        """
        Resolve destination by mapping logical topic names to resource identifiers.
        
        Args:
            destination: The original destination
            
        Returns:
            The resolved destination with resource identifiers
        """
        if destination.topic and isinstance(self.message_bus, IPubSub):
            # Look up the resource identifier for this logical topic name
            topic_identifier = self._find_topic_identifier(destination.topic)
            
            if not topic_identifier:
                raise ValueError(
                    f"Topic '{destination.topic}' not found in configuration. "
                    f"This is a configuration error in your application."
                )
            
            return MessageDestination(topic=topic_identifier.resource_identifier)
        
        return destination
    
    def _find_topic_identifier(self, logical_name: str) -> Optional[TopicIdentifier]:
        """
        Find a topic identifier by logical name.
        
        Args:
            logical_name: The logical topic name
            
        Returns:
            The TopicIdentifier if found, None otherwise
        """
        if not self.config.topics:
            return None
        
        for topic in self.config.topics:
            if topic.logical_name == logical_name:
                return topic
        
        return None
    
    async def on_pull_message_received(self, envelope: Dict) -> ProcessingResponse:
        """
        Callback for PULL queue implementations when a message is received.
        
        Routes messages to the appropriate handler based on message type.
        
        Args:
            envelope: The raw message envelope from the queue
            
        Returns:
            A ProcessingResponse with the result of handling
        """
        if not isinstance(self.message_bus, IQueue):
            return ProcessingResponse(
                status=ProcessingStatus.IGNORED,
                response_payload="Message bus is not a Queue implementation"
            )
        
        try:
            # Convert the envelope to a TotoMessage
            message = self.message_bus.convert(envelope)
            
            # Find the handler for this message type
            handler = self._find_handler("pull", message.type)
            
            if not handler:
                return ProcessingResponse(
                    status=ProcessingStatus.IGNORED,
                    response_payload=f"No handler found for message type '{message.type}'"
                )
            
            # Process the message
            return await handler.process_message(message)
        
        except Exception as e:
            self.logger.log("ERROR", f"Error processing PULL message: {str(e)}")
            return ProcessingResponse(
                status=ProcessingStatus.FAILED,
                error=str(e)
            )
    
    async def on_push_message_received(self, envelope: Request) -> ProcessingResponse:
        """
        Callback for PUSH Pub/Sub implementations when a message is received via webhook.
        
        Routes messages to the appropriate handler based on message type.
        
        Args:
            envelope: The webhook payload from the Pub/Sub provider
            
        Returns:
            A ProcessingResponse with the result of handling
        """
        self.logger.log("EVENT", "Received PUSH message from Messaging Infrastructure.")
        
        if not isinstance(self.message_bus, IPubSub):
            self.logger.log("EVENT", "Ignoring message as Message Bus is not an instance of IPubSub")
            return ProcessingResponse(
                status=ProcessingStatus.IGNORED,
                response_payload="Message bus is not a Pub/Sub implementation"
            )
            
        # Implementation-specific 
        # For SNS: Subscription confirmation messages should be answered automatically by the SNS implementation
        body = await envelope.json()
        if (envelope.headers.get('x-amz-sns-message-type', '') == 'SubscriptionConfirmation' or body.get('Type', '') == 'SubscriptionConfirmation'):
            self.logger.log("EVENT", "Received SNS SubscriptionConfirmation message. Ignoring as it should be handled by the SNS implementation.")
            # We assume here that the Message Bus Implementation is thus an SNS implementation
            return await cast(SNSMessageBus, self.message_bus).handle_subscription_confirmation(envelope)
        
        try:
            # Convert the envelope to a TotoMessage
            message = await self.message_bus.convert(envelope)
            
            # Find the handler for this message type
            handler = self._find_handler("push", message.type)
            
            if not handler:
                self.logger.log("EVENT", f"No Message Handler found for message of type {message.type}")
                return ProcessingResponse(
                    status=ProcessingStatus.IGNORED,
                    response_payload=f"No handler found for message type '{message.type}'"
                )
                
            # Process the message
            return await handler.process_message(message)
        
        except Exception as e:
            self.logger.log("ERROR", f"Error processing PUSH message: {str(e)}")
            raise e
    
    def _find_handler(
        self,
        delivery_model: str,
        message_type: str
    ) -> Optional[TotoMessageHandler]:
        """
        Find a handler for the given message type.
        
        Args:
            delivery_model: The delivery model ('push' or 'pull')
            message_type: The message type to find a handler for
            
        Returns:
            The handler if found, None otherwise
        """
        if message_type in self.message_handlers:
            return self.message_handlers[message_type].message_handler
        
        return None
