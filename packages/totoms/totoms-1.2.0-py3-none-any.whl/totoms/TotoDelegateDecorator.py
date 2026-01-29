from fastapi import Request
from totoms.TotoLogger import TotoLogger
from totoms.TotoMicroservice import TotoMicroservice
from totoms.TotoTokenVerifier import TotoTokenVerifier
from totoms.model.ExecutionContext import ExecutionContext
from totoms.model.TotoConfig import TotoControllerConfig
from totoms.model.UserContext import UserContext
from totoms.model.ValidationResult import ValidationResult

def toto_delegate(dlg): 
    """Creates a decorator for a Toto Delegate function  

    Args:
        dlg (callable): a function to decorate, that needs to have a signature f(request: Request, user_context: UserContext, exec_context: ExecutionContext)
    """
    
    async def decorator(request: Request): 
        """Decorator for a Toto Delegate function
        
        This decorator performs the following operations: 
        1. Validates mandatory headers: x-correlation-id and Authorization header
        2. Validates JWT token passed as Bearer token in the Authorization header
        3. Creates the User Context to pass it to the delegate
        4. Creates the Execution Context to pass it to the delegate

        Args:
            request (Request): FastAPI Request object

        Returns:
            any: the returned value from the decorated function or a validation error
        """
        
        microservice = TotoMicroservice.get_instance()
        
        config: TotoControllerConfig = microservice.config
        logger = TotoLogger.get_instance()
        message_bus = microservice.message_bus
        
        # Extract info 
        cid, _ = await extract_info(request)
        
        # Validate the request
        validation_result = await validate_request(request, config)
        
        if not validation_result.validation_passed: 
            return validation_result.to_fastapi_response()
        
        # Log the incoming call
        logger.log(cid, f"Incoming API Call: {request.method} {request.url.path}")
        
        # Create a user context object
        user_context = UserContext(validation_result.token_verification_result.user_email)
        
        # Create an execution context object
        execution_context = ExecutionContext(
            logger=logger,
            cid=cid,
            config=config,
            message_bus=message_bus, 
            environment=microservice.microservice_configuration.environment
        )

        # Call the delegate
        return await dlg(request, user_context, execution_context)

    return decorator


async def extract_info(request: Request) :
    """Extracts needed info from the request
    
    Returns cid and auth header
    """
    
    # Extract cid
    cid = request.headers.get("x-correlation-id")
    
    # Extract Authorization header
    auth_header = request.headers.get("Authorization")

    return cid, auth_header

async def validate_request(request: Request, config: TotoControllerConfig) -> ValidationResult: 
    """ Validates the core request data that is mandatory for any call

    Args:
        request (Request): the HTTP request

    Returns:
        ValidationResult: the result of the validation. The flag "validation_passed" will indicate whether the validation was successfull of not
    """
    # Extract the path from the request
    path = request.url.path
    
    # Extract needed info
    cid, auth_header = await extract_info(request)
    
    # Verify that the Correlation Id was provided
    if not cid: 
        # Check if paths are excluded in the config file 
        if not config.is_path_excluded(request.url.path):
            return throw_validation_error(cid, 400, "No correlation id header provided in the Request")
    
    # Verify that an Authorization header was provided
    if not auth_header: 
        return throw_validation_error(cid, 400, "No Authorization header provided in the Request")
    
    # Verify that the Authorization header contains a Bearer Token
    auth_header_tokens = auth_header.split()
    
    if auth_header_tokens[0] != 'Bearer': 
        return throw_validation_error(cid, 400, "Authorization header does not contain a Bearer token")
    
    # Verify the token
    token_verification = TotoTokenVerifier(config, cid = cid).verify_token(auth_header_tokens[1])
    
    if token_verification.code != 200: 
        return throw_validation_error(cid, token_verification.code, token_verification.message)
    
    return ValidationResult(True, token_verification_result=token_verification)
    
    
def throw_validation_error(cid: str, code: int, message: str, additional_log: str = None, logger: TotoLogger = TotoLogger(None)): 
    """ Generates a validation error

    Args:
        cid (str): the Correlation Id
        code (int): the HTTP Error Code to use
        message (str): the Message to both log and provide back to the caller
        additional_log (str): a log message to override the default log (e.g. for sensitivity or security reasons)
    """
    logger.log(cid, additional_log if additional_log is not None else message)
    
    return ValidationResult(False, error_code = code, error_message = message, cid = cid)
