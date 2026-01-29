
from dataclasses import dataclass
from typing import Literal, Union
from totoms.model.Hyperscaler import Hyperscaler

Environment = Literal["dev", "test", "prod"]

@dataclass
class AWSConfiguration:
    region: str
    environment: Environment


@dataclass
class GCPConfiguration:
    project_id: str


@dataclass
class AzureConfiguration:
    region: str
    environment: Environment


@dataclass
class TotoEnvironment:
    hyperscaler: Hyperscaler
    hyperscaler_configuration: Union[AWSConfiguration, GCPConfiguration, AzureConfiguration]