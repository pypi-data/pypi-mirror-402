import boto3
from botocore.exceptions import ClientError

from totoms.storage.CloudStorage import CloudStorage
from totoms.TotoLogger import TotoLogger

class S3Impl(CloudStorage):
    """AWS S3 implementation of CloudStorage."""
    
    def __init__(self, bucket_name: str, logger: TotoLogger, cid: str):
        super().__init__(bucket_name, logger, cid)
        self.client = boto3.client('s3')
    
    def upload_file(self, local_file_path: str, destination_path: str) -> None:
        """Upload a file to S3.
        
        Args:
            local_file_path (str): Local path to the file to upload
            destination_path (str): S3 key path where the file will be stored
        """
        try:
            with open(local_file_path, 'rb') as file:
                self.client.upload_file(local_file_path, self.bucket_name, destination_path)
                
            self.logger.log(self.cid, f"File uploaded to S3: {destination_path}")
                
        except ClientError as e:
            raise Exception(f"Error uploading file to S3: {e}")
    
    def download_file(self, source_path: str, local_destination_path: str) -> None:
        """Download a file from S3 to a local path.
        
        Args:
            source_path (str): S3 key path of the file to download
            local_destination_path (str): Local path where the file will be saved
        """
        try:
            self.client.download_file( Bucket=self.bucket_name, Key=source_path, Filename=local_destination_path )
            
            self.logger.log(self.cid, f"File downloaded from S3: {source_path}")
            
        except ClientError as e:
            raise Exception(f"Error downloading file from S3: {e}")
    
    def list_files(self, prefix: str) -> list:
        """List files in S3 with the given prefix.
        
        Args:
            prefix (str): Prefix to filter files
            
        Returns:
            list: List of file keys matching the prefix
        """
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            
            return []
        
        except ClientError as e:
            raise Exception(f"Error listing files in S3: {e}")
    
    def delete_file(self, file_path: str) -> None:
        """Delete a file from S3.
        
        Args:
            file_path (str): S3 key path of the file to delete
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_path)

            self.logger.log(self.cid, f"File deleted from S3: {file_path}")

        except ClientError as e:
            raise Exception(f"Error deleting file from S3: {e}")
    
    def get_file_content(self, file_path: str) -> str | None:
        """Get the content of a file from S3.
        
        Args:
            file_path (str): S3 key path of the file
            
        Returns:
            str | None: File content as string, or None if file doesn't exist
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=file_path)
            
            return response['Body'].read().decode('utf-8')
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            
            raise Exception(f"Error getting file content from S3: {e}") 