"""HTTP client with retry logic and resilience features."""

import json
from typing import Any

import backoff
import httpx

from .config import AegisConfig
from .errors import TimeoutError, TransportError, exception_from_status


class AegisHttpClient:
    """HTTP client for Aegis API calls with built-in resilience."""

    def __init__(self, config: AegisConfig):
        """Initialize HTTP client with configuration."""
        self.config = config
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client instance."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.config.timeout_s),
                headers={
                    "User-Agent": self.config.user_agent,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __del__(self) -> None:
        """Ensure client is closed on garbage collection."""
        self.close()

    @backoff.on_exception(
        backoff.expo,
        (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError),
        max_tries=lambda: 3,  # Will be configurable
        max_time=lambda: 10.0,  # Will be configurable
    )
    def post_json(
        self,
        path: str,
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make POST request with JSON payload and return parsed response.

        Args:
            path: API endpoint path (relative to base_url)
            headers: Additional headers to include
            json_data: JSON payload to send

        Returns:
            Parsed JSON response

        Raises:
            AegisError: For HTTP errors or transport issues
        """
        client = self._get_client()
        url = f"{self.config.base_url}{path}"

        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Add API key header
        request_headers["X-API-KEY"] = self.config.api_key_plain
        request_headers["X-DECISION-SOURCE"] = "python_client"

        try:
            response = client.post(
                url,
                headers=request_headers,
                json=json_data,
                timeout=httpx.Timeout(self.config.timeout_s),
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("message", response.text)
                    raise exception_from_status(response.status_code, message)
                except json.JSONDecodeError:
                    raise exception_from_status(
                        response.status_code, response.text
                    ) from None
                except Exception as e:
                    raise exception_from_status(response.status_code, str(e)) from e

            # Parse successful response
            response_data: dict[str, Any] = response.json()
            return response_data

        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out after {self.config.timeout_s}s"
            ) from e
        except httpx.RequestError as e:
            raise TransportError(f"Network error: {e}") from e

    @backoff.on_exception(
        backoff.expo,
        (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError),
        max_tries=lambda: 3,
        max_time=lambda: 10.0,
    )
    def get_json(
        self,
        path: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make GET request and return parsed JSON response.

        Args:
            path: API endpoint path (relative to base_url)
            headers: Additional headers to include

        Returns:
            Parsed JSON response

        Raises:
            AegisError: For HTTP errors or transport issues
        """
        client = self._get_client()
        url = f"{self.config.base_url}{path}"

        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Add API key header
        request_headers["X-API-KEY"] = self.config.api_key_plain
        request_headers["X-DECISION-SOURCE"] = "python_client"

        try:
            response = client.get(
                url,
                headers=request_headers,
                timeout=httpx.Timeout(self.config.timeout_s),
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("message", response.text)
                    raise exception_from_status(response.status_code, message)
                except json.JSONDecodeError:
                    raise exception_from_status(
                        response.status_code, response.text
                    ) from None
                except Exception as e:
                    raise exception_from_status(response.status_code, str(e)) from e

            # Parse successful response
            response_data: dict[str, Any] = response.json()
            return response_data

        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out after {self.config.timeout_s}s"
            ) from e
        except httpx.RequestError as e:
            raise TransportError(f"Network error: {e}") from e
