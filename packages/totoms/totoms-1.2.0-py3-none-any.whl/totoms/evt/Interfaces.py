from abc import ABC, abstractmethod
from typing import Dict

from totoms.evt.MessageDestination import MessageDestination
from totoms.evt.TotoMessage import TotoMessage

class IMessageBus(ABC):
    """Base interface for message bus implementations."""
    
    @abstractmethod
    async def publish_message(
        self,
        destination: MessageDestination,
        message: TotoMessage
    ) -> None:
        """Publish a message."""
        pass
    
    @abstractmethod
    async def convert(self, envelope: Dict) -> TotoMessage:
        """Convert a message envelope to TotoMessage."""
        pass


class IPubSub(IMessageBus):
    """Interface for Pub/Sub message bus implementations."""
    pass


class IQueue(IMessageBus):
    """Interface for Queue message bus implementations."""
    
    @abstractmethod
    def set_message_handler(self, handler) -> None:
        """Set the handler for PULL messages."""
        pass
