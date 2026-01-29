
class ValidationError(Exception):
    """
    Exception raised for validation errors in the application.
    """
    
    def __init__(self, message: str): 
        super().__init__(message)
        self.message = message