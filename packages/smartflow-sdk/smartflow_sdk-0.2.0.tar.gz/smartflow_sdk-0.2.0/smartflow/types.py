"""
Smartflow SDK Type Definitions.

Pydantic models for request/response types.
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    """A single message in a chat conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class AIRequest:
    """Request to an AI provider."""
    messages: List[ChatMessage]
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        data = {
            "model": self.model,
            "messages": [
                {"role": m.role, "content": m.content}
                for m in self.messages
            ],
            "temperature": self.temperature,
            "stream": self.stream,
        }
        if self.max_tokens:
            data["max_tokens"] = self.max_tokens
        if self.tools:
            data["tools"] = self.tools
        return data


@dataclass
class Usage:
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


@dataclass
class Choice:
    """A single choice in an AI response."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


@dataclass
class AIResponse:
    """Response from an AI provider."""
    id: str
    model: str
    choices: List[Choice]
    usage: Usage
    created: int
    provider: Optional[str] = None
    cached: bool = False
    cache_hit_type: Optional[str] = None  # "exact", "semantic", or None
    
    @property
    def content(self) -> str:
        """Get the content of the first choice."""
        if self.choices:
            return self.choices[0].message.content
        return ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIResponse":
        """Create from API response dictionary."""
        choices = []
        for c in data.get("choices", []):
            msg = c.get("message", {})
            choices.append(Choice(
                index=c.get("index", 0),
                message=ChatMessage(
                    role=msg.get("role", "assistant"),
                    content=msg.get("content", ""),
                ),
                finish_reason=c.get("finish_reason"),
            ))
        
        usage_data = data.get("usage", {})
        usage = Usage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            cached_tokens=usage_data.get("cached_tokens", 0),
        )
        
        return cls(
            id=data.get("id", ""),
            model=data.get("model", ""),
            choices=choices,
            usage=usage,
            created=data.get("created", 0),
            provider=data.get("provider"),
            cached=data.get("cached", False),
            cache_hit_type=data.get("cache_hit_type"),
        )


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    has_violations: bool
    compliance_score: float  # 0-100
    violations: List[str] = field(default_factory=list)
    pii_detected: List[str] = field(default_factory=list)
    risk_level: str = "low"  # "low", "medium", "high", "critical"
    recommendations: List[str] = field(default_factory=list)
    redacted_content: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComplianceResult":
        """Create from API response dictionary."""
        return cls(
            has_violations=data.get("has_violations", False),
            compliance_score=data.get("compliance_score", 100.0),
            violations=data.get("violations", []),
            pii_detected=data.get("pii_detected", []),
            risk_level=data.get("risk_level", "low"),
            recommendations=data.get("recommendations", []),
            redacted_content=data.get("redacted_content"),
        )


@dataclass
class CacheStats:
    """Cache statistics from Smartflow."""
    hits: int
    misses: int
    exact_matches: int
    semantic_matches: int
    tokens_saved: int
    cost_saved_cents: float
    hit_rate: float
    entries: int
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheStats":
        """Create from API response dictionary."""
        hits = data.get("hits", 0) or data.get("cache_hits", 0)
        misses = data.get("misses", 0) or data.get("cache_misses", 0)
        total = hits + misses
        
        return cls(
            hits=hits,
            misses=misses,
            exact_matches=data.get("exact_matches", 0),
            semantic_matches=data.get("semantic_matches", 0),
            tokens_saved=data.get("tokens_saved", 0),
            cost_saved_cents=data.get("cost_saved_cents", 0.0),
            hit_rate=hits / total if total > 0 else 0.0,
            entries=data.get("entries", 0),
            l1_hits=data.get("l1_hits", 0),
            l2_hits=data.get("l2_hits", 0),
            l3_hits=data.get("l3_hits", 0),
        )


@dataclass
class ProviderHealth:
    """Health status of an AI provider."""
    provider: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: float
    success_rate: float
    error_rate: float
    rate_limit_rate: float
    requests_total: int
    last_updated: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderHealth":
        """Create from API response dictionary."""
        return cls(
            provider=data.get("provider", "unknown"),
            status=data.get("status", "unknown"),
            latency_ms=data.get("avg_latency_ms", 0.0),
            success_rate=data.get("success_rate", 0.0),
            error_rate=data.get("error_rate", 0.0),
            rate_limit_rate=data.get("rate_limit_rate", 0.0),
            requests_total=data.get("requests", 0),
            last_updated=data.get("last_updated"),
        )


@dataclass
class VASLog:
    """Value-Added Services log entry."""
    request_id: str
    timestamp: str
    provider: Optional[str]
    model: Optional[str]
    request_content: Optional[str]
    response_content: Optional[str]
    tokens_used: int
    latency_ms: float
    cached: bool
    compliance: Optional[ComplianceResult] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VASLog":
        """Create from API response dictionary."""
        compliance_data = data.get("compliance")
        compliance = ComplianceResult.from_dict(compliance_data) if compliance_data else None
        
        return cls(
            request_id=data.get("request_id", ""),
            timestamp=data.get("timestamp", ""),
            provider=data.get("provider"),
            model=data.get("model"),
            request_content=data.get("request_content"),
            response_content=data.get("response_content"),
            tokens_used=data.get("tokens_used", 0),
            latency_ms=data.get("latency_ms", 0.0),
            cached=data.get("cached", False),
            compliance=compliance,
        )


@dataclass
class PolicyResult:
    """Result of a policy check."""
    allowed: bool
    policy_id: Optional[str]
    policy_name: Optional[str]
    violations: List[str] = field(default_factory=list)
    action: str = "allow"  # "allow", "block", "modify", "warn"
    modified_content: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyResult":
        """Create from API response dictionary."""
        return cls(
            allowed=data.get("allowed", True),
            policy_id=data.get("policy_id"),
            policy_name=data.get("policy_name"),
            violations=data.get("violations", []),
            action=data.get("action", "allow"),
            modified_content=data.get("modified_content"),
        )


@dataclass  
class SystemHealth:
    """Overall system health status."""
    status: str  # "healthy", "degraded", "unhealthy"
    uptime_seconds: int
    version: str
    providers: List[ProviderHealth]
    cache: CacheStats
    timestamp: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemHealth":
        """Create from API response dictionary."""
        providers = [
            ProviderHealth.from_dict(p) 
            for p in data.get("providers", [])
        ]
        cache_data = data.get("cache", {})
        
        return cls(
            status=data.get("status", "unknown"),
            uptime_seconds=data.get("uptime_seconds", 0),
            version=data.get("version", "unknown"),
            providers=providers,
            cache=CacheStats.from_dict(cache_data),
            timestamp=data.get("timestamp", ""),
        )


# ==============================================================================
# INTELLIGENT COMPLIANCE TYPES (ML-POWERED)
# ==============================================================================

@dataclass
class IntelligentScanResult:
    """
    Result from the intelligent ML-powered compliance scan.
    
    This uses Smartflow's adaptive learning engine which includes:
    - Regex pattern matching
    - ML embedding similarity
    - Behavioral analysis
    - Organization baselines
    """
    has_violations: bool
    risk_score: float  # 0.0 to 1.0
    recommended_action: str  # "Allow", "AllowAndLog", "Block", "Review"
    explanation: str
    regex_violations: List[Dict[str, Any]] = field(default_factory=list)
    ml_violations: List[Dict[str, Any]] = field(default_factory=list)
    behavior_deviations: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_us: int = 0
    
    @property
    def risk_level(self) -> str:
        """Get human-readable risk level."""
        if self.risk_score < 0.25:
            return "low"
        elif self.risk_score < 0.5:
            return "medium"
        elif self.risk_score < 0.75:
            return "high"
        return "critical"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntelligentScanResult":
        """Create from API response dictionary."""
        return cls(
            has_violations=data.get("has_violations", False),
            risk_score=data.get("risk_score", 0.0),
            recommended_action=data.get("recommended_action", "Allow"),
            explanation=data.get("explanation", ""),
            regex_violations=data.get("regex_violations", []),
            ml_violations=data.get("ml_violations", []),
            behavior_deviations=data.get("behavior_deviations", []),
            processing_time_us=data.get("processing_time_us", 0),
        )


@dataclass
class LearningStatus:
    """User's compliance learning status."""
    user_id: str
    org_id: Optional[str]
    days_tracked: int
    total_requests: int
    learning_complete: bool
    learning_period_days: int
    progress_percent: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningStatus":
        """Create from API response dictionary."""
        return cls(
            user_id=data.get("user_id", ""),
            org_id=data.get("org_id"),
            days_tracked=data.get("days_tracked", 0),
            total_requests=data.get("total_requests", 0),
            learning_complete=data.get("learning_complete", False),
            learning_period_days=data.get("learning_period_days", 14),
            progress_percent=data.get("progress_percent", 0.0),
        )


