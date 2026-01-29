"""
HTTP client for making API requests.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode, urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    APIError,
    AuthenticationError,
    DataNotFoundError,
    NetworkError,
    RateLimitError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class JWTTokenManager:
    """Manages JWT tokens for API authentication."""

    def __init__(self, api_key: str, base_url: str, timeout: int = 30):
        """
        Initialize JWT token manager.

        Args:
            api_key: API key for generating JWT tokens
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._jwt_token: Optional[str] = None
        self._jwt_expires_at: Optional[datetime] = None

    def get_jwt_token(self) -> str:
        """
        Get a valid JWT token, refreshing if necessary.

        Returns:
            Valid JWT token

        Raises:
            AuthenticationError: If unable to generate/refresh token
        """
        # Check if we have a valid token
        if (
            self._jwt_token
            and self._jwt_expires_at
            and datetime.now() < self._jwt_expires_at - timedelta(minutes=5)
        ):  # 5 min buffer
            return self._jwt_token

        # Generate new token
        return self._generate_jwt_token()

    def _generate_jwt_token(self) -> str:
        """
        Generate a new JWT token from API key.

        Returns:
            New JWT token

        Raises:
            AuthenticationError: If token generation fails
        """
        url = f"{self.base_url}/jwt-token"
        headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

        try:
            logger.debug("Generating new JWT token")
            response = requests.post(url, headers=headers, timeout=self.timeout)

            if response.status_code == 401:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", "Invalid API key")
                raise AuthenticationError(f"Failed to generate JWT token: {error_msg}")
            elif response.status_code != 200:
                raise AuthenticationError(
                    f"JWT token generation failed: HTTP {response.status_code}"
                )

            token_data = response.json()
            self._jwt_token = token_data["jwt_token"]
            expires_in = token_data.get("expires_in", 14400)  # Default 4 hours
            self._jwt_expires_at = datetime.now() + timedelta(seconds=expires_in)

            logger.debug(f"JWT token generated, expires at {self._jwt_expires_at}")
            return self._jwt_token

        except requests.exceptions.RequestException as e:
            raise AuthenticationError(
                f"Network error generating JWT token: {str(e)}"
            ) from e
        except (KeyError, json.JSONDecodeError) as e:
            raise AuthenticationError(f"Invalid JWT token response: {str(e)}") from e

    def invalidate_token(self) -> None:
        """Invalidate the current JWT token to force regeneration."""
        self._jwt_token = None
        self._jwt_expires_at = None


class HTTPClient:
    """HTTP client with retry logic, rate limiting, and error handling."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit: Optional[int] = None,
        use_jwt: bool = True,
        **kwargs,
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for API requests
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            rate_limit: Maximum requests per second
            use_jwt: Whether to use JWT tokens for authentication (default: True)
            **kwargs: Additional configuration
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.use_jwt = use_jwt

        # Rate limiting
        self._last_request_time = 0.0
        self._min_interval = 1.0 / rate_limit if rate_limit else 0.0

        # JWT token manager
        self._jwt_manager: Optional[JWTTokenManager] = None
        if self.api_key and self.use_jwt:
            self._jwt_manager = JWTTokenManager(self.api_key, self.base_url, timeout)

        # Create session with retry strategy
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "User-Agent": "cryptohftdata-python-sdk/0.1.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Don't set Authorization header here - we'll set it per request

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint (relative to base_url)
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            APIError: If the API returns an error
            NetworkError: If there's a network issue
            TimeoutError: If the request times out
        """
        return self._request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint (relative to base_url)
            data: Request body data
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        return self._request("POST", endpoint, data=data, params=params)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint (relative to base_url)
            data: Request body data
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        return self._request("PUT", endpoint, data=data, params=params)

    def delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint (relative to base_url)
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        return self._request("DELETE", endpoint, params=params)

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for requests.

        Returns:
            Dictionary of authentication headers
        """
        if not self.api_key:
            return {}

        if self._jwt_manager and self.use_jwt:
            try:
                jwt_token = self._jwt_manager.get_jwt_token()
                return {"Authorization": f"Bearer {jwt_token}"}
            except AuthenticationError:
                # Fall back to API key if JWT fails
                logger.warning("JWT token generation failed, falling back to API key")
                return {"X-API-Key": self.api_key}
        else:
            # Use API key directly
            return {"X-API-Key": self.api_key}

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        _retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with error handling and rate limiting.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            _retry_count: Internal retry counter for JWT token refresh

        Returns:
            Parsed JSON response
        """
        # Rate limiting
        self._enforce_rate_limit()

        # Construct URL
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        # Get authentication headers
        auth_headers = self._get_auth_headers()

        # Prepare request kwargs
        request_kwargs = {
            "timeout": self.timeout,
            "params": params,
            "headers": auth_headers,
        }

        if data is not None:
            request_kwargs["json"] = data

        try:
            logger.debug(f"Making {method} request to {url}")

            response = self.session.request(method, url, **request_kwargs)

            # Handle different status codes
            if response.status_code == 200:
                return self._parse_response(response)
            elif response.status_code == 401:
                # Check if this is a JWT token expiration error
                if (
                    _retry_count == 0
                    and self._jwt_manager
                    and self.use_jwt
                    and auth_headers.get("Authorization", "").startswith("Bearer ")
                ):

                    try:
                        error_data = response.json()
                        error_code = error_data.get("code", "")

                        # If it's an expired token, invalidate and retry
                        if error_code in [
                            "expired_token",
                            "invalid_token",
                            "validation_failed",
                        ]:
                            logger.debug("JWT token expired, refreshing and retrying")
                            self._jwt_manager.invalidate_token()
                            return self._request(
                                method, endpoint, data, params, _retry_count + 1
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass

                raise AuthenticationError("Invalid API key or authentication failed")
            elif response.status_code == 404:
                raise DataNotFoundError("Requested data not found")
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
            elif 400 <= response.status_code < 500:
                error_msg = self._extract_error_message(response)
                raise APIError(
                    error_msg,
                    status_code=response.status_code,
                    response_body=response.text,
                )
            elif 500 <= response.status_code < 600:
                raise APIError(
                    f"Server error: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )
            else:
                response.raise_for_status()
                return self._parse_response(response)

        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {str(e)}") from e

    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse a successful response.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON data
        """
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise APIError(
                f"Invalid JSON response: {str(e)}",
                status_code=response.status_code,
                response_body=response.text,
            ) from e

    def _extract_error_message(self, response: requests.Response) -> str:
        """
        Extract error message from response.

        Args:
            response: HTTP response object

        Returns:
            Error message string
        """
        try:
            error_data = response.json()
            return error_data.get("message", error_data.get("error", "Unknown error"))
        except (json.JSONDecodeError, AttributeError):
            return f"HTTP {response.status_code}: {response.reason}"

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self._min_interval > 0:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < self._min_interval:
                sleep_time = self._min_interval - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f} seconds")
                time.sleep(sleep_time)

            self._last_request_time = time.time()

    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
