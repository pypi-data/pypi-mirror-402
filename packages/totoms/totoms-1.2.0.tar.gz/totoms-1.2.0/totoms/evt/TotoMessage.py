"""
TotoMessage class for representing messages in the message bus.
"""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TotoMessage:
    """
    Represents a message in the Toto message bus.
    
    Attributes:
        timestamp: YYYY.MM.DD HH:mm:ss timestamp of the event
        cid: Correlation ID
        id: Identifier of the object related to the event (if any)
        type: Event type (identifier of the event that can be used to route the message)
        msg: Human-readable message describing the event (not really useful for processing, mostly for logging purposes)
        data: Event data (payload)
    """
    timestamp: str
    cid: str
    id: str
    type: str
    msg: str
    data: Any

