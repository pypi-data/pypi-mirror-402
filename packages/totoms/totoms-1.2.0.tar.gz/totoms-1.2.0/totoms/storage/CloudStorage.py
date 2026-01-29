
from abc import ABC, abstractmethod

from totoms import TotoLogger

class CloudStorage(ABC):
    
    """Abstract base class for cloud storage implementations."""
    def __init__(self, bucket_name: str, logger: TotoLogger, cid: str):
        self.bucket_name = bucket_name
        self.logger = logger
        self.cid = cid
    
    @abstractmethod
    def upload_file(self, local_file_path: str, destination_path: str) -> None:
        """Upload a file to the cloud storage."""
        pass

    @abstractmethod
    def download_file(self, source_path: str, local_destination_path: str) -> None:
        """Download a file from the cloud storage."""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str) -> list:
        """List files in the cloud storage with the given prefix."""
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """Delete a file from the cloud storage."""
        pass
    
    @abstractmethod
    def get_file_content(self, file_path: str) -> str | None:
        """Get the content of a file from the cloud storage."""
        pass
