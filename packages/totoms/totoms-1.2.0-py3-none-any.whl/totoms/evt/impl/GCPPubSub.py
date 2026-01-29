"""
GCP Pub/Sub Message Bus Implementation.

Provides Google Cloud Pub/Sub-based publish/subscribe functionality.
"""
import json
import base64
import os
from typing import Dict
from google.cloud import pubsub_v1
import google.auth

from totoms.TotoLogger import TotoLogger
from totoms.evt.TotoMessageBus import IPubSub
from totoms.evt.TotoMessage import TotoMessage
from totoms.evt.MessageDestination import MessageDestination
from totoms.model.TotoEnvironment import GCPConfiguration


class GCPPubSubMessageBus(IPubSub):
    """
    GCP Pub/Sub implementation of the message bus.
    
    Provides publish/subscribe functionality using Google Cloud Pub/Sub.
    """
    
    def __init__(self, config: GCPConfiguration):
        """
        Initialize the GCP Pub/Sub message bus.
        
        Args:
            config: GCP configuration with project ID
        """
        self.config = config
        self.logger = TotoLogger.get_instance()
        
        # Initialize Pub/Sub publisher client
        self.credentials, self.project_id = google.auth.default()
        self.publisher = pubsub_v1.PublisherClient(credentials=self.credentials)
        
        self.logger.log("INIT", f"GCP Pub/Sub Message Bus initialized for project {self.project_id}")
    
    async def publish_message(self, destination: MessageDestination, message: TotoMessage ) -> None:
        """
        Publish a message to a GCP Pub/Sub topic.
        
        Args:
            destination: The MessageDestination containing the topic name
            message: The TotoMessage to publish
            
        Raises:
            ValueError: If destination.topic is not provided
            Exception: If Pub/Sub publish operation fails
        """
        if not destination.topic:
            raise ValueError("destination.topic is required for GCP Pub/Sub publishing")
        
        # Build the message payload
        message_payload = {
            "timestamp": message.timestamp,
            "cid": message.cid,
            "id": message.id,
            "type": message.type,
            "msg": message.msg,
            "data": message.data
        }
        
        # Convert to JSON string
        message_body = json.dumps(message_payload)
        
        try:
            # Get topic path
            topic_name = destination.topic
            project_id = self.config.project_id
            topic_path = self.publisher.topic_path(project_id, topic_name)
            
            self.logger.log( "INFO", f"Publishing event [{message.type}] for object with id [{message.id}] to topic {topic_name}. Message: [{message.msg}]" )
            
            # Publish to Pub/Sub topic
            future = self.publisher.publish(
                topic_path,
                data=message_body.encode('utf-8')
            )
            
            # Wait for the publish to complete with timeout
            message_id = future.result(timeout=30.0)
            
            self.logger.log( "INFO", f"Successfully published event [{message.type}] to topic {topic_name}, MessageId: {message_id}" )
            
        except Exception as e:
            self.logger.log( "ERROR", f"Failed to publish message to GCP Pub/Sub topic {destination.topic}: {str(e)}" )
            raise
    
    async def convert(self, envelope: Dict) -> TotoMessage:
        """
        Convert a GCP Pub/Sub message envelope to TotoMessage.
        
        GCP Pub/Sub push messages have the following structure:
        {
            "message": {
                "data": "base64-encoded-string",
                "messageId": "...",
                "publishTime": "..."
            },
            "subscription": "..."
        }
        
        Args:
            envelope: The GCP Pub/Sub message envelope (from Flask request.get_json())
            
        Returns:
            Parsed TotoMessage
            
        Raises:
            ValueError: If the message format is invalid
        """
        try:
            # Extract the message from the envelope
            if 'message' not in envelope:
                raise ValueError("Invalid GCP Pub/Sub message: missing 'message' field")
            
            message = envelope['message']
            
            # Decode the base64-encoded data
            if 'data' not in message:
                raise ValueError("Invalid GCP Pub/Sub message: missing 'data' field")
            
            message_data_encoded = message['data']
            message_data_str = base64.b64decode(message_data_encoded).decode('utf-8')
            message_data = json.loads(message_data_str)
            
            # Build TotoMessage
            return TotoMessage(
                timestamp=message_data.get('timestamp', message.get('publishTime', '')),
                cid=message_data.get('cid', ''),
                id=message_data.get('id', ''),
                type=message_data.get('type', 'unknown'),
                msg=message_data.get('msg', ''),
                data=message_data.get('data', {})
            )
            
        except (KeyError, json.JSONDecodeError, Exception) as e:
            self.logger.log("ERROR", f"Failed to convert GCP Pub/Sub message: {str(e)}")
            raise ValueError(f"Invalid GCP Pub/Sub message format: {str(e)}")
