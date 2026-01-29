# Toto Microservice SDK - Python

The Toto Microservice SDK is a framework for building cloud-agnostic microservices. <br>
This is the Python SDK documentation. 


## Table of Contents

1. [Installation](#1-installation)
2. [Overview](#2-overview)
3. [Usage](#3-usage)
   - [3.1. Create and Register APIs](#31-create-and-register-apis)
   - [3.2. Use a Message Bus](#32-use-a-message-bus)
   - [3.3. Load Secrets](#33-load-secrets)
   - [3.4. Custom Configurations](#34-custom-configurations)
   - [3.5. Using Cloud Storage](#35-using-cloud-storage)

Other: 
* [Build and Publish guide](./docs/buildpublish.md)

## 1. Installation

```bash
pip install totoms
```

## 2. Overview
Everything starts with `TotoMicroservice` and the `TotoMicroserviceConfiguration`.<br>
`TotoMicroservice` is the main orchestrator that coordinates your entire microservice. It initializes and manages:

- **API Controller & API Endpoints**: FastAPI-based REST API setup with automatic endpoint registration
- **Message Bus & Message Handlers**: Event-driven communication via Pub/Sub and Queues. Registration and routing of event handlers to appropriate topics.
- **Secrets Management**: Automatic loading of secrets from your cloud provider
- **Service Lifecycle**: Initialization, startup, and shutdown management

The configuration is **declarative**. The goal is to make it very simple to configure a full microservice, with a syntax that will look like this: 
```python 
  TotoMicroserviceConfiguration(
        service_name="toto-ms-tome-scraper",
        base_path="/tomescraper",
        environment=TotoEnvironment(
            hyperscaler=os.getenv("HYPERSCALER", "aws").lower(),
            hyperscaler_configuration=determine_envrionment()
        ),
        custom_config=TomeScraperConfig,
        api_configuration=APIConfiguration(
            api_endpoints=[
                APIEndpoint(method="POST", path="/blogs", delegate=extract_blog_content),
                APIEndpoint(method="POST", path="/test/refresher", delegate=test_refresher),
                APIEndpoint(method="POST", path="/test/pubsub", delegate=test_pubsub),
            ]
        ),
        message_bus_configuration=MessageBusConfig(
            topics=[
                MessageBusTopicConfig(logical_name="tometopics", secret="tome_topics_topic_name")
            ], 
            message_handlers=[
                MessageBusHandlerConfig(handler_class=TopicRefreshedEventHandler)
            ]
        ),
    )
```

The `TotoMicroserviceConfiguration` object specifies:

- **Service Metadata**: Service name and base path for API endpoints
- **Environment**: Cloud provider (AWS, GCP, Azure) information
- **API Configuration**: REST endpoints with their handlers
- **Message Bus Configuration**: Topics to subscribe to and message handlers
- **Custom Configuration**: Your application-specific settings

The microservice initialization is async and returns a fully configured instance ready to start:

```python
microservice = await TotoMicroservice.init(get_microservice_config())
await microservice.start(port=8080)
```

## 3. Usage

### 3.1. The Toto Microservice Configuration
Go to the [Toto Microservice Configuration](./docs/toto_microservice_configuration.md) API Reference page.

### 3.2. Create and Register APIs

Your microservice exposes REST API endpoints using FastAPI. <br>
Endpoints are defined when creating the microservice configuration and are automatically set up with the API controller.

#### Create a Toto Delegate
Every endpoint needs to be managed by a **Toto Delegate**. <br>
Toto Delegates are identified through the **annotation** `@toto_delegate`. 

This is how you define a Toto Delegate. <br>
*The following example shows a delegate that extracts the content of a blog*. 

```python
@toto_delegate
async def extract_blog_content(request: Request, user_context: UserContext, exec_context: ExecutionContext): 

    # Extract and parse the body from FastAPI Request
    body = await request.json()

    blog_url = data.get("url")
    
    # Process the blog
    result = await process_blog(blog_url)
    
    # Return anything you'd like to
    return {"status": "success", "data": result}
```

#### Register your delegate
You can now register your endpoints in the microservice configuration:

```python
def get_microservice_config() -> TotoMicroserviceConfiguration:
    
    return TotoMicroserviceConfiguration(
        service_name="my-service",
        base_path="/myservice",
        api_configuration=APIConfiguration(
            api_endpoints=[
                APIEndpoint(method="POST", path="/blogs", delegate=extract_blog_content),
            ]
        ),
    )
```

The microservice will start a FastAPI application with all registered endpoints available at the specified base path.

---
### 3.2. Use a Message Bus

The Message Bus enables event-driven communication between microservices.<br>
It supports both PUSH (webhook-based from cloud Pub/Sub) and PULL (polling) delivery models, depending on your cloud provider and configuration.

#### 3.2.1. React to Messages

Message handlers are the primary way to react to events. <br>

##### Create a Message Handler
Create a handler by **subclassing** `TotoMessageHandler` and implementing the required methods:

```python
from totoms import TotoMessageHandler, ProcessingResponse, ProcessingStatus, TotoMessage

class TopicRefreshedEventHandler(TotoMessageHandler):
    
    def get_handled_message_type(self) -> str:
        """Return the message type this handler processes."""
        return "topicRefreshed"
    
    async def process_message(self, message: TotoMessage) -> ProcessingResponse:
        """Process incoming messages of type 'topicRefreshed'."""
        # Access message metadata
        correlation_id = message.cid
        message_id = message.id
        
        # Extract event data
        topic_name = message.data.get("name")
        blog_url = message.data.get("blogURL")
        user = message.data.get("user")
        
        # Your handler has access to context
        self.logger.log(correlation_id, f"Processing topic refresh for: {topic_name}")
        
        # Perform your business logic
        await refresh_topic(topic_name, blog_url, user)
        
        # Return success or failure
        return ProcessingResponse(status=ProcessingStatus.SUCCESS)
```

##### Register a Message Handler
Register your message handlers in the microservice configuration. 

IMPORTANT NOTE: <br>
* When using PubSub infrastructure, you need to register topics. <br>
Topics are registered by giving them: 
    * A `logical_name` which is the name that will be used in the application to reference the topic. 
    * A `secret` which is **the name of the secret** that contains the implementation-specific resource identifier of the topic (e.g. ARN on AWS or fully-qualified Topic Name on GCP)

```python
from totoms import MessageBusHandlerConfig

def get_microservice_config() -> TotoMicroserviceConfiguration:
    """Create configuration with message handlers."""
    return TotoMicroserviceConfiguration(
        service_name="my-service",
        message_bus_configuration=MessageBusConfig(
            topics=[
                MessageBusTopicConfig(
                    logical_name="topic-events", 
                    secret="topic_events_topic_name"  # Secret name in your secrets manager
                )
            ],
            message_handlers=[
                MessageBusHandlerConfig(handler_class=TopicRefreshedEventHandler),
                MessageBusHandlerConfig(handler_class=AnotherEventHandler),
            ]
        ),
    )
```

When the microservice starts, it automatically subscribes to the configured topics and routes incoming messages to the appropriate handlers based on their message type.

#### 3.2.2. Publish Messages

You can always publish messages to topics.

NOTE: 
* In the Message Destination, the topic is the **logical name of the topic** (see above).

```python
from totoms import TotoMessage, MessageDestination

async def publish_topic_update(microservice, topic_id: str, topic_name: str):
    """Publish a topic update event."""
    message = TotoMessage(
        type="topicUpdated",
        cid="correlation-id-123",
        id=topic_id,
        data={"name": topic_name, "timestamp": datetime.now().isoformat()}
    )
    
    destination = MessageDestination(topic="topic-events")

    await microservice.message_bus.publish_message(destination, message)
```

##### Getting access to the Message Bus. 
There are different ways to get access to the Message Bus instance: 

* Through the `TotoMicroservice` singleton: <br>
`TotoMicroservice.get_instance().message_bus`

* Through an existing instance of `TotoMicroservice` (in the example above)

* In a `TotoMessageHandler` you will have `message_bus` as an instance variable: <br>
`self.message_bus`

* In a `toto_delegate`, you will have it part of `ExecutionContext` and can use like this: <br>
`exec_context.message_bus`

---
### 3.3. Load Secrets

The SDK handles secret loading from your cloud provider automatically. Access secrets through the configuration or use the `SecretsManager` directly:

```python
from totoms import SecretsManager

secrets = SecretsManager()

# Load a secret by name
api_key = secrets.get_secret("api-key")
database_url = secrets.get_secret("database-url")
```

Secrets are typically stored as environment variable names or secret manager references, depending on your deployment environment.

---
### 3.4. Custom Configurations
You can define your own custom configurations by extending the `TotoControllerConfig` base class.

An example:
```python 
from totoms.model.TotoConfig import TotoControllerConfig
from typing import Optional, Dict

class TomeScraperConfig(TotoControllerConfig):
    """Custom configuration for the Toto Tome Scraper service."""
    
    def get_mongo_secret_names(self) -> Optional[Dict[str, str]]:
        """Return MongoDB secret names if service uses MongoDB."""
        return None
```

What you can do with a Custom Configuration: 

1. **Load Secrets** <br>
You can do that by overriding the `load()` async method and using `self.secrets_manager.get_secret, "your-secret-name")` to load secrets.

---
### 3.5. Using Cloud Storage

The SDK provides a cloud-agnostic storage abstraction through the `CloudStorage` interface. <br>
This allows you to interact with cloud storage (AWS S3, Google Cloud Storage, Azure Blob Storage) without worrying about provider-specific APIs.

#### Getting a CloudStorage Instance

The easiest way to get a `CloudStorage` instance is through the `ExecutionContext` in your delegates:

```python
from fastapi import Request
from totoms import toto_delegate, ExecutionContext, UserContext, ValidationError

@toto_delegate
async def handle_file_upload(request: Request, user_context: UserContext, exec_context: ExecutionContext):
    
    bucket_name = request.query_params.get("bucket")
    
    if not bucket_name:
        raise ValidationError("Missing 'bucket' query parameter.")
    
    # Get a CloudStorage instance for the specified bucket
    storage = exec_context.get_storage(bucket_name)
    
    # Now you can use the storage instance
    # ... (see examples below)
```

The `get_storage()` method automatically creates the appropriate storage implementation based on your configured cloud provider (hyperscaler).

#### Uploading Files

```python
# Create a local file
local_file_path = './hello.txt'

with open(local_file_path, 'w') as f:
    f.write('Hello, Toto!')

# Upload to cloud storage
destination_path = 'my-folder/hello.txt'
storage.upload_file(local_file_path, destination_path)

exec_context.logger.log(exec_context.cid, f"Uploaded file to {destination_path}")
```

#### Downloading Files

```python
# Download a file from cloud storage
source_path = 'my-folder/hello.txt'
local_destination = './downloaded_hello.txt'

storage.download_file(source_path, local_destination)

exec_context.logger.log(exec_context.cid, f"Downloaded file to {local_destination}")
```

#### Listing Files

```python
# List all files with a specific prefix
files = storage.list_files('my-folder/')

exec_context.logger.log(exec_context.cid, f"Files in bucket: {files}")

for file_path in files:
    exec_context.logger.log(exec_context.cid, f"  - {file_path}")
```

#### Getting File Content

```python
# Read file content directly without downloading
file_path = 'my-folder/hello.txt'
content = storage.get_file_content(file_path)

exec_context.logger.log(exec_context.cid, f"File content: {content}")
```

#### Deleting Files

```python
# Delete a file from cloud storage
file_path = 'my-folder/hello.txt'
storage.delete_file(file_path)

exec_context.logger.log(exec_context.cid, f"Deleted file: {file_path}")
```

