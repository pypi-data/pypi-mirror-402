# Toto Microservice Configuration API Reference

The `TotoMicroserviceConfiguration` class is the primary configuration object used to initialize and configure your Toto microservice. It provides a declarative way to define all aspects of your service including API endpoints, message bus subscriptions, environment settings, and custom configuration.

#### Class: `TotoMicroserviceConfiguration`

**Module:** `totoms.TotoMicroservice`

**Description:**
Configuration object for initializing a `TotoMicroservice`. This dataclass defines the complete setup for your microservice including service metadata, cloud environment, API endpoints, and event-driven messaging configuration.

#### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `service_name` | `str` | Yes | - | The name of the microservice. Used for logging and service identification. |
| `environment` | `TotoEnvironment` | Yes | - | The cloud environment configuration specifying the hyperscaler (AWS, GCP, Azure) and region/project details. |
| `custom_config` | `Type[TotoControllerConfig]` | Yes | - | A class (not instance) that inherits from `TotoControllerConfig`. Used to load service-specific secrets and configuration. |
| `base_path` | `Optional[str]` | No | `None` | Base path prefix for all API endpoints (e.g., `/api/v1`, `/tomescraper`). If specified, all endpoint paths will be prefixed with this value. |
| `api_configuration` | `Optional[APIConfiguration]` | No | `None` | Configuration object defining REST API endpoints. Contains the list of API endpoints to register. |
| `message_bus_configuration` | `Optional[MessageBusConfig]` | No | `None` | Configuration for event-driven messaging. Defines topics to subscribe to and message handlers to register. |

#### Related Classes

##### `TotoEnvironment`

Defines the cloud provider and environment-specific configuration.

**Parameters:**
- `hyperscaler` (`Literal["aws", "gcp", "azure"]`): The cloud provider.
- `hyperscaler_configuration` (`Union[AWSConfiguration, GCPConfiguration, AzureConfiguration]`): Provider-specific configuration object.

**Cloud Provider Configurations:**
- **`AWSConfiguration`**
  - `region` (`str`): AWS region (e.g., `"eu-north-1"`)
  - `environment` (`Literal["dev", "test", "prod"]`): Deployment environment
  
- **`GCPConfiguration`**
  - `project_id` (`str`): GCP project identifier

- **`AzureConfiguration`**
  - `region` (`str`): Azure region
  - `environment` (`Literal["dev", "test", "prod"]`): Deployment environment

##### `APIConfiguration`

Configures the REST API endpoints for the microservice.

**Parameters:**
- `api_endpoints` (`Optional[List[APIEndpoint]]`): List of API endpoint definitions. Defaults to empty list.

##### `APIEndpoint`

Defines a single REST API endpoint.

**Parameters:**
- `method` (`str`): HTTP method (e.g., `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`)
- `path` (`str`): Endpoint path relative to base_path (e.g., `"/blogs"`, `"/users/{id}"`)
- `delegate` (`Callable[[Request], Awaitable[Any]]`): Async function decorated with `@toto_delegate` that handles the request

##### `MessageBusConfig`

Configures the event-driven message bus.

**Parameters:**
- `topics` (`Optional[List[MessageBusTopicConfig]]`): List of topics to subscribe to. Defaults to empty list.
- `message_handlers` (`Optional[List[MessageBusHandlerConfig]]`): List of message handler classes. Defaults to empty list.

##### `MessageBusTopicConfig`

Defines a message bus topic subscription.

**Parameters:**
- `logical_name` (`str`): Logical name for the topic used in your code
- `secret` (`str`): Name of the secret containing the actual topic resource identifier (topic name, ARN, etc.)

##### `MessageBusHandlerConfig`

Registers a message handler class.

**Parameters:**
- `handler_class` (`Type[TotoMessageHandler]`): A class (not instance) that inherits from `TotoMessageHandler`

#### Example Usage

```python
from totoms import (
    TotoMicroserviceConfiguration,
    TotoEnvironment,
    APIConfiguration,
    APIEndpoint,
    MessageBusConfig,
    MessageBusTopicConfig,
    MessageBusHandlerConfig,
)
from totoms.model.TotoEnvironment import AWSConfiguration

# Define your custom configuration class
class MyServiceConfig(TotoControllerConfig):
    async def load(self):
        # Load service-specific secrets
        return self

# Create the configuration
config = TotoMicroserviceConfiguration(
    service_name="my-microservice",
    base_path="/api/v1",
    environment=TotoEnvironment(
        hyperscaler="aws",
        hyperscaler_configuration=AWSConfiguration(
            region="eu-west-1",
            environment="prod"
        )
    ),
    custom_config=MyServiceConfig,
    api_configuration=APIConfiguration(
        api_endpoints=[
            APIEndpoint(method="GET", path="/health", delegate=health_check),
            APIEndpoint(method="POST", path="/items", delegate=create_item),
            APIEndpoint(method="GET", path="/items/{id}", delegate=get_item),
        ]
    ),
    message_bus_configuration=MessageBusConfig(
        topics=[
            MessageBusTopicConfig(
                logical_name="orders",
                secret="orders_topic_arn"
            )
        ],
        message_handlers=[
            MessageBusHandlerConfig(handler_class=OrderCreatedHandler)
        ]
    ),
)

# Initialize the microservice
microservice = await TotoMicroservice.init(config)
await microservice.start(port=8080)
```

#### Helper Function: `determine_environment()`

A utility function that reads environment variables to construct the appropriate hyperscaler configuration.

**Returns:** `Union[AWSConfiguration, GCPConfiguration, AzureConfiguration]`

**Environment Variables:**
- `HYPERSCALER`: Cloud provider (`"aws"`, `"gcp"`, `"azure"`). Defaults to `"aws"`.
- For AWS:
  - `AWS_REGION`: AWS region. Defaults to `"eu-north-1"`.
  - `ENVIRONMENT`: Environment name (`"dev"`, `"test"`, `"prod"`). Defaults to `"dev"`.
- For GCP:
  - `GCP_PID`: GCP project ID (required).

**Example:**
```python
config = TotoMicroserviceConfiguration(
    service_name="my-service",
    environment=TotoEnvironment(
        hyperscaler=os.getenv("HYPERSCALER", "aws").lower(),
        hyperscaler_configuration=determine_environment()
    ),
    custom_config=MyConfig,
)
```

#### Notes

- All endpoint delegates must be async functions decorated with `@toto_delegate`
- The `custom_config` parameter expects a class type, not an instance
- Message handler classes must inherit from `TotoMessageHandler`
- Topic secrets are loaded from the cloud provider's secrets manager at initialization
- If `base_path` is provided, it will be prepended to all API endpoint paths