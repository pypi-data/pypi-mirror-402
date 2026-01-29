"""
Client-side configuration for hipocap.
"""

import os
from typing import Optional


class ClientConfig:
    """
    Configuration for hipocap client.
    
    Handles server endpoint URLs, API keys, and LMNR user information.
    """
    
    def __init__(
        self,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None
    ):
        """
        Initialize client configuration.
        
        Args:
            server_url: Base URL of the hipocap-v1 server (defaults to HIPOCAP_SERVER_URL env var)
            api_key: API key for authentication (defaults to HIPOCAP_API_KEY env var)
            timeout: Request timeout in seconds
            user_id: LMNR user ID (UUID string) - optional
            user_email: LMNR user email - optional
            user_name: LMNR user name - optional
        """
        self.server_url = server_url or os.getenv("HIPOCAP_SERVER_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("HIPOCAP_API_KEY")
        self.timeout = timeout
        self.user_id = user_id
        self.user_email = user_email
        self.user_name = user_name
        
        # Ensure server_url doesn't end with /
        if self.server_url.endswith("/"):
            self.server_url = self.server_url.rstrip("/")
    
    def get_analyze_endpoint(self) -> str:
        """Get the full URL for the analyze endpoint."""
        return f"{self.server_url}/api/v1/analyze"
    
    def get_health_endpoint(self) -> str:
        """Get the full URL for the health check endpoint."""
        return f"{self.server_url}/api/v1/health"
    
    def get_rbac_config_endpoint(self) -> str:
        """Get the full URL for the RBAC configuration endpoint."""
        return f"{self.server_url}/api/v1/config/rbac"
    
    def get_traces_endpoint(self) -> str:
        """Get the full URL for the traces list endpoint."""
        return f"{self.server_url}/api/v1/traces"
    
    def get_trace_endpoint(self, trace_id: int) -> str:
        """Get the full URL for a specific trace endpoint."""
        return f"{self.server_url}/api/v1/traces/{trace_id}"
    
    def get_review_required_endpoint(self) -> str:
        """Get the full URL for the review-required traces endpoint."""
        return f"{self.server_url}/api/v1/traces/review-required"
    
    def get_shield_analyze_endpoint(self, shield_key: str) -> str:
        """Get the full URL for the shield analyze endpoint."""
        return f"{self.server_url}/api/v1/shields/{shield_key}/analyze"