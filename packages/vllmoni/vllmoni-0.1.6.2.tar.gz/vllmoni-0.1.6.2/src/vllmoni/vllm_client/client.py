"""VLLM API client for health and metrics endpoints."""

import json
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from vllmoni.utils.logger import logger


@dataclass
class VLLMHealth:
    """VLLM Health status."""

    status: str = "unknown"
    error: Optional[str] = None


@dataclass
class VLLMStats:
    """VLLM Statistics."""

    num_requests_running: int = 0
    num_requests_waiting: int = 0
    num_requests_swapped: int = 0
    gpu_cache_usage: float = 0.0
    cpu_cache_usage: float = 0.0
    error: Optional[str] = None


class VLLMClient:
    """Client for VLLM API endpoints."""

    def __init__(self, base_url: str, timeout: int = 2):
        """Initialize VLLM client.

        Args:
            base_url: Base URL of the VLLM server (e.g., http://localhost:8000)
            timeout: Request timeout in seconds

        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _make_request(self, endpoint: str) -> Optional[dict]:
        """Make HTTP request to VLLM endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Response data as dict or None if request fails

        """
        try:
            url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
            req = Request(url)
            with urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
                return None
        except Exception as e:
            logger.debug(f"VLLM API request failed for {endpoint}: {e}")
            return None

    def get_health(self) -> VLLMHealth:
        """Get health status from VLLM server.

        Returns:
            VLLMHealth object with status information

        """
        # Try /health endpoint first, then /v1/health as fallback
        for endpoint in ["/health", "/v1/health"]:
            data = self._make_request(endpoint)
            if data is not None and isinstance(data, dict):
                # VLLM typically returns {} for healthy status or {"status": "ok"}
                status = data.get("status", "healthy")
                return VLLMHealth(status=status)

        return VLLMHealth(status="unreachable", error="Could not connect to health endpoint")

    def get_stats(self) -> VLLMStats:
        """Get statistics from VLLM server (v0.7.0).

        Parses Prometheus text format from the /metrics endpoint.
        """
        response_text = self._make_request("/metrics")

        if response_text is None:
            return VLLMStats(error="Could not connect to metrics endpoint")

        try:
            # Map of internal field names to vLLM Prometheus metric names
            metric_mapping = {
                "num_requests_running": r"vllm:num_requests_running(?:\{.*?\})?\s+(\d+)",
                "num_requests_waiting": r"vllm:num_requests_waiting(?:\{.*?\})?\s+(\d+)",
                "num_requests_swapped": r"vllm:num_requests_swapped(?:\{.*?\})?\s+(\d+)",
                "gpu_cache_usage": r"vllm:gpu_cache_usage_perc(?:\{.*?\})?\s+([\d\.]+)",
                "cpu_cache_usage": r"vllm:cpu_cache_usage_perc(?:\{.*?\})?\s+([\d\.]+)",
            }

            stats_data = {}
            for field, pattern in metric_mapping.items():
                match = re.search(pattern, response_text)
                if match:
                    # Convert to float first, then int for count fields if necessary
                    val = float(match.group(1))
                    stats_data[field] = int(val) if "num_" in field else val
                else:
                    stats_data[field] = 0

            return VLLMStats(**stats_data)

        except Exception as e:
            return VLLMStats(error=f"Failed to parse metrics: {str(e)}")