@dataclass
class LearningSummary:
    """Summary of compliance learning across all users."""
    total_users: int
    users_learning_complete: int
    users_in_learning: int
    average_progress_percent: float
    config_learning_days: int
    config_min_samples: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningSummary":
        """Create from API response dictionary."""
        return cls(
            total_users=data.get("total_users", 0),
            users_learning_complete=data.get("users_learning_complete", 0),
            users_in_learning=data.get("users_in_learning", 0),
            average_progress_percent=data.get("average_progress_percent", 0.0),
            config_learning_days=data.get("config_learning_days", 14),
            config_min_samples=data.get("config_min_samples", 20),
        )


@dataclass
class MLStats:
    """Statistics about the ML compliance engine."""
    total_patterns: int
    builtin_patterns: int
    learned_patterns: int
    patterns_by_category: Dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MLStats":
        """Create from API response dictionary."""
        return cls(
            total_patterns=data.get("total_patterns", 0),
            builtin_patterns=data.get("builtin_patterns", 0),
            learned_patterns=data.get("learned_patterns", 0),
            patterns_by_category=data.get("patterns_by_category", {}),
            average_confidence=data.get("average_confidence", 0.0),
        )


@dataclass
class OrgBaseline:
    """Organization-level compliance baseline."""
    org_id: str
    user_count: int
    total_requests: int
    avg_requests_per_user_day: float
    violation_rate: float
    top_violation_types: List[str] = field(default_factory=list)
    learning_complete: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrgBaseline":
        """Create from API response dictionary."""
        return cls(
            org_id=data.get("org_id", ""),
            user_count=data.get("user_count", 0),
            total_requests=data.get("total_requests", 0),
            avg_requests_per_user_day=data.get("avg_requests_per_user_day", 0.0),
            violation_rate=data.get("violation_rate", 0.0),
            top_violation_types=data.get("top_violation_types", []),
            learning_complete=data.get("learning_complete", False),
        )


