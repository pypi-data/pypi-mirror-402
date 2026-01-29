"""
XSource API Client.

Async HTTP client for communicating with XSource Security API.
"""

import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from .config import get_config, get_credentials, Credentials


class APIError(Exception):
    """API error with status code and message."""

    def __init__(self, status_code: int, message: str, detail: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"[{status_code}] {message}")


class XSourceAPI:
    """XSource Security API Client."""

    def __init__(self, credentials: Optional[Credentials] = None):
        self.config = get_config()
        self.credentials = credentials or get_credentials()
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.credentials.auth_header:
                headers["Authorization"] = self.credentials.auth_header

            self._client = httpx.Client(
                base_url=self.config.api_url,
                headers=headers,
                timeout=self.config.timeout,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise errors if needed."""
        if response.status_code >= 400:
            try:
                data = response.json()
                message = data.get("detail", data.get("message", "Request failed"))
            except Exception:
                message = response.text or f"HTTP {response.status_code}"
            raise APIError(response.status_code, message)

        if response.status_code == 204:
            return {}

        try:
            return response.json()
        except Exception:
            return {"data": response.text}

    # =========================================================================
    # Authentication
    # =========================================================================

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login with email and password."""
        response = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        return self._handle_response(response)

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        response = self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        return self._handle_response(response)

    def get_me(self) -> Dict[str, Any]:
        """Get current user info."""
        response = self.client.get("/api/auth/me")
        return self._handle_response(response)

    # =========================================================================
    # AgentAudit (Scanning)
    # =========================================================================

    def create_scan(
        self,
        target: str,
        scan_type: str = "quick",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new security scan."""
        payload = {
            "target_url": target,
            "target_type": "url",
            "mode": scan_type,
        }
        if config:
            payload["config"] = config

        response = self.client.post("/api/scans", json=payload)
        return self._handle_response(response)

    def create_demo_scan(self, target: str) -> Dict[str, Any]:
        """Create a demo scan without authentication."""
        payload = {
            "target_url": target,
            "target_type": "mcp_server",
            "mode": "full",
            "transport_type": "http",
            "auth_method": "none",
        }

        # Create a client without auth headers for demo
        with httpx.Client(
            base_url=self.config.api_url,
            headers={"Content-Type": "application/json"},
            timeout=self.config.timeout,
        ) as client:
            response = client.post("/api/scans", json=payload)
            return self._handle_response(response)

    def get_demo_scan(self, scan_id: int) -> Dict[str, Any]:
        """Get demo scan details without authentication."""
        with httpx.Client(
            base_url=self.config.api_url,
            headers={"Content-Type": "application/json"},
            timeout=self.config.timeout,
        ) as client:
            response = client.get(f"/api/scans/{scan_id}")
            return self._handle_response(response)

    def get_scan(self, scan_id: int) -> Dict[str, Any]:
        """Get scan details."""
        response = self.client.get(f"/api/scans/{scan_id}")
        return self._handle_response(response)

    def list_scans(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """List all scans."""
        response = self.client.get(f"/api/scans?limit={limit}&offset={offset}")
        return self._handle_response(response)

    def get_scan_results(self, scan_id: int) -> Dict[str, Any]:
        """Get detailed scan results."""
        response = self.client.get(f"/api/scans/{scan_id}/results")
        return self._handle_response(response)

    def export_report(self, scan_id: int, format: str = "pdf") -> bytes:
        """Export scan report as PDF or other format."""
        response = self.client.get(
            f"/api/reports/export/{format}",
            params={"scan_id": scan_id},
        )
        if response.status_code >= 400:
            self._handle_response(response)
        return response.content

    # =========================================================================
    # AgentBench (Benchmarking)
    # =========================================================================

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List available benchmark scenarios."""
        response = self.client.get("/api/agentbench/scenarios")
        return self._handle_response(response)

    def run_benchmark(
        self,
        scenario_id: str,
        agent_name: str,
        api_endpoint: str,
        api_key: str,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a benchmark scenario."""
        payload = {
            "scenario_id": scenario_id,
            "agent_name": agent_name,
            "api_endpoint": api_endpoint,
            "api_key": api_key,
        }
        if model_name:
            payload["model_name"] = model_name

        response = self.client.post("/api/agentbench/run", json=payload)
        return self._handle_response(response)

    def get_benchmark_run(self, run_id: int) -> Dict[str, Any]:
        """Get benchmark run details."""
        response = self.client.get(f"/api/agentbench/run/{run_id}")
        return self._handle_response(response)

    def list_benchmark_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List benchmark runs."""
        response = self.client.get(f"/api/agentbench/runs?limit={limit}")
        return self._handle_response(response)

    def get_benchmark_stats(self) -> Dict[str, Any]:
        """Get benchmark statistics."""
        response = self.client.get("/api/agentbench/stats")
        return self._handle_response(response)

    def get_benchmark_usage(self) -> Dict[str, Any]:
        """Get benchmark usage info."""
        response = self.client.get("/api/agentbench/usage")
        return self._handle_response(response)

    # =========================================================================
    # Stats & Overview
    # =========================================================================

    def get_stats_overview(self) -> Dict[str, Any]:
        """Get dashboard overview stats."""
        response = self.client.get("/api/v1/stats/overview")
        return self._handle_response(response)


# Convenience function for quick API access
def get_api() -> XSourceAPI:
    """Get API client instance."""
    return XSourceAPI()
