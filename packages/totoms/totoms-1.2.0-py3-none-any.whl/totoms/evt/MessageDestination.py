"""
Message Destination configuration.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MessageDestination:
    """
    Represents the destination for a message in the message bus.
    
    Attributes:
        topic: The topic name for Pub/Sub implementations (optional)
        queue: The queue name for Queue implementations (optional)
    """
    topic: Optional[str] = None
    queue: Optional[str] = None
