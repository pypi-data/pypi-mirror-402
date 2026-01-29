"""
Smartflow SDK - Developer-friendly AI orchestration, caching, and governance.

Connect to a deployed Smartflow instance and leverage enterprise AI infrastructure.

Quick Start:
    >>> from smartflow import SmartflowClient
    >>> 
    >>> async with SmartflowClient("http://your-smartflow:7775") as sf:
    ...     response = await sf.chat("What is machine learning?")
    ...     print(response)

Synchronous Usage:
    >>> from smartflow import SyncSmartflowClient
    >>> 
    >>> sf = SyncSmartflowClient("http://your-smartflow:7775")
    >>> response = sf.chat("What is machine learning?")
    >>> print(response)

OpenAI Drop-in Replacement:
    >>> from openai import OpenAI
    >>> 
    >>> # Just change the base_url!
    >>> client = OpenAI(base_url="http://your-smartflow:7775/v1")
    >>> response = client.chat.completions.create(...)

Build AI Agents:
    >>> from smartflow import SmartflowClient, SmartflowAgent
    >>> 
    >>> async with SmartflowClient("http://your-smartflow:7775") as sf:
    ...     agent = SmartflowAgent(
    ...         client=sf,
    ...         name="CustomerSupport",
    ...         system_prompt="You are a helpful support agent.",
    ...     )
    ...     response = await agent.chat("How do I reset my password?")

Intelligent Compliance:
    >>> result = await sf.intelligent_scan(
    ...     "My SSN is 123-45-6789",
    ...     user_id="user123",
    ...     org_id="acme_corp"
    ... )
    >>> print(f"Risk: {result.risk_level}, Action: {result.recommended_action}")
"""

__version__ = "0.2.0"
__author__ = "Langsmart, Inc."

from .client import SmartflowClient, SmartflowAgent, SmartflowWorkflow
from .sync import SyncSmartflowClient
from .types import (
    # Core AI types
    AIRequest,
    AIResponse,
    ChatMessage,
    Usage,
    Choice,
    # Basic Compliance
    ComplianceResult,
    PolicyResult,
    # Intelligent Compliance (ML-powered)
    IntelligentScanResult,
    LearningStatus,
    LearningSummary,
    MLStats,
    OrgBaseline,
    PersistenceStats,
    # Cache & Monitoring
    CacheStats,
    ProviderHealth,
    VASLog,
    SystemHealth,
    # Agent Building
    AgentConfig,
    WorkflowStep,
    WorkflowResult,
)
from .exceptions import (
    SmartflowError,
    ConnectionError,
    AuthenticationError,
    RateLimitError,
    ComplianceError,
    ProviderError,
    TimeoutError,
)

__all__ = [
    # Clients
    "SmartflowClient",
    "SyncSmartflowClient",
    # Agent Building
    "SmartflowAgent",
    "SmartflowWorkflow",
    # Core AI Types
    "AIRequest",
    "AIResponse",
    "ChatMessage",
    "Usage",
    "Choice",
    # Basic Compliance
    "ComplianceResult",
    "PolicyResult",
    # Intelligent Compliance (ML-powered)
    "IntelligentScanResult",
    "LearningStatus",
    "LearningSummary",
    "MLStats",
    "OrgBaseline",
    "PersistenceStats",
    # Cache & Monitoring
    "CacheStats",
    "ProviderHealth",
    "VASLog",
    "SystemHealth",
    # Agent Building Types
    "AgentConfig",
    "WorkflowStep",
    "WorkflowResult",
    # Exceptions
    "SmartflowError",
    "ConnectionError",
    "AuthenticationError",
    "RateLimitError",
    "ComplianceError",
    "ProviderError",
    "TimeoutError",
]
