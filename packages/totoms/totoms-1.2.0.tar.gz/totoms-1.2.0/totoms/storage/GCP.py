from google.cloud import storage
from google.cloud.exceptions import NotFound

from totoms.TotoLogger import TotoLogger
from totoms.storage.CloudStorage import CloudStorage


class GCSImpl(CloudStorage):
    """Google Cloud Storage implementation of CloudStorage."""
    
    def __init__(self, bucket_name: str, logger: TotoLogger, cid: str):
        super().__init__(bucket_name, logger, cid)
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
    
    def upload_file(self, local_file_path: str, destination_path: str) -> None:
        """Upload a file to GCS.
        
        Args:
            local_file_path (str): Local path to the file to upload
            destination_path (str): GCS blob path where the file will be stored
        """
        try:
            blob = self.bucket.blob(destination_path)
            
            blob.upload_from_filename(local_file_path)
            
            self.logger.log(self.cid, f"File uploaded to GCS: {destination_path}")
            
        except Exception as e:
            raise Exception(f"Error uploading file to GCS: {e}")
    
    def download_file(self, source_path: str, local_destination_path: str) -> None:
        """Download a file from GCS to a local path.
        
        Args:
            source_path (str): GCS blob path of the file to download
            local_destination_path (str): Local path where the file will be saved
        """
        try:
            blob = self.bucket.blob(source_path)
            
            blob.download_to_filename(local_destination_path)
            
            self.logger.log(self.cid, f"File downloaded from GCS: {source_path}")
            
        except NotFound:
            raise Exception(f"File not found in GCS: {source_path}")
        except Exception as e:
            raise Exception(f"Error downloading file from GCS: {e}")
    
    def list_files(self, prefix: str) -> list:
        """List files in GCS with the given prefix.
        
        Args:
            prefix (str): Prefix to filter files
            
        Returns:
            list: List of blob names matching the prefix
        """
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            return [blob.name for blob in blobs]
        
        except Exception as e:
            raise Exception(f"Error listing files in GCS: {e}")
    
    def delete_file(self, file_path: str) -> None:
        """Delete a file from GCS.
        
        Args:
            file_path (str): GCS blob path of the file to delete
        """
        try:
            blob = self.bucket.blob(file_path)
            
            blob.delete()
            
            self.logger.log(self.cid, f"File deleted from GCS: {file_path}")
            
        except NotFound:
            raise Exception(f"File not found in GCS: {file_path}")
        except Exception as e:
            raise Exception(f"Error deleting file from GCS: {e}")
    
    def get_file_content(self, file_path: str) -> str | None:
        """Get the content of a file from GCS.
        
        Args:
            file_path (str): GCS blob path of the file
            
        Returns:
            str | None: File content as string, or None if file doesn't exist
        """
        try:
            blob = self.bucket.blob(file_path)
            
            return blob.download_as_text()
        
        except NotFound:
            return None
        except Exception as e:
            raise Exception(f"Error getting file content from GCS: {e}")