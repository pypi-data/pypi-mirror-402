"""
Smartflow SDK Client.

The main async client for connecting to a deployed Smartflow instance.

Example:
    >>> from smartflow import SmartflowClient
    >>> 
    >>> async with SmartflowClient("http://smartflow:7775") as sf:
    ...     response = await sf.chat("What is machine learning?")
    ...     print(response)
"""

from typing import Optional, Dict, List, Any, AsyncIterator
import httpx
import json
from datetime import datetime

from .types import (
    AIRequest,
    AIResponse,
    ChatMessage,
    ComplianceResult,
    CacheStats,
    ProviderHealth,
    VASLog,
    PolicyResult,
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
from .exceptions import (
    SmartflowError,
    ConnectionError as SmartflowConnectionError,
    raise_for_status,
)


class SmartflowClient:
    """
    Async client for connecting to a deployed Smartflow instance.
    
    Smartflow provides:
    - Intelligent routing across AI providers (OpenAI, Anthropic, Gemini, etc.)
    - 3-layer semantic caching (60-80% cost savings)
    - Real-time compliance scanning
    - Full audit logging (VAS logs)
    - Provider failover and load balancing
    
    Args:
        base_url: URL of Smartflow proxy (default port 7775)
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds (default 30)
        management_port: Port for management API (default 7778)
        compliance_port: Port for compliance API (default 7777)
        bridge_port: Port for hybrid bridge API (default 3500)
    
    Example:
        >>> async with SmartflowClient("http://192.81.214.94:7775") as sf:
        ...     # Simple chat
        ...     response = await sf.chat("What is AI?")
        ...     print(response)
        ...     
        ...     # Check cache stats
        ...     stats = await sf.get_cache_stats()
        ...     print(f"Hit rate: {stats.hit_rate:.1%}")
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        management_port: int = 7778,
        compliance_port: int = 7777,
        bridge_port: int = 3500,
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Extract host from base_url for other ports
        # e.g., "http://192.81.214.94:7775" -> "http://192.81.214.94"
        parts = self.base_url.rsplit(':', 1)
        if len(parts) == 2 and parts[1].isdigit():
            self._host = parts[0]
        else:
            self._host = self.base_url
        
        self.management_url = f"{self._host}:{management_port}"
        self.compliance_url = f"{self._host}:{compliance_port}"
        self.bridge_url = f"{self._host}:{bridge_port}"
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
    
    def _headers(self, extra: Dict[str, str] = None) -> Dict[str, str]:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            headers.update(extra)
        return headers
    
    async def _get(
        self, 
        url: str, 
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        await self._ensure_client()
        try:
            response = await self._client.get(
                url, 
                params=params, 
                headers=self._headers(headers)
            )
            data = response.json()
            raise_for_status(data, response.status_code)
            return data
        except httpx.ConnectError as e:
            raise SmartflowConnectionError(f"Failed to connect to {url}: {e}")
    
    async def _post(
        self, 
        url: str, 
        payload: Dict[str, Any],
        headers: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        await self._ensure_client()
        try:
            response = await self._client.post(
                url, 
                json=payload, 
                headers=self._headers(headers)
            )
            data = response.json()
            raise_for_status(data, response.status_code)
            return data
        except httpx.ConnectError as e:
            raise SmartflowConnectionError(f"Failed to connect to {url}: {e}")
    
    # =========================================================================
    # CORE AI METHODS
    # =========================================================================
    
    async def chat(
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
        
        Smartflow automatically handles:
        - Provider routing (best model selection)
        - Semantic caching (60-80% cost savings)
        - Compliance checking
        - Audit logging
        
        Args:
            message: User message
            model: Model to use (default "gpt-4o")
            system_prompt: Optional system prompt
            temperature: Sampling temperature (default 0.7)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to provider
        
        Returns:
            AI response text
        
        Example:
            >>> response = await sf.chat("Explain quantum computing")
            >>> print(response)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        response = await self.chat_completions(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.content
    
    async def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> AIResponse:
        """
        OpenAI-compatible chat completions endpoint.
        
        Fully compatible with existing OpenAI code - just change the base URL!
        
        Args:
            messages: List of message dicts with "role" and "content"
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            stream: Enable streaming (returns async iterator if True)
            **kwargs: Additional parameters
        
        Returns:
            AIResponse object with choices, usage, etc.
        
        Example:
            >>> response = await sf.chat_completions(
            ...     messages=[{"role": "user", "content": "Hello!"}],
            ...     model="gpt-4o"
            ... )
            >>> print(response.content)
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            **kwargs,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        url = f"{self.base_url}/v1/chat/completions"
        data = await self._post(url, payload)
        return AIResponse.from_dict(data)
    
    async def embeddings(
        self,
        input: str | List[str],
        model: str = "text-embedding-3-small",
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text.
        
        Args:
            input: Text or list of texts to embed
            model: Embedding model to use
        
        Returns:
            Dict with embeddings data
        """
        payload = {
            "model": model,
            "input": input if isinstance(input, list) else [input],
        }
        url = f"{self.base_url}/v1/embeddings"
        return await self._post(url, payload)
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of model info dicts
        """
        url = f"{self.base_url}/v1/models"
        data = await self._get(url)
        return data.get("data", [])
    
    # =========================================================================
    # ANTHROPIC METHODS
    # =========================================================================
    
    async def claude_message(
        self,
        message: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        system: Optional[str] = None,
        anthropic_key: Optional[str] = None,
    ) -> str:
        """
        Send a message to Claude via Anthropic API.
        
        Args:
            message: User message
            model: Claude model to use
            max_tokens: Maximum tokens
            system: System prompt
            anthropic_key: Anthropic API key (uses stored key if not provided)
        
        Returns:
            Claude's response text
        """
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": message}],
        }
        if system:
            payload["system"] = system
        
        headers = {
            "anthropic-version": "2023-06-01",
        }
        if anthropic_key:
            headers["x-api-key"] = anthropic_key
        
        url = f"{self.base_url}/v1/messages"
        data = await self._post(url, payload, headers=headers)
        
        # Extract content from Anthropic response format
        content = data.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "")
        return ""
    
    # =========================================================================
    # COMPLIANCE METHODS
    # =========================================================================
    
    async def check_compliance(
        self,
        content: str,
        policy: str = "enterprise_standard",
    ) -> ComplianceResult:
        """
        Check content for compliance issues.
        
        Scans for:
        - PII (emails, phone numbers, SSNs, etc.)
        - Policy violations
        - Regulatory issues (HIPAA, GDPR, SOC2)
        
        Args:
            content: Text to scan
            policy: Compliance policy to apply
        
        Returns:
            ComplianceResult with violations, risk score, etc.
        
        Example:
            >>> result = await sf.check_compliance("My SSN is 123-45-6789")
            >>> if result.has_violations:
            ...     print(f"Found: {result.violations}")
        """
        payload = {"content": content, "policy": policy}
        url = f"{self.compliance_url}/api/compliance/scan"
        data = await self._post(url, payload)
        
        return ComplianceResult(
            has_violations=not data.get("compliant", True),
            compliance_score=100 - (data.get("risk_score", 0) * 100),
            violations=data.get("violations", []),
            pii_detected=data.get("pii_detected", []),
            risk_level=self._risk_level_from_score(data.get("risk_score", 0)),
            recommendations=data.get("recommendations", []),
            redacted_content=data.get("redacted_content"),
        )
    
    def _risk_level_from_score(self, score: float) -> str:
        """Convert risk score to level."""
        if score < 0.25:
            return "low"
        elif score < 0.5:
            return "medium"
        elif score < 0.75:
            return "high"
        return "critical"
    
    async def redact_pii(self, content: str) -> str:
        """
        Automatically redact PII from content.
        
        Args:
            content: Text potentially containing PII
        
        Returns:
            Redacted text
        """
        result = await self.check_compliance(content)
        return result.redacted_content or content
    
    # =========================================================================
    # INTELLIGENT COMPLIANCE (ML-POWERED)
    # =========================================================================
    
    async def intelligent_scan(
        self,
        content: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> IntelligentScanResult:
        """
        Scan content using the ML-powered intelligent compliance engine.
        
        This uses Smartflow's adaptive learning system which includes:
        - Regex pattern matching (SSN, CC, email, phone, etc.)
        - ML embedding similarity for semantic violation detection
        - Behavioral analysis (user patterns, anomaly detection)
        - Organization baselines (deviation from org norms)
        
        Args:
            content: Text to scan for compliance issues
            user_id: Optional user ID for behavioral tracking
            org_id: Optional organization ID for org-level baselines
            context: Optional context (e.g., "customer_support", "sales")
        
        Returns:
            IntelligentScanResult with risk score, violations, and recommendations
        
        Example:
            >>> result = await sf.intelligent_scan(
            ...     "My SSN is 123-45-6789",
            ...     user_id="user123",
            ...     org_id="acme_corp"
            ... )
            >>> print(f"Risk: {result.risk_level}")
            >>> print(f"Action: {result.recommended_action}")
        """
        payload = {"content": content}
        if user_id:
            payload["user_id"] = user_id
        if org_id:
            payload["org_id"] = org_id
        if context:
            payload["context"] = context
        
        url = f"{self.compliance_url}/api/compliance/intelligent/scan"
        data = await self._post(url, payload)
        return IntelligentScanResult.from_dict(data)
    
    async def submit_compliance_feedback(
        self,
        scan_id: str,
        is_false_positive: bool,
        user_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit feedback on a compliance scan result.
        
        This feedback is used to train the ML model and reduce false positives.
        
        Args:
            scan_id: ID of the scan to provide feedback on
            is_false_positive: True if the detection was a false positive
            user_id: Optional user ID submitting feedback
            notes: Optional notes explaining the feedback
        
        Returns:
            Confirmation response
        
        Example:
            >>> await sf.submit_compliance_feedback(
            ...     scan_id="scan_abc123",
            ...     is_false_positive=True,
            ...     notes="This was a test phone number"
            ... )
        """
        payload = {
            "scan_id": scan_id,
            "is_false_positive": is_false_positive,
        }
        if user_id:
            payload["user_id"] = user_id
        if notes:
            payload["notes"] = notes
        
        url = f"{self.compliance_url}/api/compliance/intelligent/feedback"
        return await self._post(url, payload)
    
    async def get_learning_status(self, user_id: str) -> LearningStatus:
        """
        Get the learning status for a specific user.
        
        Args:
            user_id: User ID to check
        
        Returns:
            LearningStatus with progress info
        """
        url = f"{self.compliance_url}/api/compliance/learning/status/{user_id}"
        data = await self._get(url)
        return LearningStatus.from_dict(data)
    
    async def get_learning_summary(self) -> LearningSummary:
        """
        Get overall learning summary across all users.
        
        Returns:
            LearningSummary with aggregate learning progress
        """
        url = f"{self.compliance_url}/api/compliance/learning/summary"
        data = await self._get(url)
        return LearningSummary.from_dict(data)
    
    async def get_ml_stats(self) -> MLStats:
        """
        Get statistics about the ML compliance engine.
        
        Returns:
            MLStats with pattern counts and categories
        """
        url = f"{self.compliance_url}/api/compliance/intelligent/stats"
        data = await self._get(url)
        ml_data = data.get("ml_stats", data)
        return MLStats.from_dict(ml_data)
    
    async def get_org_summary(self) -> Dict[str, Any]:
        """
        Get organization-level compliance summary.
        
        Returns:
            Dict with org learning stats
        """
        url = f"{self.compliance_url}/api/compliance/org/summary"
        return await self._get(url)
    
    async def get_org_baseline(self, org_id: str) -> OrgBaseline:
        """
        Get the compliance baseline for a specific organization.
        
        Args:
            org_id: Organization ID
        
        Returns:
            OrgBaseline with org-level metrics
        """
        url = f"{self.compliance_url}/api/compliance/org/status/{org_id}"
        data = await self._get(url)
        return OrgBaseline.from_dict(data)
    
    async def get_persistence_stats(self) -> PersistenceStats:
        """
        Get Redis persistence statistics for compliance data.
        
        Returns:
            PersistenceStats with storage info
        """
        url = f"{self.compliance_url}/api/compliance/persistence/stats"
        data = await self._get(url)
        return PersistenceStats.from_dict(data.get("persistence", data))
    
    async def save_compliance_data(self) -> Dict[str, Any]:
        """
        Trigger manual save of compliance data to Redis.
        
        Returns:
            Confirmation response
        """
        url = f"{self.compliance_url}/api/compliance/persistence/save"
        return await self._post(url, {})
    
    async def get_intelligent_health(self) -> Dict[str, Any]:
        """
        Get health status of the intelligent compliance engine.
        
        Returns:
            Health status including ML engine, behavior analysis, etc.
        """
        url = f"{self.compliance_url}/api/compliance/intelligent/health"
        return await self._get(url)
    
    # =========================================================================
    # CACHE METHODS
    # =========================================================================
    
    async def get_cache_stats(self) -> CacheStats:
        """
        Get Smartflow cache statistics.
        
        Returns L1/L2/L3 hit rates, tokens saved, cost savings, etc.
        
        Returns:
            CacheStats object with cache metrics
        
        Example:
            >>> stats = await sf.get_cache_stats()
            >>> print(f"Hit rate: {stats.hit_rate:.1%}")
            >>> print(f"Tokens saved: {stats.tokens_saved:,}")
        """
        url = f"{self.management_url}/api/metacache/stats"
        data = await self._get(url)
        
        # Handle wrapped response
        if "data" in data:
            data = data["data"]
        
        return CacheStats.from_dict(data)
    
    # =========================================================================
    # HEALTH & MONITORING
    # =========================================================================
    
    async def health(self) -> Dict[str, Any]:
        """
        Quick health check of Smartflow proxy.
        
        Returns:
            Health status dict
        """
        url = f"{self.base_url}/health"
        return await self._get(url)
    
    async def health_comprehensive(self) -> SystemHealth:
        """
        Comprehensive health check including all services and providers.
        
        Returns:
            SystemHealth object with full status
        """
        url = f"{self.management_url}/api/health/comprehensive"
        data = await self._get(url)
        
        if "data" in data:
            data = data["data"]
        
        return SystemHealth.from_dict(data)
    
    async def get_provider_health(self) -> List[ProviderHealth]:
        """
        Get health status of all AI providers.
        
        Returns:
            List of ProviderHealth objects
        """
        url = f"{self.management_url}/api/providers/perf"
        data = await self._get(url)
        
        snapshots = data.get("data", {}).get("snapshots", [])
        return [ProviderHealth.from_dict(s) for s in snapshots]
    
    # =========================================================================
    # VAS LOGS (AUDIT)
    # =========================================================================
    
    async def get_logs(
        self,
        limit: int = 50,
        provider: Optional[str] = None,
    ) -> List[VASLog]:
        """
        Get VAS audit logs.
        
        Full audit trail of all AI interactions through Smartflow.
        
        Args:
            limit: Maximum logs to return
            provider: Filter by provider name
        
        Returns:
            List of VASLog objects
        """
        url = f"{self.management_url}/api/vas/logs"
        params = {"limit": limit}
        if provider:
            params["provider"] = provider
        
        data = await self._get(url, params=params)
        
        logs_data = data.get("data", [])
        return [VASLog.from_dict(log) for log in logs_data]
    
    async def get_logs_hybrid(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get VAS logs from hybrid bridge (Redis + MongoDB combined).
        
        Args:
            limit: Maximum logs to return
        
        Returns:
            List of log dicts
        """
        url = f"{self.bridge_url}/api/redis/logs"
        params = {"limit": limit}
        data = await self._get(url, params=params)
        return data.get("logs", [])
    
    # =========================================================================
    # ANALYTICS
    # =========================================================================
    
    async def get_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get usage analytics.
        
        Args:
            start_date: ISO format start date
            end_date: ISO format end date
        
        Returns:
            Analytics data dict
        """
        url = f"{self.bridge_url}/api/hybrid/analytics"
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self._get(url, params=params)
    
    # =========================================================================
    # ROUTING
    # =========================================================================
    
    async def get_routing_status(self) -> Dict[str, Any]:
        """
        Get current routing configuration and status.
        
        Returns:
            Routing status including active providers, failover state, etc.
        """
        url = f"{self.management_url}/api/routing/status"
        data = await self._get(url)
        return data.get("data", data)
    
    async def force_provider(
        self,
        provider: str,
        duration_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Force routing to a specific provider.
        
        Args:
            provider: Provider name ("openai", "anthropic", etc.)
            duration_seconds: How long to force (default 5 minutes)
        
        Returns:
            Confirmation response
        """
        url = f"{self.management_url}/api/routing/override"
        payload = {
            "provider": provider,
            "ttl_minutes": duration_seconds // 60,
        }
        return await self._post(url, payload)
    
    # =========================================================================
    # CHATBOT (Built-in Smartflow chatbot)
    # =========================================================================
    
    async def chatbot_query(self, query: str) -> Dict[str, Any]:
        """
        Query Smartflow's built-in chatbot for system info.
        
        The chatbot can answer questions about:
        - VAS logs and analytics
        - Cache performance
        - System health
        - Cost analysis
        
        Args:
            query: Natural language query (e.g., "show cache stats")
        
        Returns:
            Chatbot response
        
        Example:
            >>> result = await sf.chatbot_query("show me today's cache stats")
            >>> print(result["response"])
        """
        url = f"{self.base_url}/api/chatbot/query"
        payload = {"query": query}
        return await self._post(url, payload)
    
    # =========================================================================
    # CONTEXT MANAGER
    # =========================================================================
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# =============================================================================
# AGENT BUILDER
# =============================================================================

class SmartflowAgent:
    """
    A Smartflow-powered AI agent with built-in compliance, caching, and routing.
    
    SmartflowAgent wraps a SmartflowClient to provide higher-level abstractions
    for building AI applications, including:
    - Conversation memory
    - Automatic compliance scanning
    - Tool/function calling
    - Response caching
    
    Example:
        >>> async with SmartflowClient("http://smartflow:7775") as sf:
        ...     agent = SmartflowAgent(
        ...         client=sf,
        ...         name="CustomerSupport",
        ...         system_prompt="You are a helpful customer support agent.",
        ...         compliance_policy="enterprise_standard"
        ...     )
        ...     
        ...     response = await agent.chat("How do I reset my password?")
        ...     print(response)
    """
    
    def __init__(
        self,
        client: SmartflowClient,
        name: str = "SmartflowAgent",
        model: str = "gpt-4o",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        compliance_policy: str = "enterprise_standard",
        enable_compliance_scan: bool = True,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize a SmartflowAgent.
        
        Args:
            client: SmartflowClient instance
            name: Agent name for logging
            model: AI model to use
            system_prompt: System prompt for the agent
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            compliance_policy: Compliance policy to apply
            enable_compliance_scan: Scan inputs/outputs for compliance
            user_id: User ID for behavioral tracking
            org_id: Organization ID for org baselines
            tools: List of tools/functions the agent can call
        """
        self.client = client
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.compliance_policy = compliance_policy
        self.enable_compliance_scan = enable_compliance_scan
        self.user_id = user_id
        self.org_id = org_id
        self.tools = tools or []
        
        # Conversation memory
        self._messages: List[Dict[str, str]] = []
        if system_prompt:
            self._messages.append({"role": "system", "content": system_prompt})
    
    async def chat(
        self,
        message: str,
        scan_input: bool = True,
        scan_output: bool = True,
    ) -> str:
        """
        Send a message to the agent.
        
        Args:
            message: User message
            scan_input: Scan input for compliance (default True)
            scan_output: Scan output for compliance (default True)
        
        Returns:
            Agent's response
        
        Raises:
            SmartflowError: If compliance violation blocks the message
        """
        # Optionally scan input
        if self.enable_compliance_scan and scan_input:
            input_scan = await self.client.intelligent_scan(
                content=message,
                user_id=self.user_id,
                org_id=self.org_id,
            )
            if input_scan.recommended_action == "Block":
                raise SmartflowError(
                    f"Input blocked by compliance: {input_scan.explanation}"
                )
        
        # Add message to history
        self._messages.append({"role": "user", "content": message})
        
        # Get response
        response = await self.client.chat_completions(
            messages=self._messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        assistant_message = response.content
        
        # Optionally scan output
        if self.enable_compliance_scan and scan_output:
            output_scan = await self.client.intelligent_scan(
                content=assistant_message,
                user_id=self.user_id,
                org_id=self.org_id,
            )
            if output_scan.recommended_action == "Block":
                # Don't add to history, return warning
                return "[Response blocked due to compliance policy]"
        
        # Add response to history
        self._messages.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    def clear_history(self):
        """Clear conversation history, keeping system prompt."""
        self._messages = []
        if self.system_prompt:
            self._messages.append({"role": "system", "content": self.system_prompt})
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self._messages.copy()
    
    @property
    def message_count(self) -> int:
        """Get number of messages in history."""
        return len(self._messages)


class SmartflowWorkflow:
    """
    A workflow orchestrator for chaining AI operations.
    
    SmartflowWorkflow allows you to define and execute multi-step AI workflows
    with branching, parallel execution, and error handling.
    
    Example:
        >>> workflow = SmartflowWorkflow(client, name="SupportTicketFlow")
        >>> 
        >>> workflow.add_step("classify", action="chat",
        ...     config={"prompt": "Classify this ticket: {input}"})
        >>> workflow.add_step("route", action="condition",
        ...     config={"field": "category", "cases": {...}})
        >>> 
        >>> result = await workflow.execute({"input": ticket_text})
    """
    
    def __init__(
        self,
        client: SmartflowClient,
        name: str = "SmartflowWorkflow",
    ):
        """
        Initialize a workflow.
        
        Args:
            client: SmartflowClient instance
            name: Workflow name for logging
        """
        self.client = client
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.entry_step: Optional[str] = None
    
    def add_step(
        self,
        name: str,
        action: str,
        config: Dict[str, Any] = None,
        next_steps: List[str] = None,
        on_error: Optional[str] = None,
    ) -> "SmartflowWorkflow":
        """
        Add a step to the workflow.
        
        Args:
            name: Step name
            action: Action type ("chat", "compliance_check", "condition", etc.)
            config: Step configuration
            next_steps: Names of subsequent steps
            on_error: Step to execute on error
        
        Returns:
            Self for chaining
        """
        step = WorkflowStep(
            name=name,
            action=action,
            config=config or {},
            next_steps=next_steps or [],
            on_error=on_error,
        )
        self.steps[name] = step
        
        # First step added becomes entry
        if self.entry_step is None:
            self.entry_step = name
        
        return self
    
    def set_entry(self, step_name: str) -> "SmartflowWorkflow":
        """Set the entry step for the workflow."""
        if step_name not in self.steps:
            raise ValueError(f"Step '{step_name}' not found in workflow")
        self.entry_step = step_name
        return self
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        max_iterations: int = 100,
    ) -> WorkflowResult:
        """
        Execute the workflow.
        
        Args:
            input_data: Initial input data
            max_iterations: Maximum steps to execute (prevent infinite loops)
        
        Returns:
            WorkflowResult with output and execution details
        """
        if not self.entry_step:
            return WorkflowResult(
                success=False,
                output=None,
                errors=["No entry step defined"],
            )
        
        context = {"input": input_data, "output": None}
        steps_executed = []
        errors = []
        current_step = self.entry_step
        iterations = 0
        total_tokens = 0
        
        import time
        start_time = time.time()
        
        while current_step and iterations < max_iterations:
            iterations += 1
            step = self.steps.get(current_step)
            
            if not step:
                errors.append(f"Step '{current_step}' not found")
                break
            
            steps_executed.append(current_step)
            
            try:
                result, next_step = await self._execute_step(step, context)
                context["output"] = result
                current_step = next_step
            except Exception as e:
                errors.append(f"Error in step '{current_step}': {str(e)}")
                if step.on_error:
                    current_step = step.on_error
                else:
                    break
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return WorkflowResult(
            success=len(errors) == 0,
            output=context.get("output"),
            steps_executed=steps_executed,
            errors=errors,
            total_tokens=total_tokens,
            execution_time_ms=execution_time_ms,
        )
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> tuple:
        """Execute a single workflow step."""
        action = step.action
        config = step.config
        
        if action == "chat":
            prompt = config.get("prompt", "{input}")
            formatted_prompt = self._format_template(prompt, context)
            
            response = await self.client.chat(
                message=formatted_prompt,
                model=config.get("model", "gpt-4o"),
                temperature=config.get("temperature", 0.7),
            )
            
            next_step = step.next_steps[0] if step.next_steps else None
            return response, next_step
        
        elif action == "compliance_check":
            content = config.get("content", context.get("output", ""))
            if isinstance(content, str):
                content = self._format_template(content, context)
            
            result = await self.client.intelligent_scan(content=content)
            
            next_step = step.next_steps[0] if step.next_steps else None
            return result, next_step
        
        elif action == "condition":
            field = config.get("field", "output")
            value = context.get(field)
            cases = config.get("cases", {})
            default = config.get("default")
            
            next_step = cases.get(str(value), default)
            return value, next_step
        
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _format_template(self, template: str, context: Dict[str, Any]) -> str:
        """Format a template string with context values."""
        result = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result

