# Smartflow Python SDK

The official Python SDK for [Smartflow](https://smartflow.ai) - the enterprise AI orchestration, caching, compliance, and governance platform.

## Features

- **🚀 Simple API** - Chat, embeddings, and completions with one line of code
- **💰 60-80% Cost Savings** - 3-layer semantic caching (L1/L2/L3)
- **🛡️ ML-Powered Compliance** - Intelligent PII detection with adaptive learning
- **🔄 Automatic Failover** - Multi-provider routing with intelligent fallback
- **📊 Full Audit Trail** - VAS logs for every AI interaction
- **🤖 Agent Builder** - Create AI agents with built-in compliance
- **📈 Workflow Orchestration** - Chain AI operations with branching and error handling

## Installation

```bash
pip install smartflow-sdk
```

## Quick Start

### Async Usage (Recommended)

```python
import asyncio
from smartflow import SmartflowClient

async def main():
    async with SmartflowClient("http://your-smartflow:7775") as sf:
        # Simple chat
        response = await sf.chat("What is machine learning?")
        print(response)
        
        # Check cache stats
        stats = await sf.get_cache_stats()
        print(f"Cache hit rate: {stats.hit_rate:.1%}")
        print(f"Tokens saved: {stats.tokens_saved:,}")

asyncio.run(main())
```

### Sync Usage

```python
from smartflow import SyncSmartflowClient

sf = SyncSmartflowClient("http://your-smartflow:7775")

response = sf.chat("Explain quantum computing")
print(response)

sf.close()
```

### OpenAI Drop-in Replacement

Just change the `base_url` - your existing OpenAI code works with Smartflow!

```python
from openai import OpenAI

# Point to Smartflow instead of OpenAI
client = OpenAI(
    base_url="http://your-smartflow:7775/v1",
    api_key="your-key"  # Or use Smartflow's stored keys
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Intelligent Compliance (ML-Powered)

Smartflow's adaptive learning compliance engine provides:

- **Regex Pattern Matching** - SSN, credit cards, emails, phone numbers, etc.
- **ML Embedding Similarity** - Semantic violation detection
- **Behavioral Analysis** - User pattern tracking and anomaly detection
- **Organization Baselines** - Deviation detection from org norms

```python
async with SmartflowClient("http://your-smartflow:7775") as sf:
    # Scan content for compliance issues
    result = await sf.intelligent_scan(
        content="My SSN is 123-45-6789 and my email is john@example.com",
        user_id="user123",
        org_id="acme_corp"
    )
    
    print(f"Risk Score: {result.risk_score:.2f}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Action: {result.recommended_action}")
    print(f"Explanation: {result.explanation}")
    
    # Check regex violations
    for violation in result.regex_violations:
        print(f"  - {violation['violation_type']}: {violation['severity']}")
    
    # Submit feedback to improve detection
    await sf.submit_compliance_feedback(
        scan_id="scan_abc123",
        is_false_positive=True,
        notes="This was a test number"
    )
    
    # Get learning status
    learning = await sf.get_learning_summary()
    print(f"Users tracked: {learning.total_users}")
    print(f"Learning complete: {learning.users_learning_complete}")
    
    # Get ML stats
    ml_stats = await sf.get_ml_stats()
    print(f"Total patterns: {ml_stats.total_patterns}")
    print(f"Learned patterns: {ml_stats.learned_patterns}")
```

## Building AI Agents

Create AI agents with built-in compliance scanning and conversation memory:

```python
from smartflow import SmartflowClient, SmartflowAgent

async with SmartflowClient("http://your-smartflow:7775") as sf:
    agent = SmartflowAgent(
        client=sf,
        name="CustomerSupport",
        model="gpt-4o",
        system_prompt="""You are a helpful customer support agent for TechCorp.
        Be professional, friendly, and always protect customer data.""",
        compliance_policy="enterprise_standard",
        enable_compliance_scan=True,
        user_id="support_agent_1",
        org_id="techcorp"
    )
    
    # Chat with automatic compliance scanning
    response = await agent.chat("How do I reset my password?")
    print(response)
    
    # Conversation memory is maintained
    response = await agent.chat("What about two-factor authentication?")
    print(response)
    
    # Get conversation history
    history = agent.get_history()
    print(f"Messages: {len(history)}")
    
    # Clear and start fresh
    agent.clear_history()
```

## Workflow Orchestration

Chain AI operations with branching, parallel execution, and error handling:

```python
from smartflow import SmartflowClient, SmartflowWorkflow

async with SmartflowClient("http://your-smartflow:7775") as sf:
    workflow = SmartflowWorkflow(sf, name="TicketClassification")
    
    # Step 1: Classify the ticket
    workflow.add_step(
        name="classify",
        action="chat",
        config={
            "prompt": "Classify this support ticket into one of: billing, technical, account. Ticket: {input}",
            "model": "gpt-4o-mini"
        },
        next_steps=["route"]
    )
    
    # Step 2: Route based on classification
    workflow.add_step(
        name="route",
        action="condition",
        config={
            "field": "output",
            "cases": {
                "billing": "billing_response",
                "technical": "technical_response",
                "account": "account_response"
            },
            "default": "general_response"
        }
    )
    
    # Execute the workflow
    result = await workflow.execute({"input": "My payment failed yesterday"})
    
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Steps executed: {result.steps_executed}")
    print(f"Execution time: {result.execution_time_ms:.1f}ms")
```

## Monitoring & Analytics

```python
async with SmartflowClient("http://your-smartflow:7775") as sf:
    # System health
    health = await sf.health_comprehensive()
    print(f"Status: {health.status}")
    print(f"Uptime: {health.uptime_seconds / 3600:.1f} hours")
    
    # Provider health
    providers = await sf.get_provider_health()
    for p in providers:
        print(f"{p.provider}: {p.status} ({p.latency_ms:.0f}ms)")
    
    # Cache statistics
    cache = await sf.get_cache_stats()
    print(f"Hit rate: {cache.hit_rate:.1%}")
    print(f"L1 hits: {cache.l1_hits}")
    print(f"L2 hits: {cache.l2_hits}")
    print(f"Tokens saved: {cache.tokens_saved:,}")
    
    # Audit logs
    logs = await sf.get_logs(limit=10)
    for log in logs:
        print(f"{log.timestamp}: {log.provider}/{log.model} - {log.tokens_used} tokens")
```

## Configuration

### Client Options

```python
sf = SmartflowClient(
    base_url="http://smartflow:7775",      # Proxy URL
    api_key="your-api-key",                 # Optional API key
    timeout=30.0,                           # Request timeout
    management_port=7778,                   # Management API port
    compliance_port=7777,                   # Compliance API port
    bridge_port=3500,                       # Hybrid bridge port
)
```

### Environment Variables

```bash
export SMARTFLOW_URL="http://your-smartflow:7775"
export SMARTFLOW_API_KEY="your-key"
```

## API Reference

### SmartflowClient Methods

| Method | Description |
|--------|-------------|
| `chat()` | Simple chat with AI |
| `chat_completions()` | OpenAI-compatible completions |
| `embeddings()` | Generate text embeddings |
| `claude_message()` | Anthropic Claude API |
| `intelligent_scan()` | ML-powered compliance scan |
| `check_compliance()` | Basic compliance check |
| `get_cache_stats()` | Cache hit rates and savings |
| `health()` | Quick health check |
| `health_comprehensive()` | Full system health |
| `get_logs()` | VAS audit logs |
| `get_provider_health()` | Provider status |

### SmartflowAgent Methods

| Method | Description |
|--------|-------------|
| `chat()` | Chat with compliance scanning |
| `clear_history()` | Reset conversation |
| `get_history()` | Get conversation history |

### SmartflowWorkflow Methods

| Method | Description |
|--------|-------------|
| `add_step()` | Add a workflow step |
| `set_entry()` | Set entry point |
| `execute()` | Run the workflow |

## Examples

See the [examples/](./examples/) directory for more:

- `simple_chat.py` - Basic chat usage
- `compliance_check.py` - PII detection and redaction
- `system_monitoring.py` - Health and analytics
- `openai_drop_in.py` - OpenAI compatibility
- `agent_example.py` - Building AI agents
- `workflow_example.py` - Workflow orchestration

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Support

- Documentation: https://docs.smartflow.ai/sdk/python
- Issues: https://github.com/langsmart/smartflow-sdk-python/issues
- Email: support@smartflow.ai

---

Built with ❤️ by [Langsmart, Inc.](https://smartflow.ai)
