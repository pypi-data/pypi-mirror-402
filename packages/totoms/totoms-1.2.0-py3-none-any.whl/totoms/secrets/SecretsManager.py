
from dataclasses import dataclass
import os
from typing import Union, cast

import boto3
from botocore.exceptions import ClientError
from google.cloud import secretmanager

from totoms.TotoLogger import TotoLogger
from totoms.model.TotoEnvironment import AWSConfiguration, GCPConfiguration, TotoEnvironment

@dataclass
class SecretsManager: 
    
    environment: TotoEnvironment
    
    def get_secret(self, name: str) -> str:
        """Retrieves a secret from the right cloud provider, based on the environment

        Args:
            name (str): _name of the secret

        Returns:
            _type_: _secret value
        """
        logger = TotoLogger.get_instance()
        
        logger.log("INIT", f"Accessing secret {name} for hyperscaler {self.environment.hyperscaler}")
        
        if self.environment.hyperscaler == 'gcp':
            return self.access_gcp_secret_version(name)
        else:
            return self.access_aws_secret_version(name)
        
        
    def access_gcp_secret_version(self, secret_id: str, version_id: str = "latest") -> str:
        """
        Retrieves a Secret on GCP Secret Manager
        """

        project_id = cast(GCPConfiguration, self.environment.hyperscaler_configuration).project_id

        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret version
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

        # Access the secret version
        response = client.access_secret_version(name=name)

        # Extract the secret payload
        payload = response.payload.data.decode("UTF-8")

        return payload


    def access_aws_secret_version(self, secret_name: str) -> str:
        """
        Retrieves a Secret on AWS Secrets Manager
        """

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=cast(AWSConfiguration, self.environment.hyperscaler_configuration).region, 
        )

        try:
            get_secret_value_response = client.get_secret_value( SecretId=f"{cast(AWSConfiguration, self.environment.hyperscaler_configuration).environment}/{secret_name}" )
            
        except ClientError as e:
            raise e

        secret = get_secret_value_response['SecretString']
        
        return secret
    