"""
Smartflow SDK Synchronous Client.

A synchronous wrapper around the async SmartflowClient for use in
environments that can't use asyncio.

Example:
    >>> from smartflow import SyncSmartflowClient
    >>> 
    >>> sf = SyncSmartflowClient("http://smartflow:7775")
    >>> response = sf.chat("What is machine learning?")
    >>> print(response)
"""

from typing import Optional, Dict, List, Any
import asyncio
import threading

from .client import SmartflowClient, SmartflowAgent, SmartflowWorkflow
from .types import (
    AIResponse,
    ComplianceResult,
    CacheStats,
    ProviderHealth,
    VASLog,
    SystemHealth,
    IntelligentScanResult,
    LearningStatus,
    LearningSummary,
    MLStats,
    OrgBaseline,
    PersistenceStats,
    AgentConfig,
    WorkflowStep,
    WorkflowResult,
)


class SyncSmartflowClient:
    """
    Synchronous client for connecting to a deployed Smartflow instance.
    
    This is a wrapper around SmartflowClient for environments that
    cannot use async/await (e.g., Jupyter notebooks, simple scripts).
    
    For better performance in async applications, use SmartflowClient directly.
    
    Args:
        base_url: URL of Smartflow proxy (default port 7775)
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to SmartflowClient
    
    Example:
        >>> sf = SyncSmartflowClient("http://192.81.214.94:7775")
        >>> 
        >>> # Simple chat
        >>> response = sf.chat("What is AI?")
        >>> print(response)
        >>> 
        >>> # Check cache stats
        >>> stats = sf.get_cache_stats()
        >>> print(f"Hit rate: {stats.hit_rate:.1%}")
        >>> 
        >>> # Clean up
        >>> sf.close()
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        **kwargs,
    ):
        self._async_client = SmartflowClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            **kwargs,
        )
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
    
    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for running async code."""
        if self._loop is None or self._loop.is_closed():
            try:
                # Try to get the running loop (works in some environments)
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create a new one
                self._loop = asyncio.new_event_loop()
        return self._loop
    
    def _run(self, coro):
        """Run a coroutine synchronously."""
        loop = self._get_loop()
        
        # Check if we're already in an async context
        try:
            asyncio.get_running_loop()
            # We're in an async context, use nest_asyncio if available
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(coro)
            except ImportError:
                # nest_asyncio not available, try running in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
        except RuntimeError:
            # Not in async context, run normally
            return loop.run_until_complete(coro)
    
    # =========================================================================
    # CORE AI METHODS
    # =========================================================================
    
    def chat(
        self,
        message: str,
        model: str = "gpt-4o",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Send a chat message through Smartflow.
        
        See SmartflowClient.chat() for full documentation.
        """
        return self._run(self._async_client.chat(
            message=message,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ))
    
    def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        **kwargs,
    ) -> AIResponse:
        """
        OpenAI-compatible chat completions endpoint.
        
        See SmartflowClient.chat_completions() for full documentation.
        """
        return self._run(self._async_client.chat_completions(
            messages=messages,
            model=model,
            **kwargs,
        ))
    
    def embeddings(
        self,
        input: str | List[str],
        model: str = "text-embedding-3-small",
    ) -> Dict[str, Any]:
        """Generate embeddings for text."""
        return self._run(self._async_client.embeddings(input, model))
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        return self._run(self._async_client.list_models())
    
    # =========================================================================
    # ANTHROPIC METHODS
    # =========================================================================
    
    def claude_message(
        self,
        message: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        system: Optional[str] = None,
        anthropic_key: Optional[str] = None,
    ) -> str:
        """Send a message to Claude via Anthropic API."""
        return self._run(self._async_client.claude_message(
            message=message,
            model=model,
            max_tokens=max_tokens,
            system=system,
            anthropic_key=anthropic_key,
        ))
    
    # =========================================================================
    # COMPLIANCE METHODS
    # =========================================================================
    
    def check_compliance(
        self,
        content: str,
        policy: str = "enterprise_standard",
    ) -> ComplianceResult:
        """
        Check content for compliance issues.
        
        See SmartflowClient.check_compliance() for full documentation.
        """
        return self._run(self._async_client.check_compliance(content, policy))
    
    def redact_pii(self, content: str) -> str:
        """Automatically redact PII from content."""
        return self._run(self._async_client.redact_pii(content))
    
    # =========================================================================
    # INTELLIGENT COMPLIANCE (ML-POWERED)
    # =========================================================================
    
    def intelligent_scan(
        self,
        content: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> IntelligentScanResult:
        """
        Scan content using the ML-powered intelligent compliance engine.
        
        See SmartflowClient.intelligent_scan() for full documentation.
        """
        return self._run(self._async_client.intelligent_scan(
            content=content,
            user_id=user_id,
            org_id=org_id,
            context=context,
        ))
    
    def submit_compliance_feedback(
        self,
        scan_id: str,
        is_false_positive: bool,
        user_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit feedback on a compliance scan result."""
        return self._run(self._async_client.submit_compliance_feedback(
            scan_id=scan_id,
            is_false_positive=is_false_positive,
            user_id=user_id,
            notes=notes,
        ))
    
    def get_learning_status(self, user_id: str) -> LearningStatus:
        """Get the learning status for a specific user."""
        return self._run(self._async_client.get_learning_status(user_id))
    
    def get_learning_summary(self) -> LearningSummary:
        """Get overall learning summary across all users."""
        return self._run(self._async_client.get_learning_summary())
    
    def get_ml_stats(self) -> MLStats:
        """Get statistics about the ML compliance engine."""
        return self._run(self._async_client.get_ml_stats())
    
    def get_org_summary(self) -> Dict[str, Any]:
        """Get organization-level compliance summary."""
        return self._run(self._async_client.get_org_summary())
    
    def get_org_baseline(self, org_id: str) -> OrgBaseline:
        """Get the compliance baseline for a specific organization."""
        return self._run(self._async_client.get_org_baseline(org_id))
    
    def get_persistence_stats(self) -> PersistenceStats:
        """Get Redis persistence statistics for compliance data."""
        return self._run(self._async_client.get_persistence_stats())
    
    def save_compliance_data(self) -> Dict[str, Any]:
        """Trigger manual save of compliance data to Redis."""
        return self._run(self._async_client.save_compliance_data())
    
    def get_intelligent_health(self) -> Dict[str, Any]:
        """Get health status of the intelligent compliance engine."""
        return self._run(self._async_client.get_intelligent_health())
    
    # =========================================================================
    # CACHE METHODS
    # =========================================================================
    
    def get_cache_stats(self) -> CacheStats:
        """
        Get Smartflow cache statistics.
        
        See SmartflowClient.get_cache_stats() for full documentation.
        """
        return self._run(self._async_client.get_cache_stats())
    
    # =========================================================================
    # HEALTH & MONITORING
    # =========================================================================
    
    def health(self) -> Dict[str, Any]:
        """Quick health check of Smartflow proxy."""
        return self._run(self._async_client.health())
    
    def health_comprehensive(self) -> SystemHealth:
        """Comprehensive health check including all services."""
        return self._run(self._async_client.health_comprehensive())
    
    def get_provider_health(self) -> List[ProviderHealth]:
        """Get health status of all AI providers."""
        return self._run(self._async_client.get_provider_health())
    
    # =========================================================================
    # VAS LOGS (AUDIT)
    # =========================================================================
    
    def get_logs(
        self,
        limit: int = 50,
        provider: Optional[str] = None,
    ) -> List[VASLog]:
        """
        Get VAS audit logs.
        
        See SmartflowClient.get_logs() for full documentation.
        """
        return self._run(self._async_client.get_logs(limit, provider))
    
    def get_logs_hybrid(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get VAS logs from hybrid bridge."""
        return self._run(self._async_client.get_logs_hybrid(limit))
    
    # =========================================================================
    # ANALYTICS
    # =========================================================================
    
    def get_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get usage analytics."""
        return self._run(self._async_client.get_analytics(start_date, end_date))
    
    # =========================================================================
    # ROUTING
    # =========================================================================
    
    def get_routing_status(self) -> Dict[str, Any]:
        """Get current routing configuration and status."""
        return self._run(self._async_client.get_routing_status())
    
    def force_provider(
        self,
        provider: str,
        duration_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Force routing to a specific provider."""
        return self._run(self._async_client.force_provider(provider, duration_seconds))
    
    # =========================================================================
    # CHATBOT
    # =========================================================================
    
    def chatbot_query(self, query: str) -> Dict[str, Any]:
        """Query Smartflow's built-in chatbot for system info."""
        return self._run(self._async_client.chatbot_query(query))
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    
    def close(self):
        """Close the client and clean up resources."""
        self._run(self._async_client.close())
        if self._loop and not self._loop.is_closed():
            self._loop.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

