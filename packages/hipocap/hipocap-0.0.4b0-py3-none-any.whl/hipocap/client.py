"""
Hipocap client for LMNR integration.

This client provides security analysis capabilities with automatic
OpenTelemetry span creation for all analyses. Analysis data is sent
as spans using the same exporter mechanism that LMNR uses, ensuring
it appears in the backend trace view.
"""

import json
import time
from typing import Any, Dict, List, Optional

from .hipocap import Hipocap
from lmnr.sdk.utils import from_env

from .api_client import APIClient
from .config import ClientConfig
from .exceptions import HipocapAPIError, HipocapConnectionError
from .types import AnalyzeResponse

# Import for getting user_id from LMNR context
try:
    from lmnr.opentelemetry_lib.tracing.context import (
        get_current_context,
        get_value,
        CONTEXT_USER_ID_KEY,
    )
except ImportError:
    # Fallback if context module not available
    get_current_context = None
    get_value = None
    CONTEXT_USER_ID_KEY = None


class HipocapClient:
    """
    Client for Hipocap security analysis with LMNR tracing integration.
    
    This client requires Laminar to be initialized before use. It sends all
    analysis data as OpenTelemetry spans using the same exporter mechanism
    that LMNR uses, ensuring analysis data appears in the backend trace view.
    
    Each analysis creates a span named "hipocap.security.analysis" with all
    analysis results as span attributes. The span status is set to ERROR if
    a threat is detected, or OK if the analysis is safe.
    
    Typically, you should access Hipocap via Laminar.hipocap_client after
    initializing Laminar with Hipocap parameters:
    
        Laminar.initialize(
            project_api_key="...",
            hipocap_base_url="http://localhost:8006",
            hipocap_user_id="...",
        )
        client = Laminar.hipocap_client
    
    Alternatively, you can create a HipocapClient directly if Laminar is already initialized.
    """
    
    def __init__(
        self,
        hipocap_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 60,
        # LMNR user info (for authentication)
        user_id: str = "",
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
    ):
        """
        Initialize Hipocap client.
        
        Note: Laminar must be initialized before creating a HipocapClient instance.
        Use Laminar.initialize() to initialize Laminar, which will automatically
        initialize Hipocap if Hipocap parameters are provided.
        
        Args:
            hipocap_base_url: Hipocap server URL (defaults to HIPOCAP_SERVER_URL env var)
            api_key: LMNR API key for authentication (defaults to HIPOCAP_API_KEY env var or LMNR project API key from initialized LMNR)
            timeout: Request timeout in seconds (default: 60)
            user_id: LMNR user ID (UUID string) - if not provided, tries to get from LMNR context
            user_email: LMNR user email - optional
            user_name: LMNR user name - optional
        """
        # Validate that Laminar is initialized
        if not Hipocap.is_initialized():
            raise RuntimeError(
                "Hipocap must be initialized before creating a HipocapClient. "
                "Please call Hipocap.initialize() first. "
                "You can pass Hipocap parameters to Hipocap.initialize() to automatically "
                "initialize Hipocap, or access it via Hipocap.hipocap_client after initialization."
            )
        
        # Try to get user_id from LMNR context if not provided
        if not user_id and get_current_context and CONTEXT_USER_ID_KEY:
            try:
                context = get_current_context()
                user_id = get_value(CONTEXT_USER_ID_KEY, context)
            except Exception:
                # If context is not available, user_id remains empty string
                pass
        
        # Use LMNR project API key as fallback for api_key if not provided
        if api_key is None:
            api_key = Hipocap.get_project_api_key()
        
        # Initialize Hipocap client configuration
        self.config = ClientConfig(
            server_url=hipocap_base_url,
            api_key=api_key,
            timeout=timeout,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
        )
        self.api_client = APIClient(self.config)
    
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
        keywords: Optional[List[str]] = None,
        policy_key: Optional[str] = None
    ) -> AnalyzeResponse:
        """
        Analyze a function call for security threats.
        
        Args:
            function_name: Name of the function to analyze
            function_result: Result from the function call
            function_args: Optional arguments passed to the function call
            user_query: Optional user query for context
            user_role: Optional user role for RBAC checking (e.g., "admin", "user", "guest")
            target_function: Optional target function for function chaining checks
            input_analysis: Whether to run input analysis (Stage 1: Prompt Guard) - default True
            llm_analysis: Whether to run LLM analysis agent (Stage 2: Structured LLM analysis) - default False
            quarantine_analysis: Whether to run quarantine analysis (Stage 3: Two-stage infection simulation) - default False
            quick_analysis: If True, uses quick mode for LLM analysis (simplified output). If False, uses full detailed analysis with structured outputs including threat indicators, detected patterns, and function call attempts. Defaults to True if only LLM analysis is enabled without quarantine - default False
            enable_keyword_detection: Whether to enable keyword detection for sensitive keywords - default False
            keywords: Optional custom list of keywords to detect (if not provided, uses default sensitive keywords)
            policy_key: Optional policy key to use for analysis (defaults to user's default policy)
            
        Returns:
            Dictionary with analysis results:
            - final_decision: "ALLOWED", "BLOCKED", "REVIEW_REQUIRED", or "ALLOWED_WITH_WARNING"
            - final_score: Final risk score (0.0-1.0) from the analysis
            - safe_to_use: Boolean indicating if result is safe to use
            - blocked_at: Stage where blocking occurred (if any)
            - reason: Reason for blocking or decision
            - input_analysis: Input analysis results (if available)
            - quarantine_analysis: Quarantine analysis results (if available)
            - llm_analysis: LLM analysis results (if available). When quick_analysis=False, includes:
              - threats_found: List of general threats detected
              - threat_indicators: List of S1-S14 threat categories and technical indicators
              - detected_patterns: List of attack patterns detected
              - function_call_attempts: List of function names that were attempted
              - policy_violations: List of policy violations found
              - severity: Severity level (safe, low, medium, high, critical)
              - summary: Brief summary of findings
              - details: Detailed analysis explanation
            - keyword_detection: Keyword detection results (if enabled)
            
        Example:
            >>> client = HipocapClient(server_url="https://api.example.com")
            >>> result = client.analyze(
            ...     function_name="get_mail",
            ...     function_result={"status": "success"},
            ...     user_query="Check emails",
            ...     user_role="user",
            ...     policy_key="my_custom_policy"
            ... )
            >>> print(result["final_decision"])
            ALLOWED
            
        Raises:
            HipocapAPIError: If API returns an error response
            HipocapConnectionError: If connection to server fails
        """
        # Capture client-side timestamp when analysis request starts
        analysis_start_time = time.time()
        
        # Call API client
        result = self.api_client.analyze(
            function_name=function_name,
            function_result=function_result,
            function_args=function_args,
            user_query=user_query,
            user_role=user_role,
            target_function=target_function,
            input_analysis=input_analysis,
            llm_analysis=llm_analysis,
            quarantine_analysis=quarantine_analysis,
            quick_analysis=quick_analysis,
            enable_keyword_detection=enable_keyword_detection,
            keywords=keywords,
            policy_key=policy_key
        )
        
        # Capture client-side timestamp when analysis completes
        analysis_end_time = time.time()
        
        # Add client-side timestamps to analysis results
        # Override any server-side timestamps with client-side timestamps
        if input_analysis and result.get("input_analysis"):
            if isinstance(result["input_analysis"], dict):
                result["input_analysis"]["timestamp"] = analysis_start_time
            elif isinstance(result["input_analysis"], str):
                try:
                    input_analysis_dict = json.loads(result["input_analysis"])
                    input_analysis_dict["timestamp"] = analysis_start_time
                    result["input_analysis"] = json.dumps(input_analysis_dict)
                except:
                    pass
        
        if llm_analysis and result.get("llm_analysis"):
            if isinstance(result["llm_analysis"], dict):
                result["llm_analysis"]["timestamp"] = analysis_end_time
            elif isinstance(result["llm_analysis"], str):
                try:
                    llm_analysis_dict = json.loads(result["llm_analysis"])
                    llm_analysis_dict["timestamp"] = analysis_end_time
                    result["llm_analysis"] = json.dumps(llm_analysis_dict)
                except:
                    pass
        
        # Send analysis data as OpenTelemetry span with client-side timestamps
        self._send_analysis_span(function_name, result, analysis_start_time, analysis_end_time)
        
        return result
    
    def _send_analysis_span(
        self, 
        function_name: str, 
        result: AnalyzeResponse,
        analysis_start_time: float,
        analysis_end_time: float
    ) -> None:
        """
        Create and send OpenTelemetry span for Hipocap analysis.
        
        This sends all analysis data as a span using the same exporter mechanism
        that LMNR uses, ensuring it appears in the backend trace view.
        
        Args:
            function_name: Name of the function that was analyzed
            result: Analysis result from Hipocap server
            analysis_start_time: Client-side timestamp when analysis started (Unix timestamp in seconds)
            analysis_end_time: Client-side timestamp when analysis completed (Unix timestamp in seconds)
        """
        if not Hipocap.is_initialized():
            return
        
        # Prepare span attributes from analysis result
        attributes: Dict[str, Any] = {
            "hipocap.function_name": function_name,
            "hipocap.final_decision": result.get("final_decision", "UNKNOWN"),
            "hipocap.safe_to_use": result.get("safe_to_use", False),
        }
        
        # Add severity and score information
        # First try to get final_score from result (highest priority)
        final_score = result.get("final_score")
        combined_severity = None
        combined_score = final_score  # Use final_score if available
        
        # Get analysis results for both score calculation and span attributes
        input_analysis = result.get("input_analysis")
        llm_analysis = result.get("llm_analysis")
        quarantine_analysis = result.get("quarantine_analysis")
        
        # If no final_score, try to get from various analysis stages
        if combined_score is None:
            # Check input_analysis
            if input_analysis:
                if isinstance(input_analysis, dict):
                    combined_severity = input_analysis.get("combined_severity")
                    combined_score = input_analysis.get("combined_score")
                    if not combined_severity:
                        combined_severity = input_analysis.get("severity")
                    if not combined_score:
                        combined_score = input_analysis.get("score")
            
            # Check llm_analysis
            if llm_analysis and isinstance(llm_analysis, dict):
                if not combined_severity:
                    combined_severity = llm_analysis.get("severity")
                if not combined_score:
                    combined_score = llm_analysis.get("score") or llm_analysis.get("risk_score")
            
            # Check quarantine_analysis
            if quarantine_analysis and isinstance(quarantine_analysis, dict):
                if not combined_severity:
                    combined_severity = quarantine_analysis.get("combined_severity")
                if not combined_score:
                    combined_score = quarantine_analysis.get("combined_score")
        
        # Add severity and score if available
        if combined_severity:
            attributes["hipocap.severity"] = combined_severity
        if combined_score is not None:
            attributes["hipocap.score"] = float(combined_score)
        
        # Also add final_score explicitly if available
        if final_score is not None:
            attributes["hipocap.final_score"] = float(final_score)
        
        # Add blocked_at and reason
        if result.get("blocked_at"):
            attributes["hipocap.blocked_at"] = result.get("blocked_at")
        if result.get("reason"):
            attributes["hipocap.reason"] = result.get("reason")
        
        # Add analysis stage results (as JSON strings to avoid attribute limit issues)
        # Ensure client-side timestamps are included
        if input_analysis:
            try:
                if isinstance(input_analysis, dict):
                    # Ensure client-side timestamp is set
                    input_analysis["timestamp"] = analysis_start_time
                    attributes["hipocap.input_analysis"] = json.dumps(input_analysis)
                else:
                    attributes["hipocap.input_analysis"] = str(input_analysis)
            except:
                pass
        
        if llm_analysis:
            try:
                if isinstance(llm_analysis, dict):
                    # Ensure client-side timestamp is set
                    llm_analysis["timestamp"] = analysis_end_time
                    attributes["hipocap.llm_analysis"] = json.dumps(llm_analysis)
                else:
                    attributes["hipocap.llm_analysis"] = str(llm_analysis)
            except:
                pass
        
        if quarantine_analysis:
            try:
                attributes["hipocap.quarantine_analysis"] = json.dumps(quarantine_analysis) if isinstance(quarantine_analysis, dict) else str(quarantine_analysis)
            except:
                pass
        
        # Add RBAC and chaining information
        if result.get("rbac_blocked") is not None:
            attributes["hipocap.rbac_blocked"] = bool(result.get("rbac_blocked"))
        if result.get("chaining_blocked") is not None:
            attributes["hipocap.chaining_blocked"] = bool(result.get("chaining_blocked"))
        
        # Add warning if present
        if result.get("warning"):
            attributes["hipocap.warning"] = result.get("warning")
        
        # Create span for the analysis using context manager for proper nesting
        # Use span_type="TOOL" since Hipocap is a security analysis tool
        # This ensures the span nests under the parent function span from @observe() decorator
        with Hipocap.start_as_current_span(
            name=function_name,
            span_type="TOOL",
            metadata=attributes
        ) as span:
            # Set span status based on analysis result
            from opentelemetry.trace import Status, StatusCode
            from datetime import datetime
            
            # Add events with client-side timestamps
            # Convert Unix timestamps to datetime objects for event timestamps
            analysis_start_datetime = datetime.fromtimestamp(analysis_start_time)
            analysis_end_datetime = datetime.fromtimestamp(analysis_end_time)
            
            # Add event for input analysis if it was performed
            if input_analysis:
                Hipocap.event(
                    "hipocap.security.analysis_complete",
                    attributes={
                        "hipocap.function_name": function_name,
                        "hipocap.analysis_stage": "input_analysis",
                        "hipocap.final_decision": result.get("final_decision", "UNKNOWN"),
                        "hipocap.severity": combined_severity or "unknown",
                        "hipocap.reason": result.get("reason", ""),
                    },
                    timestamp=analysis_start_datetime
                )
            
            # Add event for LLM analysis if it was performed
            if llm_analysis:
                Hipocap.event(
                    "hipocap.security.analysis_complete",
                    attributes={
                        "hipocap.function_name": function_name,
                        "hipocap.analysis_stage": "llm_analysis",
                        "hipocap.final_decision": result.get("final_decision", "UNKNOWN"),
                        "hipocap.severity": combined_severity or "unknown",
                        "hipocap.reason": result.get("reason", ""),
                    },
                    timestamp=analysis_end_datetime
                )
            
            # Add event if threat was detected
            if not result.get("safe_to_use") or result.get("final_decision") != "ALLOWED":
                Hipocap.event(
                    "hipocap.security.threat_detected",
                    attributes={
                        "hipocap.function_name": function_name,
                        "hipocap.final_decision": result.get("final_decision", "UNKNOWN"),
                        "hipocap.severity": combined_severity or "unknown",
                        "hipocap.reason": result.get("reason", "Security threat detected"),
                        "hipocap.blocked_at": result.get("blocked_at", ""),
                    },
                    timestamp=analysis_end_datetime
                )
                # Threat detected - set status to ERROR
                reason = result.get("reason", "Security threat detected")
                span.set_status(Status(StatusCode.ERROR, reason))
            else:
                # Safe - set status to OK
                span.set_status(Status(StatusCode.OK))
            # Span automatically ended when exiting context
    
    def _send_shield_span(
        self,
        shield_key: str,
        content: str,
        result: Dict[str, Any],
        analysis_start_time: float,
        analysis_end_time: float
    ) -> None:
        """
        Create and send OpenTelemetry span for Hipocap shield analysis.
        
        This sends all shield analysis data as a span using the same exporter mechanism
        that LMNR uses, ensuring it appears in the backend trace view.
        
        Args:
            shield_key: The shield key that was used for analysis
            content: The content that was analyzed
            result: Shield analysis result from Hipocap server
            analysis_start_time: Client-side timestamp when analysis started (Unix timestamp in seconds)
            analysis_end_time: Client-side timestamp when analysis completed (Unix timestamp in seconds)
        """
        if not Hipocap.is_initialized():
            return
        
        # Prepare span attributes from shield analysis result
        decision = result.get("decision", "UNKNOWN")
        is_blocked = decision == "BLOCK"
        
        attributes: Dict[str, Any] = {
            "hipocap.shield_key": shield_key,
            "hipocap.shield_decision": decision,
            "hipocap.shield_blocked": is_blocked,
            "hipocap.content_length": len(content) if content else 0,
        }
        
        # Add reason if available
        if result.get("reason"):
            attributes["hipocap.shield_reason"] = result.get("reason")
        
        # Add content preview (first 500 chars to avoid attribute size limits)
        if content:
            content_preview = content[:500] + "..." if len(content) > 500 else content
            attributes["hipocap.content_preview"] = content_preview
        
        # Create span for the shield analysis using context manager for proper nesting
        # Use span_type="TOOL" since Hipocap is a security analysis tool
        # This ensures the span nests under the parent function span from @observe() decorator
        span_name = f"shield.{shield_key}"
        with Hipocap.start_as_current_span(
            name=span_name,
            span_type="TOOL",
            metadata=attributes
        ) as span:
            # Set span status based on shield analysis result
            from opentelemetry.trace import Status, StatusCode
            from datetime import datetime
            
            # Convert Unix timestamps to datetime objects for event timestamps
            analysis_start_datetime = datetime.fromtimestamp(analysis_start_time)
            analysis_end_datetime = datetime.fromtimestamp(analysis_end_time)
            
            # Add event for shield analysis completion
            Hipocap.event(
                "hipocap.shield.analysis_complete",
                attributes={
                    "hipocap.shield_key": shield_key,
                    "hipocap.shield_decision": decision,
                    "hipocap.shield_reason": result.get("reason", ""),
                },
                timestamp=analysis_end_datetime
            )
            
            # Add event if content was blocked
            if is_blocked:
                Hipocap.event(
                    "hipocap.shield.content_blocked",
                    attributes={
                        "hipocap.shield_key": shield_key,
                        "hipocap.shield_decision": decision,
                        "hipocap.shield_reason": result.get("reason", "Content blocked by shield"),
                    },
                    timestamp=analysis_end_datetime
                )
                # Content blocked - set status to ERROR
                reason = result.get("reason", "Content blocked by shield")
                span.set_status(Status(StatusCode.ERROR, reason))
            else:
                # Content allowed - set status to OK
                span.set_status(Status(StatusCode.OK))
            # Span automatically ended when exiting context
    
    def health_check(self) -> Dict[str, str]:
        """
        Check if the server is healthy and reachable.
        
        Returns:
            Dictionary with health status
            
        Example:
            >>> client = HipocapClient()
            >>> status = client.health_check()
            >>> print(status)
            {'status': 'healthy', 'service': 'hipocap-v1'}
        """
        return self.api_client.health_check()
    
    def add_role(self, role_name: str, description: str = None) -> Dict[str, Any]:
        """
        Add or update a role on the server.
        
        Note: Roles no longer have permissions. Permissions are managed through
        functions' allowed_roles field. Use add_function_permission() to grant
        roles access to functions.
        
        Args:
            role_name: Name of the role
            description: Optional description of the role
            
        Returns:
            Response from server with update status
            
        Example:
            >>> client = HipocapClient()
            >>> client.add_role("developer", "Developer role")
            {'success': True, 'message': 'RBAC configuration updated successfully', ...}
            >>> # Then grant permissions via functions:
            >>> client.add_function_permission("get_mail", ["developer"])
        """
        roles = {
            role_name: {
                "description": description or f"Role: {role_name}"
            }
        }
        return self.api_client.update_rbac(roles=roles)
    
    def add_function_permission(
        self,
        function_name: str,
        allowed_roles: list,
        output_restrictions: Dict[str, Any] = None,
        description: str = None
    ) -> Dict[str, Any]:
        """
        Add or update function permissions on the server.
        
        Args:
            function_name: Name of the function
            allowed_roles: List of roles allowed to call this function
            output_restrictions: Optional output restrictions for the function
            description: Optional description of the function
            
        Returns:
            Response from server with update status
            
        Example:
            >>> client = HipocapClient()
            >>> client.add_function_permission(
            ...     "custom_function",
            ...     ["developer", "admin"],
            ...     output_restrictions={"max_severity_for_use": "medium"}
            ... )
            {'success': True, 'message': 'RBAC configuration updated successfully', ...}
        """
        func_config = {
            "allowed_roles": allowed_roles,
            "description": description or f"Function: {function_name}"
        }
        if output_restrictions:
            func_config["output_restrictions"] = output_restrictions
        
        functions = {function_name: func_config}
        return self.api_client.update_rbac(functions=functions)
    
    def update_rbac_config(
        self,
        roles: Dict[str, Any] = None,
        functions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Update RBAC configuration on the server with multiple roles and/or functions.
        
        Args:
            roles: Dictionary of roles to add/update (roles only contain description, no permissions)
            functions: Dictionary of function configurations to add/update (functions contain allowed_roles)
            
        Returns:
            Response from server with update status
            
        Example:
            >>> client = HipocapClient()
            >>> client.update_rbac_config(
            ...     roles={
            ...         "developer": {
            ...             "description": "Developer role"
            ...         }
            ...     },
            ...     functions={
            ...         "custom_function": {
            ...             "allowed_roles": ["developer", "admin"],
            ...             "description": "Custom function"
            ...         }
            ...     }
            ... )
            {'success': True, 'message': 'RBAC configuration updated successfully', ...}
        """
        return self.api_client.update_rbac(roles=roles, functions=functions)
    
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
            
        Example:
            >>> traces = client.list_traces(limit=10, final_decision="BLOCKED")
            >>> print(f"Found {traces['total']} blocked traces")
        """
        return self.api_client.list_traces(
            function_name=function_name,
            start_date=start_date,
            end_date=end_date,
            final_decision=final_decision,
            limit=limit,
            offset=offset
        )
    
    def get_trace(self, trace_id: int) -> Dict[str, Any]:
        """
        Get a specific trace by ID.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace data
            
        Example:
            >>> trace = client.get_trace(123)
            >>> print(trace['final_decision'])
        """
        return self.api_client.get_trace(trace_id)
    
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
            
        Example:
            >>> traces = client.get_review_required_traces(status="pending")
            >>> print(f"Found {traces['total']} pending reviews")
        """
        return self.api_client.get_review_required_traces(
            status=status,
            function_name=function_name,
            limit=limit,
            offset=offset
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
            
        Example:
            >>> result = client.update_review_status(123, "approved", "Looks safe")
            >>> print(result['message'])
        """
        return self.api_client.update_review_status(
            trace_id=trace_id,
            status=status,
            notes=notes
        )
    
    def shield(
        self,
        shield_key: str,
        content: str,
        user_query: Optional[str] = None,
        require_reason: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze content using a shield's custom blocking rules.
        
        This method uses the Shield Analyze API to check if content should be
        blocked or allowed based on a shield's custom rules. The shield defines
        what patterns to block and what exceptions to allow.
        
        Args:
            shield_key: The unique key identifying the shield to use (e.g., "email_protection_shield")
            content: The text content to analyze. Can be any text input:
                    - Email content
                    - Document text
                    - User messages
                    - Any other text that needs protection
            user_query: Optional context about what the user was trying to do
            require_reason: Whether to include a reason in the response (default: True)
            
        Returns:
            Dictionary with analysis results:
            - decision: "BLOCK" or "ALLOW"
            - reason: Optional one-liner reason for the decision (if require_reason is True)
            
        Example:
            >>> client = HipocapClient()
            >>> result = client.shield(
            ...     shield_key="email_protection_shield",
            ...     content="Please click this suspicious link immediately to verify your account.",
            ...     user_query="User is checking their email",
            ...     require_reason=True
            ... )
            >>> print(result["decision"])
            BLOCK
            >>> print(result["reason"])
            Contains suspicious link pattern
            
        Raises:
            HipocapAPIError: If API returns an error response
            HipocapConnectionError: If connection to server fails
        """
        # Capture client-side timestamp when shield analysis request starts
        analysis_start_time = time.time()
        
        # Call API client
        result = self.api_client.shield_analyze(
            shield_key=shield_key,
            content=content,
            user_query=user_query,
            require_reason=require_reason
        )
        
        # Capture client-side timestamp when analysis completes
        analysis_end_time = time.time()
        
        # Send shield analysis data as OpenTelemetry span with client-side timestamps
        self._send_shield_span(shield_key, content, result, analysis_start_time, analysis_end_time)
        
        return result
    
    def close(self):
        """Close the client and release resources."""
        self.api_client.close()
