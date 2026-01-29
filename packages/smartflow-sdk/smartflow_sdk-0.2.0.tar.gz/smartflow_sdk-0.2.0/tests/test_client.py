"""
Tests for SmartflowClient.

Run with: pytest tests/
"""

import pytest
from smartflow import SmartflowClient, SyncSmartflowClient
from smartflow.types import CacheStats, AIResponse


class TestSmartflowClient:
    """Tests for async SmartflowClient."""
    
    def test_init(self):
        """Test client initialization."""
        client = SmartflowClient("http://localhost:7775")
        assert client.base_url == "http://localhost:7775"
        assert client.api_key is None
        assert client.timeout == 30.0
    
    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = SmartflowClient(
            "http://localhost:7775",
            api_key="test-key",
            timeout=60.0,
        )
        assert client.api_key == "test-key"
        assert client.timeout == 60.0
    
    def test_port_extraction(self):
        """Test that ports are correctly extracted from base URL."""
        client = SmartflowClient("http://192.168.1.1:7775")
        assert "7778" in client.management_url
        assert "7777" in client.compliance_url
        assert "3500" in client.bridge_url


class TestSyncSmartflowClient:
    """Tests for sync SmartflowClient."""
    
    def test_init(self):
        """Test sync client initialization."""
        client = SyncSmartflowClient("http://localhost:7775")
        assert client._async_client.base_url == "http://localhost:7775"


class TestTypes:
    """Tests for SDK types."""
    
    def test_cache_stats_from_dict(self):
        """Test CacheStats.from_dict()."""
        data = {
            "cache_hits": 100,
            "cache_misses": 50,
            "exact_matches": 60,
            "semantic_matches": 40,
            "tokens_saved": 10000,
            "cost_saved_cents": 50.0,
            "entries": 500,
        }
        stats = CacheStats.from_dict(data)
        
        assert stats.hits == 100
        assert stats.misses == 50
        assert stats.exact_matches == 60
        assert stats.semantic_matches == 40
        assert stats.tokens_saved == 10000
        assert abs(stats.hit_rate - 0.667) < 0.01
    
    def test_ai_response_from_dict(self):
        """Test AIResponse.from_dict()."""
        data = {
            "id": "chatcmpl-123",
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello!"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
            "created": 1234567890,
        }
        response = AIResponse.from_dict(data)
        
        assert response.id == "chatcmpl-123"
        assert response.model == "gpt-4o"
        assert response.content == "Hello!"
        assert response.usage.total_tokens == 15


# Integration tests (require running Smartflow instance)
@pytest.mark.integration
class TestIntegration:
    """Integration tests - require running Smartflow."""
    
    @pytest.fixture
    def client(self):
        return SmartflowClient("http://192.81.214.94:7775")
    
    @pytest.mark.asyncio
    async def test_health(self, client):
        """Test health endpoint."""
        async with client:
            health = await client.health()
            assert "status" in health
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, client):
        """Test cache stats endpoint."""
        async with client:
            stats = await client.get_cache_stats()
            assert isinstance(stats, CacheStats)

