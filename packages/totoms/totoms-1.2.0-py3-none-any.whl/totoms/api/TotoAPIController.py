"""
TotoAPIController - FastAPI-based API controller for Toto microservices.

Provides functionality to:
- Register API paths with methods (GET, POST, PUT, DELETE, etc.)
- Handle validation and authentication
- Support file uploads and streaming responses
- Manage CORS and standard HTTP headers
- Integrate with the Toto Registry
"""
from typing import Callable, Dict, List, Optional, Any
from enum import Enum
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from totoms.TotoLogger import TotoLogger
from totoms.api.APIControllerProps import APIControllerProps
from totoms.api.APIControllerOptions import APIControllerOptions
from totoms.model.PathOptions import PathOptions
from totoms.model.TotoAPIEndpoint import APIEndpoint
from totoms.model.exceptions.ValidationError import ValidationError


class HTTPMethod(str, Enum):
    """HTTP methods supported by the API controller."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class TotoAPIController:
    """
    FastAPI-based API controller for Toto microservices.
    
    Provides a high-level interface to build REST APIs with:
    - Automatic path registration
    - Built-in validation and authentication
    - Standard error handling
    - Integration with Toto Registry
    - Support for static content, file uploads, and streaming responses
    - Full async/await support
    """
    
    def __init__(self, props: APIControllerProps, options: Optional[APIControllerOptions] = None):
        """
        Initialize the TotoAPIController.
        
        Args:
            props: APIControllerProps containing api_name, environment, and config
            options: Optional APIControllerOptions for configuration
        """
        self.app = FastAPI(title=props.api_name)
        self.props = props
        self.api_name = props.api_name
        self.options = options or APIControllerOptions()
        
        self.logger = TotoLogger.get_instance()
        
        # Log configuration if debug mode is enabled
        if self.options.debug_mode:
            self.logger.log("INIT", f"[TotoAPIController Debug] - Config Properties: {self._get_config_props()}")
        
        # Initialize FastAPI middleware
        self._setup_middleware()
        
        # Register standard Toto paths and exception handlers
        self._register_standard_paths()
        self._register_exception_handlers()
    
    def _setup_middleware(self) -> None:
        """Set up FastAPI middleware for CORS, etc."""
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*", "x-correlation-id", "x-msg-id", "auth-provider", "x-app-version", "x-client", "x-client-id"],
        )
    
    def _register_exception_handlers(self) -> None:
        """
        Register standard exception handlers for the API controller.
        """
        # Register Validation Error
        @self.app.exception_handler(ValidationError)
        async def validation_error_handler(request: Request, exc: ValidationError):
            return JSONResponse(
                status_code=400,
                content={"code": 400, "detail": exc.message},
            )
    
    def _register_standard_paths(self) -> None:
        """Register standard Toto paths (smoke test, health check, etc.)."""
        # Add smoke endpoint at '/'
        @self.app.get("/")
        async def smoke_root():
            return await self._smoke_handler(None)
        
        # Add health endpoint
        @self.app.get("/health")
        async def health():
            return await self._smoke_handler(None)
    
    async def _smoke_handler(self, request: Optional[Request]) -> Dict[str, Any]:
        """
        Smoke test (health check) handler.
        
        Returns:
            A dictionary with status information
        """
        return {
            "status": "ok",
            "apiName": self.api_name,
            "message": "Service is running"
        }
    
    def _get_config_props(self) -> Dict[str, Any]:
        """Get configuration properties for logging."""
        # This would be implemented based on TotoConfig interface
        return {}
    
    def path(self, endpoint: APIEndpoint, options: Optional[PathOptions] = None) -> None:
        """
        Register an API path handler.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API path
            handler: Handler function or delegate (can be async or sync)
            options: Optional PathOptions for configuration
        """
        # Apply base path if configured and not ignored
        corrected_path = self._apply_base_path(endpoint.path, options)
        
        # Register with FastAPI
        self.app.add_api_route(
            corrected_path,
            endpoint.delegate,
            methods=[endpoint.method]
        )
        
        self.logger.log("INIT", f"Registered API path: {endpoint.method} {corrected_path}")
        
    def _apply_base_path(self, path: str, options: Optional[PathOptions] = None) -> str:
        """
        Apply base path to the given path if configured.
        
        Args:
            path: The original path
            options: Optional PathOptions
            
        Returns:
            The corrected path with base path applied
        """
        if (self.options.base_path and 
            (not options or not options.ignore_base_path)):
            # Ensure base_path doesn't end with '/'
            base = self.options.base_path.rstrip('/')
            return base + path
        return path
    
    def static_content(self, path: str, folder: str, options: Optional[PathOptions] = None) -> None:
        """
        Register a path for serving static content.
        
        Args:
            path: The path to serve static content from (e.g., '/img')
            folder: The folder containing the static files
            options: Optional PathOptions
        """
        from fastapi.staticfiles import StaticFiles
        
        corrected_path = self._apply_base_path(path, options)
        self.app.mount(corrected_path, StaticFiles(directory=folder), name="static")
    
    def file_upload_path(self, path: str, handler: Callable, options: Optional[PathOptions] = None) -> None:
        """
        Register a path that supports file uploads.
        
        Args:
            path: The path for file uploads
            handler: Handler function to process uploads
            options: Optional PathOptions
        """
        self.path(HTTPMethod.POST, path, handler, options)
    
    def stream_get(self, path: str, handler: Callable, options: Optional[PathOptions] = None) -> None:
        """
        Register a GET path that returns a stream response.
        
        Args:
            path: The path
            handler: Handler function that returns a stream
            options: Optional PathOptions
        """
        self.path(HTTPMethod.GET, path, handler, options)
    
    def register_pub_sub_message_endpoint(self, path: str, handler: Callable) -> None:
        """
        Register an endpoint for receiving Pub/Sub PUSH messages.
        
        Args:
            path: The endpoint path (typically '/events')
            handler: Handler function to process messages
        """
        self.path(endpoint=APIEndpoint(HTTPMethod.POST, path, handler), options=PathOptions(no_auth=True))
    
    async def init(self) -> None:
        """
        Initialize the API controller.
        
        Performs tasks like:
        - Register with Toto API Registry
        - Download API endpoints from registry
        - Cache registry data
        """
        # Register with Toto API Registry
        self.logger.log("INIT", f"API {self.api_name} initialization complete")
    
    async def listen(self, port: Optional[int] = None) -> None:
        """
        Start the FastAPI app listening for requests.
        
        Args:
            port: The port to listen on (uses configured port if not specified)
        """
        import uvicorn
        
        port = port or self.options.port
        self.logger.log("INFO", f"Starting {self.api_name} on port {port}")
        
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port, log_level="info" if self.options.debug_mode else "warning")
        server = uvicorn.Server(config)
        await server.serve()
