from totoms.TotoLogger import TotoLogger
from totoms.model import Hyperscaler
from totoms.storage.AWS import S3Impl
from totoms.storage.CloudStorage import CloudStorage
from totoms.storage.GCP import GCSImpl

class CloudStorageFactory: 
    
    def __init__(self, logger: TotoLogger, cid: str):
        self.logger = logger
        self.cid = cid
    
    def create_storage(self, hyperscaler: Hyperscaler, bucket_name: str) -> CloudStorage:
        """Factory method to create a CloudStorage instance based on the hyperscaler."""
        
        if hyperscaler == "aws":
            return S3Impl(bucket_name, self.logger, self.cid)
        elif hyperscaler == "gcp":
            return GCSImpl(bucket_name, self.logger, self.cid)
        else:
            raise ValueError(f"Unsupported hyperscaler: {hyperscaler}")