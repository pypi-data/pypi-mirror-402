"""
Custom exceptions for Hipocap client.
"""


class HipocapError(Exception):
    """Base exception for all Hipocap client errors."""
    pass


class HipocapAPIError(HipocapError):
    """Exception raised for API errors (4xx, 5xx responses)."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response: Response body (if available)
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response
    
    def __str__(self):
        if self.status_code:
            return f"{super().__str__()} (Status: {self.status_code})"
        return super().__str__()


class HipocapConnectionError(HipocapError):
    """Exception raised for connection/network errors."""
    pass



