"""
HTTP client for communicating with hipocap-v1 server.
"""

import requests
from typing import Dict, Any, Optional
from .config import ClientConfig
from .exceptions import HipocapAPIError, HipocapConnectionError


class APIClient:
    """
    HTTP client for hipocap-v1 API.
    
    Handles all HTTP requests and error handling.
    """
    
    def __init__(self, config: ClientConfig):
        """
        Initialize API client.
        
        Args:
            config: Client configuration
        """
        self.config = config
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Add API key if provided
        if self.config.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.config.api_key}",
                "X-LMNR-API-Key": self.config.api_key
            })
        
        # Add LMNR user info headers if provided
        if self.config.user_id:
            self.session.headers["X-LMNR-User-Id"] = self.config.user_id
        if self.config.user_email:
            self.session.headers["X-LMNR-User-Email"] = self.config.user_email
        if self.config.user_name:
            self.session.headers["X-LMNR-User-Name"] = self.config.user_name
    
    def analyze(
        self,
        function_name: str,
        function_result: Any,
        function_args: Optional[Any] = None,
        user_query: Optional[str] = None,
        user_role: Optional[str] = None,
        target_function: Optional[str] = None,
        input_analysis: bool = True,
        llm_analysis: bool = False,
        quarantine_analysis: bool = False,
        quick_analysis: bool = False,
        enable_keyword_detection: bool = False,
        keywords: Optional[list] = None,
        policy_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send analysis request to server.
        
        Args:
            function_name: Name of the function to analyze
            function_result: Result from the function call
            function_args: Optional arguments passed to the function call
            user_query: Optional user query for context
            user_role: Optional user role for RBAC checking
            target_function: Optional target function for function chaining checks
            input_analysis: Whether to run input analysis (Stage 1: Prompt Guard) - default True
            llm_analysis: Whether to run LLM analysis agent (Stage 2: Structured LLM analysis) - default False
            quarantine_analysis: Whether to run quarantine analysis (Stage 3: Two-stage infection simulation) - default False
            enable_keyword_detection: Whether to enable keyword detection for sensitive keywords - default False
            keywords: Optional custom list of keywords to detect (if not provided, uses default sensitive keywords)
            policy_key: Optional policy key to use for analysis (defaults to user's default policy)
            
        Returns:
            Analysis response from server
            
        Raises:
            HipocapAPIError: If API returns an error
            HipocapConnectionError: If connection fails
        """
        url = self.config.get_analyze_endpoint()
        
        payload = {
            "function_name": function_name,
            "function_result": function_result,
            "input_analysis": input_analysis,
            "llm_analysis": llm_analysis,
            "quarantine_analysis": quarantine_analysis,
            "quick_analysis": quick_analysis,
            "enable_keyword_detection": enable_keyword_detection
        }
        
        if function_args is not None:
            payload["function_args"] = function_args
        if user_query is not None:
            payload["user_query"] = user_query
        if user_role is not None:
            payload["user_role"] = user_role
        if target_function is not None:
            payload["target_function"] = target_function
        if keywords is not None:
            payload["keywords"] = keywords
        
        # Add policy_key as query parameter if provided
        params = {}
        if policy_key is not None:
            params["policy_key"] = policy_key
        
        try:
            response = self.session.post(
                url,
                json=payload,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
            raise HipocapAPIError(
                f"API error: {error_detail.get('detail', str(e))}",
                status_code=e.response.status_code,
                response=error_detail
            )
        except requests.exceptions.ConnectionError as e:
            raise HipocapConnectionError(
                f"Failed to connect to server at {self.config.server_url}: {str(e)}"
            )
        except requests.exceptions.Timeout as e:
            raise HipocapConnectionError(
                f"Request timeout after {self.config.timeout} seconds"
            )
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Request failed: {str(e)}"
            )
    
    def health_check(self) -> Dict[str, str]:
        """
        Check server health.
        
        Returns:
            Health status from server
            
        Raises:
            HipocapConnectionError: If connection fails
        """
        url = self.config.get_health_endpoint()
        
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Health check failed: {str(e)}"
            )
    
    def update_rbac(
        self,
        roles: Dict[str, Any] = None,
        functions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Update RBAC configuration on the server.
        
        Args:
            roles: Dictionary of roles to add/update
            functions: Dictionary of function configurations to add/update
            
        Returns:
            Response from server with update status
            
        Raises:
            HipocapAPIError: If API returns an error
            HipocapConnectionError: If connection fails
        """
        url = self.config.get_rbac_config_endpoint()
        
        payload = {}
        if roles:
            payload["roles"] = roles
        if functions:
            payload["functions"] = functions
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
            raise HipocapAPIError(
                f"API error: {error_detail.get('detail', str(e))}",
                status_code=e.response.status_code,
                response=error_detail
            )
        except requests.exceptions.ConnectionError as e:
            raise HipocapConnectionError(
                f"Failed to connect to server at {self.config.server_url}: {str(e)}"
            )
        except requests.exceptions.Timeout as e:
            raise HipocapConnectionError(
                f"Request timeout after {self.config.timeout} seconds"
            )
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Request failed: {str(e)}"
            )
    
    def list_traces(
        self,
        function_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        final_decision: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List analysis traces for the current user.
        
        Args:
            function_name: Filter by function name
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            final_decision: Filter by final decision (ALLOWED, BLOCKED, etc.)
            limit: Maximum number of results (1-100)
            offset: Offset for pagination
            
        Returns:
            Dictionary with traces list and pagination info
            
        Raises:
            HipocapAPIError: If API returns an error
            HipocapConnectionError: If connection fails
        """
        url = self.config.get_traces_endpoint()
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if function_name:
            params["function_name"] = function_name
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if final_decision:
            params["final_decision"] = final_decision
        
        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
            raise HipocapAPIError(
                f"API error: {error_detail.get('detail', str(e))}",
                status_code=e.response.status_code,
                response=error_detail
            )
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Request failed: {str(e)}"
            )
    
    def get_trace(self, trace_id: int) -> Dict[str, Any]:
        """
        Get a specific trace by ID.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace data
            
        Raises:
            HipocapAPIError: If API returns an error
            HipocapConnectionError: If connection fails
        """
        url = self.config.get_trace_endpoint(trace_id)
        
        try:
            response = self.session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
            raise HipocapAPIError(
                f"API error: {error_detail.get('detail', str(e))}",
                status_code=e.response.status_code,
                response=error_detail
            )
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Request failed: {str(e)}"
            )
    
    def get_review_required_traces(
        self,
        status: Optional[str] = None,
        function_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get traces that require review.
        
        Args:
            status: Filter by review status (pending, approved, rejected, reviewed)
            function_name: Filter by function name
            limit: Maximum number of results (1-100)
            offset: Offset for pagination
            
        Returns:
            Dictionary with traces list and pagination info
            
        Raises:
            HipocapAPIError: If API returns an error
            HipocapConnectionError: If connection fails
        """
        url = self.config.get_review_required_endpoint()
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if status:
            params["status"] = status
        if function_name:
            params["function_name"] = function_name
        
        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
            raise HipocapAPIError(
                f"API error: {error_detail.get('detail', str(e))}",
                status_code=e.response.status_code,
                response=error_detail
            )
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Request failed: {str(e)}"
            )
    
    def update_review_status(
        self,
        trace_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the review status of a trace.
        
        Args:
            trace_id: Trace ID
            status: Review status (approved, rejected, reviewed)
            notes: Optional review notes
            
        Returns:
            Updated trace data
            
        Raises:
            HipocapAPIError: If API returns an error
            HipocapConnectionError: If connection fails
        """
        url = f"{self.config.server_url}/api/v1/traces/{trace_id}/review"
        
        payload = {"status": status}
        if notes is not None:
            payload["notes"] = notes
        
        try:
            response = self.session.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
            raise HipocapAPIError(
                f"API error: {error_detail.get('detail', str(e))}",
                status_code=e.response.status_code,
                response=error_detail
            )
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Request failed: {str(e)}"
            )
    
    def shield_analyze(
        self,
        shield_key: str,
        content: str,
        user_query: Optional[str] = None,
        require_reason: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze content using a shield's custom blocking rules.
        
        Args:
            shield_key: The unique key identifying the shield to use
            content: The text content to analyze (email content, document text, user message, etc.)
            user_query: Optional context about what the user was trying to do
            require_reason: Whether to include a reason in the response (default: True)
            
        Returns:
            Dictionary with analysis results:
            - decision: "BLOCK" or "ALLOW"
            - reason: Optional one-liner reason (if require_reason is True)
            
        Raises:
            HipocapAPIError: If API returns an error
            HipocapConnectionError: If connection fails
        """
        url = self.config.get_shield_analyze_endpoint(shield_key)
        
        payload = {
            "content": content,
            "require_reason": require_reason
        }
        
        if user_query is not None:
            payload["user_query"] = user_query
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json()
            except:
                error_detail = {"detail": str(e)}
            raise HipocapAPIError(
                f"API error: {error_detail.get('detail', str(e))}",
                status_code=e.response.status_code,
                response=error_detail
            )
        except requests.exceptions.ConnectionError as e:
            raise HipocapConnectionError(
                f"Failed to connect to server at {self.config.server_url}: {str(e)}"
            )
        except requests.exceptions.Timeout as e:
            raise HipocapConnectionError(
                f"Request timeout after {self.config.timeout} seconds"
            )
        except requests.exceptions.RequestException as e:
            raise HipocapConnectionError(
                f"Request failed: {str(e)}"
            )
    
    def close(self):
        """Close the session."""
        self.session.close()

