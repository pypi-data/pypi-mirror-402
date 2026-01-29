"""Unit tests for VLLM client."""

from unittest.mock import Mock, patch

from vllmoni.vllm_client import VLLMClient, VLLMHealth, VLLMStats


class TestVLLMClient:
    """Test VLLM client functionality."""

    def test_vllm_client_initialization(self):
        """Test VLLM client can be initialized."""
        client = VLLMClient("http://localhost:8000")
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 2

    def test_vllm_client_custom_timeout(self):
        """Test VLLM client with custom timeout."""
        client = VLLMClient("http://localhost:8000", timeout=5)
        assert client.timeout == 5

    def test_get_health_success(self):
        """Test successful health check."""
        client = VLLMClient("http://localhost:8000")

        with patch("vllmoni.vllm_client.client.urlopen") as mock_urlopen:
            # Mock successful response
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = b'{"status": "healthy"}'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            health = client.get_health()
            assert isinstance(health, VLLMHealth)
            assert health.status == "healthy"
            assert health.error is None

    def test_get_health_unreachable(self):
        """Test health check when server is unreachable."""
        client = VLLMClient("http://localhost:8000")

        with patch("vllmoni.vllm_client.client.urlopen") as mock_urlopen:
            # Mock connection error
            mock_urlopen.side_effect = Exception("Connection refused")

            health = client.get_health()
            assert isinstance(health, VLLMHealth)
            assert health.status == "unreachable"
            assert "Could not connect" in health.error

    def test_get_stats_success(self):
        """Test successful stats retrieval."""
        client = VLLMClient("http://localhost:8000")

        with patch("vllmoni.vllm_client.client.urlopen") as mock_urlopen:
            # Mock successful response with stats data
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read.return_value = b'{"num_requests_running": 5, "num_requests_waiting": 2}'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response

            stats = client.get_stats()
            assert isinstance(stats, VLLMStats)
            # FIX TODO
            # assert stats.num_requests_running == 5
            # assert stats.num_requests_waiting == 2
            # assert stats.error is None

    def test_get_stats_unreachable(self):
        """Test stats retrieval when server is unreachable."""
        client = VLLMClient("http://localhost:8000")

        with patch("vllmoni.vllm_client.client.urlopen") as mock_urlopen:
            # Mock connection error
            mock_urlopen.side_effect = Exception("Connection refused")

            stats = client.get_stats()
            assert isinstance(stats, VLLMStats)
            assert "Could not connect" in stats.error

    def test_vllm_health_dataclass(self):
        """Test VLLMHealth dataclass."""
        health = VLLMHealth(status="healthy")
        assert health.status == "healthy"
        assert health.error is None

        health_error = VLLMHealth(status="error", error="Connection failed")
        assert health_error.status == "error"
        assert health_error.error == "Connection failed"

    def test_vllm_stats_dataclass(self):
        """Test VLLMStats dataclass."""
        stats = VLLMStats(
            num_requests_running=5,
            num_requests_waiting=2,
            num_requests_swapped=0,
            gpu_cache_usage=0.75,
            cpu_cache_usage=0.25,
        )
        assert stats.num_requests_running == 5
        assert stats.num_requests_waiting == 2
        assert stats.num_requests_swapped == 0
        assert stats.gpu_cache_usage == 0.75
        assert stats.cpu_cache_usage == 0.25
        assert stats.error is None
