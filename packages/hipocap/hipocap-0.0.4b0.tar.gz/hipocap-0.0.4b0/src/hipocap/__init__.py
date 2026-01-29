"""
Hipocap client library for LMNR integration.

This module provides a client for integrating Hipocap security analysis
with LMNR tracing. The client automatically initializes LMNR tracing and
emits OpenTelemetry events when security threats are detected.
"""

from .config import ClientConfig
from .exceptions import (
    HipocapError,
    HipocapAPIError,
    HipocapConnectionError,
)
from .types import AnalyzeRequest, AnalyzeResponse, AnalysisResult
from .hipocap import Hipocap
from .decorators import observe
__all__ = [
    "ClientConfig",
    "HipocapError",
    "HipocapAPIError",
    "HipocapConnectionError",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "AnalysisResult",
    "Hipocap",
    "observe",
]


