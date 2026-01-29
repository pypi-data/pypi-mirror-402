"""
Type definitions for Hipocap client library.
"""

from typing import Dict, Any, Optional, List, TypedDict


class AnalyzeRequest(TypedDict, total=False):
    """Request type for analyze endpoint."""
    function_name: str
    function_result: Any
    function_args: Optional[Any]
    user_query: Optional[str]
    user_role: Optional[str]
    target_function: Optional[str]
    input_analysis: bool
    llm_analysis: bool
    quarantine_analysis: bool
    enable_keyword_detection: bool
    keywords: Optional[List[str]]


class AnalyzeResponse(TypedDict, total=False):
    """Response type for analyze endpoint."""
    final_decision: str  # "ALLOWED", "BLOCKED", etc.
    final_score: Optional[float]  # Final risk score (0.0-1.0)
    safe_to_use: bool
    blocked_at: Optional[str]
    reason: Optional[str]
    input_analysis: Optional[Dict[str, Any]]
    quarantine_analysis: Optional[Dict[str, Any]]
    llm_analysis: Optional[Dict[str, Any]]
    keyword_detection: Optional[Dict[str, Any]]
    rbac_blocked: Optional[bool]
    chaining_blocked: Optional[bool]
    severity_rule: Optional[Dict[str, Any]]
    output_restriction: Optional[Dict[str, Any]]
    context_rule: Optional[Dict[str, Any]]
    warning: Optional[str]
    function_chaining_info: Optional[Dict[str, Any]]


# Alias for backward compatibility
AnalysisResult = AnalyzeResponse