@dataclass
class PersistenceStats:
    """Redis persistence statistics for compliance data."""
    enabled: bool
    user_profiles_stored: int
    org_baselines_stored: int
    learned_patterns_stored: int
    profile_ttl_days: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersistenceStats":
        """Create from API response dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            user_profiles_stored=data.get("user_profiles_stored", 0),
            org_baselines_stored=data.get("org_baselines_stored", 0),
            learned_patterns_stored=data.get("learned_patterns_stored", 0),
            profile_ttl_days=data.get("profile_ttl_days", 90),
        )


# ==============================================================================
# AGENT BUILDING TYPES
# ==============================================================================

@dataclass
class AgentConfig:
    """Configuration for a Smartflow-powered agent."""
    name: str
    description: str = ""
    model: str = "gpt-4o"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)
    compliance_policy: str = "enterprise_standard"
    enable_caching: bool = True
    enable_logging: bool = True
    fallback_provider: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": self.tools,
            "compliance_policy": self.compliance_policy,
            "enable_caching": self.enable_caching,
            "enable_logging": self.enable_logging,
            "fallback_provider": self.fallback_provider,
        }


@dataclass
class WorkflowStep:
    """A single step in an agent workflow."""
    name: str
    action: str  # "chat", "tool_call", "compliance_check", "condition", "parallel"
    config: Dict[str, Any] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)
    on_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "action": self.action,
            "config": self.config,
            "next_steps": self.next_steps,
            "on_error": self.on_error,
        }


@dataclass
class WorkflowResult:
    """Result of executing a workflow."""
    success: bool
    output: Any
    steps_executed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    total_tokens: int = 0
    total_cost_cents: float = 0.0
    execution_time_ms: float = 0.0

