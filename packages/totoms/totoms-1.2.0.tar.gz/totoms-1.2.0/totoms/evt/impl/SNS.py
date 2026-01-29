"""
SNS Message Bus Implementation for AWS.

Provides AWS SNS-based publish/subscribe functionality.
"""
import json
from typing import Dict
import boto3
from botocore.exceptions import ClientError
from fastapi import Request

from totoms.TotoLogger import TotoLogger
from totoms.evt.TotoMessageBus import IPubSub
from totoms.evt.TotoMessage import TotoMessage
from totoms.evt.MessageDestination import MessageDestination
from totoms.evt.TotoMessageHandler import ProcessingResponse, ProcessingStatus
from totoms.model.TotoEnvironment import AWSConfiguration


class SNSMessageBus(IPubSub):
    """
    AWS SNS implementation of the message bus.
    
    Provides publish/subscribe functionality using AWS Simple Notification Service (SNS).
    """
    
    def __init__(self, config: AWSConfiguration):
        """
        Initialize the SNS message bus.
        
        Args:
            config: AWS configuration with region and environment
        """
        self.config = config
        self.logger = TotoLogger.get_instance()
        
        # Initialize SNS client
        self.sns_client = boto3.client('sns', region_name=config.region)
        
        self.logger.log("INIT", f"SNS Message Bus initialized in region {config.region}")
    
    async def publish_message( self, destination: MessageDestination, message: TotoMessage ) -> None:
        """
        Publish a message to an SNS topic.
        
        Args:
            destination: The MessageDestination containing the topic ARN or name
            message: The TotoMessage to publish
            
        Raises:
            ValueError: If destination.topic is not provided
            ClientError: If SNS publish operation fails
        """
        if not destination.topic:
            raise ValueError("destination.topic is required for SNS publishing")
        
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
            # Publish to SNS topic
            response = self.sns_client.publish(
                TopicArn=destination.topic,
                Message=message_body,
                MessageAttributes={
                    'messageType': {
                        'DataType': 'String',
                        'StringValue': message.type
                    }
                }
            )
            
            self.logger.log(
                "INFO",
                f"Message published to SNS topic {destination.topic}, MessageId: {response.get('MessageId')}"
            )
            
        except ClientError as e:
            self.logger.log(
                "ERROR",
                f"Failed to publish message to SNS: {str(e)}"
            )
            raise
    
    async def handle_subscription_confirmation(self, envelope: Request) -> ProcessingResponse:
        """
        Handle SNS subscription confirmation messages.
        Concretely does the following: 
        - Extract the SubscribeURL from the message
        - Send a GET request to the SubscribeURL to confirm the subscription
        - Returns a ProcessingResponse IGNORED
        
        Args:
            envelope: The SNS subscription confirmation message as a Request object
        """
        body = await envelope.json()
        subscribe_url = body.get('SubscribeURL', '')
        
        if not subscribe_url:
            self.logger.log("ERROR", "SNS SubscriptionConfirmation message missing SubscribeURL")
            return ProcessingResponse(
                status=ProcessingStatus.IGNORED,
                response_payload="SNS SubscriptionConfirmation message missing SubscribeURL."
            )
        
        import requests
        
        try:
            response = requests.get(subscribe_url)
            
            if response.status_code == 200:
                self.logger.log("INFO", "SNS subscription confirmed successfully.")
            else:
                self.logger.log("ERROR", f"SNS subscription confirmation failed with status code {response.status_code}.")
                
        except requests.RequestException as e:
            self.logger.log("ERROR", f"Error confirming SNS subscription: {str(e)}")
            
        return ProcessingResponse(
            status=ProcessingStatus.IGNORED,
            response_payload="SNS subscription confirmed successfully."
        )
        
    async def convert(self, envelope: Request) -> TotoMessage:
        """
        Convert an SNS message envelope to TotoMessage.
        
        SNS messages come in different formats depending on the subscription type:
        - HTTP/HTTPS subscriptions receive SNS notifications
        - SQS subscriptions receive SNS messages wrapped in SQS format
        
        Args:
            envelope: The SNS message envelope
            
        Returns:
            Parsed TotoMessage
            
        Raises:
            ValueError: If the message format is invalid
        """
        try:
            body = await envelope.json()
            
            # Check if this is an SNS notification (HTTP/HTTPS subscription)
            if body.get("Type", "") in ['Notification']:
                return self._convert_sns_notification(body)
            
            # Check if this is an SQS message containing SNS data
            # elif 'Records' in envelope:
            #     # Handle SQS messages that contain SNS notifications
            #     if len(envelope['Records']) > 0:
            #         record = envelope['Records'][0]
            #         if 'Sns' in record:
            #             return self._convert_sns_notification(record['Sns'])
            
            # Try to parse as direct message
            return self._convert_direct_message(envelope)
            
        except (KeyError, json.JSONDecodeError) as e:
            self.logger.log("ERROR", f"Failed to convert SNS message: {str(e)}")
            raise ValueError(f"Invalid SNS message format: {str(e)}")
    
    def _convert_sns_notification(self, sns_message: Dict) -> TotoMessage:
        """
        Convert an SNS notification to TotoMessage.
        
        Args:
            sns_message: The SNS notification
            
        Returns:
            Parsed TotoMessage
        """
        # Extract the message body
        message_body = sns_message.get('Message', '{}')
        
        # Parse the message body (it's usually JSON)
        if isinstance(message_body, str):
            message_data = json.loads(message_body)
        else:
            message_data = message_body
        
        # Extract message attributes
        message_attributes = sns_message.get('MessageAttributes', {})
        message_type = message_attributes.get('messageType', {}).get('Value', 'unknown')
        
        # Build TotoMessage
        return TotoMessage(
            timestamp=message_data.get('timestamp', sns_message.get('Timestamp', '')),
            cid=message_data.get('cid', ''),
            id=message_data.get('id', ''),
            type=message_data.get('type', message_type),
            msg=message_data.get('msg', ''),
            data=message_data.get('data', {})
        )
    
    def _convert_direct_message(self, envelope: Dict) -> TotoMessage:
        """
        Convert a direct message format to TotoMessage.
        
        Args:
            envelope: The message envelope
            
        Returns:
            Parsed TotoMessage
        """
        return TotoMessage(
            timestamp=envelope.get('timestamp', ''),
            cid=envelope.get('cid', ''),
            id=envelope.get('id', ''),
            type=envelope.get('type', 'unknown'),
            msg=envelope.get('msg', ''),
            data=envelope.get('data', {})
        )
