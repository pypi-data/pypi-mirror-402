"""
TotoLogger - Singleton logger for Toto microservices.
"""
from datetime import datetime
from typing import Optional


class TotoLogger:
    """
    Singleton logger for Toto microservices.
    
    Usage:
        logger = TotoLogger.get_instance("my-service")
        logger.log("INIT", "Service started")
    """
    
    _instance: Optional['TotoLogger'] = None
    
    def __init__(self, api_name: str = "") -> None:
        """
        Initialize the logger.
        
        Args:
            api_name: The name of the API/service for logging
        """
        self.api_name = api_name
    
    @classmethod
    def get_instance(cls, api_name: str = "") -> 'TotoLogger':
        """
        Get or create the singleton instance.
        
        Args:
            api_name: The name of the API/service (used on first initialization)
            
        Returns:
            The singleton TotoLogger instance
        """
        if cls._instance is None:
            cls._instance = cls(api_name or "unknown")
        return cls._instance
    
    def log(self, correlation_id: str, msg: str) -> None:
        """
        Log a message to the console.
        
        Args:
            correlation_id: The correlation ID (request ID, operation ID, etc.)
            msg: The message to log
        """
        # Get the current timestamp
        current_timestamp = datetime.now()
        
        # Format it
        formatted_timestamp = current_timestamp.strftime('%Y.%m.%d %H:%M:%S,%f')[:-3]
        
        # Log
        print(f"[{self.api_name}] - [{correlation_id}] - [{formatted_timestamp}] - {msg}")
