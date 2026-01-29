
from dataclasses import dataclass
from totoms import TotoLogger
from totoms.model.TotoEnvironment import TotoEnvironment
from totoms.evt.TotoMessageBus import TotoMessageBus
from totoms.model.TotoConfig import TotoControllerConfig

@dataclass
class ExecutionContext: 
    
    logger: TotoLogger
    cid: str 
    config: TotoControllerConfig
    message_bus: TotoMessageBus
    environment: TotoEnvironment
    
    def get_storage(self, bucket_name: str):
        """
        Get a CloudStorage instance based on the current environment's hyperscaler.
        This method uses the CloudStorageFactory to create the appropriate storage implementation. 
        It is a utility method to simplify storage access within the execution context.
        
        Args:
            bucket_name (str): The name of the storage bucket to access. This is just the bucket name, not a full path.
        """
        from totoms.storage.CloudStorageFactory import CloudStorageFactory
        
        factory = CloudStorageFactory(self.logger, self.cid)
        
        return factory.create_storage(self.environment.hyperscaler, bucket_name)