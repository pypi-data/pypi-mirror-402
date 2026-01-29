"""
TotoControllerConfig - Base configuration class for Toto microservices.

Provides functionality for:
- Loading secrets from cloud providers
- Managing JWT signing keys and audience
- Database connection details
- API configuration and properties
- Validating excluded paths
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from totoms.TotoLogger import TotoLogger
from totoms.model.TotoEnvironment import TotoEnvironment


class TotoControllerConfig(ABC):
    """
    Base abstract class for microservice configuration.
    
    Subclasses must implement methods to load configuration specific to their service.
    This class handles common configuration like JWT keys, database connections, etc.
    """
    
    def __init__(self, environment: TotoEnvironment) -> None:
        """
        Initialize the configuration.
        
        Args:
            environment: The TotoEnvironment specifying hyperscaler and region
        """
        from totoms.secrets.SecretsManager import SecretsManager
        
        self.logger = TotoLogger.get_instance()
        self.environment = environment
        self.secrets_manager = SecretsManager(environment)
        
        # Configuration properties (loaded lazily)
        self._jwt_key: Optional[str] = None
        self._jwt_expected_audience: Optional[str] = None
        self._toto_registry_endpoint: Optional[str] = None
        self._mongo_host: Optional[str] = None
        self._mongo_user: Optional[str] = None
        self._mongo_pwd: Optional[str] = None
        self._is_loaded = False
        
        self.logger.log( "INIT", f"Initializing Configuration for environment: {environment.hyperscaler}" )
    
    async def load(self) -> "TotoControllerConfig":
        """
        Load all configuration from secrets manager.
        
        This method should be called once during application initialization.
        Subclasses can override to add service-specific configuration loading.
        """
        if self._is_loaded:
            return
        
        self.logger.log("INIT", "Loading configuration secrets...")
        
        # Load common secrets in parallel
        self._jwt_key, self._jwt_expected_audience, self._toto_registry_endpoint = await asyncio.gather(
            asyncio.to_thread(self.secrets_manager.get_secret, "jwt-signing-key"),
            asyncio.to_thread(self.secrets_manager.get_secret, "toto-expected-audience"),
            asyncio.to_thread(self.secrets_manager.get_secret, "toto-registry-endpoint"),
        )
        
        # Load Mongo secrets in parallel if needed
        mongo_secret_names = self.get_mongo_secret_names()
        if mongo_secret_names:
            self._mongo_host, self._mongo_user, self._mongo_pwd = await asyncio.gather(
                asyncio.to_thread(self.secrets_manager.get_secret, "mongo-host"),
                asyncio.to_thread(self.secrets_manager.get_secret, mongo_secret_names["user_secret_name"]),
                asyncio.to_thread(self.secrets_manager.get_secret, mongo_secret_names["pwd_secret_name"]),
            )
        
        self._is_loaded = True
        self.logger.log("INIT", "Configuration loaded successfully")
        
        return self
    
    @property
    def jwt_key(self) -> Optional[str]:
        """Get the JWT signing key."""
        return self._jwt_key
    
    @property
    def jwt_expected_audience(self) -> Optional[str]:
        """Get the expected JWT audience."""
        return self._jwt_expected_audience
    
    @property
    def toto_registry_endpoint(self) -> Optional[str]:
        """Get the Toto Registry endpoint."""
        return self._toto_registry_endpoint
    
    @property
    def mongo_host(self) -> Optional[str]:
        """Get the MongoDB host."""
        return self._mongo_host
    
    @property
    def mongo_user(self) -> Optional[str]:
        """Get the MongoDB username."""
        return self._mongo_user
    
    @property
    def mongo_pwd(self) -> Optional[str]:
        """Get the MongoDB password."""
        return self._mongo_pwd
    
    def get_mongo_secret_names(self) -> Optional[Dict[str, str]]:
        """
        Get the names of Mongo secrets to load.
        
        Override this method if your service uses MongoDB.
        
        Returns:
            A dictionary with 'user_secret_name' and 'pwd_secret_name' keys,
            or None if MongoDB is not used
        """
        return None
    
    def is_path_excluded(self, path: str) -> bool:
        """
        Check if a path should be excluded from authentication validation.
        
        Override this method to exclude specific paths (e.g., '/health', '/smoke').
        
        Args:
            path: The request path
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        # By default, exclude health and smoke paths
        return path in ["/", "/health", "/smoke"]
    
    def get_props(self) -> Dict[str, Any]:
        """
        Get all configuration properties as a dictionary.
        
        Useful for debugging and logging.
        
        Returns:
            A dictionary of configuration properties
        """
        return {
            "api_name": self.get_api_name(),
            "expected_audience": self.get_expected_audience(),
            "mongo_enabled": self._mongo_host is not None,
            "registry_endpoint": self.toto_registry_endpoint,
        }
    

