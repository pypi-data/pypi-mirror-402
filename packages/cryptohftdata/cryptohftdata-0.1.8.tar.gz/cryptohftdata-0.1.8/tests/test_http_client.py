import time
import unittest
from unittest.mock import MagicMock, patch

import requests  # Import the requests module

from cryptohftdata.http_client import (
    APIError,
    AuthenticationError,
    DataNotFoundError,
    HTTPClient,
    NetworkError,
    RateLimitError,
    TimeoutError,
)


class TestHTTPClient(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://mockapi.test.com"
        self.api_key = "test_api_key"
        # Disable JWT for most tests to avoid complexity in mocking
        self.client = HTTPClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=5,
            max_retries=1,
            rate_limit=10,
            use_jwt=False,  # Disable JWT for simpler testing
        )

    def tearDown(self):
        self.client.close()

    @patch("requests.Session.request")
    def test_get_successful(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_request.return_value = mock_response

        response = self.client.get("/test_endpoint", params={"param": "value"})
        self.assertEqual(response, {"data": "success"})
        mock_request.assert_called_once_with(
            "GET",
            f"{self.base_url}/test_endpoint",
            timeout=5,
            params={"param": "value"},
            headers={"X-API-Key": self.api_key},  # Expect API key header
        )

    @patch("requests.Session.request")
    def test_post_successful(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "created"}
        mock_request.return_value = mock_response

        response = self.client.post("/test_endpoint", data={"key": "value"})
        self.assertEqual(response, {"data": "created"})
        mock_request.assert_called_once_with(
            "POST",
            f"{self.base_url}/test_endpoint",
            json={"key": "value"},
            timeout=5,
            params=None,
            headers={"X-API-Key": self.api_key},  # Expect API key header
        )

    @patch("requests.Session.request")
    def test_put_successful(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "updated"}
        mock_request.return_value = mock_response

        response = self.client.put("/test_endpoint", data={"key": "new_value"})
        self.assertEqual(response, {"data": "updated"})
        mock_request.assert_called_once_with(
            "PUT",
            f"{self.base_url}/test_endpoint",
            json={"key": "new_value"},
            timeout=5,
            params=None,
            headers={"X-API-Key": self.api_key},  # Expect API key header
        )

    @patch("requests.Session.request")
    def test_delete_successful(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "deleted"}
        mock_request.return_value = mock_response

        response = self.client.delete("/test_endpoint")
        self.assertEqual(response, {"data": "deleted"})
        mock_request.assert_called_once_with(
            "DELETE",
            f"{self.base_url}/test_endpoint",
            timeout=5,
            params=None,
            headers={"X-API-Key": self.api_key},  # Expect API key header
        )

    @patch("requests.Session.request")
    def test_authentication_error_401(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        with self.assertRaises(AuthenticationError) as context:
            self.client.get("/protected_endpoint")
        self.assertEqual(
            str(context.exception), "Invalid API key or authentication failed"
        )

    @patch("requests.Session.request")
    def test_data_not_found_error_404(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        with self.assertRaises(DataNotFoundError) as context:
            self.client.get("/nonexistent_endpoint")
        self.assertEqual(str(context.exception), "Requested data not found")

    @patch("requests.Session.request")
    def test_rate_limit_error_429(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_request.return_value = mock_response

        with self.assertRaises(RateLimitError) as context:
            self.client.get("/limited_endpoint")
        self.assertEqual(str(context.exception), "Rate limit exceeded")
        self.assertEqual(context.exception.retry_after, 60)

    @patch("requests.Session.request")
    def test_rate_limit_error_429_no_header(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}  # No Retry-After header
        mock_request.return_value = mock_response

        with self.assertRaises(RateLimitError) as context:
            self.client.get("/limited_endpoint")
        self.assertEqual(str(context.exception), "Rate limit exceeded")
        self.assertEqual(context.exception.retry_after, 60)  # Default value

    @patch("requests.Session.request")
    def test_api_error_400(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"message": "Bad request"}'
        mock_response.json.return_value = {"message": "Bad request"}
        mock_request.return_value = mock_response

        with self.assertRaises(APIError) as context:
            self.client.get("/bad_request_endpoint")
        self.assertEqual(str(context.exception), "Bad request")
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.response_body, '{"message": "Bad request"}')

    @patch("requests.Session.request")
    def test_api_error_400_non_json_response(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Not a JSON"
        mock_response.reason = "Bad Request"
        # Simulate json.JSONDecodeError when response.json() is called in _extract_error_message
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "No JSON object could be decoded", "doc", 0
        )
        mock_request.return_value = mock_response

        with self.assertRaises(APIError) as context:
            self.client.get("/bad_request_endpoint_non_json")
        self.assertEqual(str(context.exception), "HTTP 400: Bad Request")
        self.assertEqual(context.exception.status_code, 400)

    @patch("requests.Session.request")
    def test_server_error_500(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response

        with self.assertRaises(APIError) as context:
            self.client.get("/server_error_endpoint")
        self.assertEqual(str(context.exception), "Server error: 500")
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.response_body, "Internal Server Error")

    @patch("requests.Session.request")
    def test_timeout_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.Timeout("Request timed out")

        with self.assertRaises(TimeoutError) as context:
            self.client.get("/timeout_endpoint")
        self.assertTrue("Request timed out after 5 seconds" in str(context.exception))

    @patch("requests.Session.request")
    def test_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        with self.assertRaises(NetworkError) as context:
            self.client.get("/connection_error_endpoint")
        self.assertTrue("Connection error: Connection failed" in str(context.exception))

    @patch("requests.Session.request")
    def test_generic_request_exception(self, mock_request):
        mock_request.side_effect = requests.exceptions.RequestException(
            "Some other request error"
        )

        with self.assertRaises(NetworkError) as context:
            self.client.get("/generic_error_endpoint")
        self.assertTrue(
            "Request failed: Some other request error" in str(context.exception)
        )

    @patch("requests.Session.request")
    def test_invalid_json_response(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Not a valid JSON"
        # Simulate json.JSONDecodeError when response.json() is called in _parse_response
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "No JSON object could be decoded", "doc", 0
        )
        mock_request.return_value = mock_response

        with self.assertRaises(APIError) as context:
            self.client.get("/invalid_json_endpoint")
        self.assertTrue("Invalid JSON response" in str(context.exception))
        self.assertEqual(context.exception.status_code, 200)
        self.assertEqual(context.exception.response_body, "Not a valid JSON")

    def test_client_without_api_key(self):
        client_no_key = HTTPClient(base_url=self.base_url)
        self.assertNotIn("Authorization", client_no_key.session.headers)
        client_no_key.close()

    def test_client_with_api_key(self):
        # With JWT disabled, client should not set Authorization header in session
        self.assertNotIn("Authorization", self.client.session.headers)
        # But should have API key available
        self.assertEqual(self.client.api_key, self.api_key)

    @patch("time.sleep", return_value=None)  # Mock time.sleep to speed up test
    @patch("time.time")
    @patch("requests.Session.request")
    def test_rate_limiting(self, mock_request, mock_time, mock_sleep):
        # Ensure mocks are clean for this specific test
        mock_request.reset_mock()
        mock_time.reset_mock()
        mock_sleep.reset_mock()

        # Configure rate limit to 1 request per second for easier testing
        client_rate_limited = HTTPClient(base_url=self.base_url, rate_limit=1)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_request.return_value = mock_response

        # Define the sequence of time.time() return values
        mock_time_sequence = [
            0.0,
            0.0,  # For first call to client_rate_limited.get()
            0.1,
            0.1,  # For second call
            1.1,
            1.1,  # For third call
            1.2,
            1.2,  # For fourth call
        ]
        mock_time.side_effect = mock_time_sequence

        # --- Test Call 1 ---
        client_rate_limited.get("/endpoint1")
        # Expected behavior: current_time=0.0, _last_request_time was 0.0. time_since_last=0.0.
        # sleep_time = 1.0 (min_interval) - 0.0 = 1.0. So, sleep(1.0) is called.
        # _last_request_time becomes 0.0 (from mock_time.side_effect).
        mock_sleep.assert_called_once_with(1.0)
        self.assertEqual(mock_request.call_count, 1, "Call count after first request")
        self.assertEqual(
            client_rate_limited._last_request_time,
            0.0,
            "_last_request_time after first call",
        )

        mock_sleep.reset_mock()  # Reset for next assertion block

        # --- Test Call 2 ---
        client_rate_limited.get("/endpoint2")
        # Expected: current_time=0.1, _last_request_time=0.0. time_since_last=0.1.
        # sleep_time = 1.0 - 0.1 = 0.9. sleep(0.9).
        # _last_request_time becomes 0.1.
        mock_sleep.assert_called_once()
        self.assertAlmostEqual(
            mock_sleep.call_args[0][0],
            0.9,
            places=5,
            msg="Sleep duration for second call",
        )
        self.assertEqual(mock_request.call_count, 2, "Call count after second request")
        self.assertEqual(
            client_rate_limited._last_request_time,
            0.1,
            "_last_request_time after second call",
        )

        mock_sleep.reset_mock()

        # --- Test Call 3 ---
        client_rate_limited.get("/endpoint3")
        # Expected: current_time=1.1, _last_request_time=0.1. time_since_last=1.0.
        # 1.0 < 1.0 is false. No sleep.
        # _last_request_time becomes 1.1.
        mock_sleep.assert_not_called()
        self.assertEqual(mock_request.call_count, 3, "Call count after third request")
        self.assertEqual(
            client_rate_limited._last_request_time,
            1.1,
            "_last_request_time after third call",
        )

        mock_sleep.reset_mock()

        # --- Test Call 4 ---
        client_rate_limited.get("/endpoint4")
        # Expected: current_time=1.2, _last_request_time=1.1. time_since_last=0.1.
        # sleep_time = 1.0 - 0.1 = 0.9. sleep(0.9).
        # _last_request_time becomes 1.2.
        mock_sleep.assert_called_once()
        self.assertAlmostEqual(
            mock_sleep.call_args[0][0],
            0.9,
            places=5,
            msg="Sleep duration for fourth call",
        )
        self.assertEqual(mock_request.call_count, 4, "Call count after fourth request")
        self.assertEqual(
            client_rate_limited._last_request_time,
            1.2,
            "_last_request_time after fourth call",
        )

        client_rate_limited.close()

    def test_context_manager(self):
        # Create a new client instance for this test to avoid interference
        # with the self.client that might be closed in tearDown
        client_cm = HTTPClient(base_url=self.base_url)
        with patch.object(client_cm.session, "close") as mock_session_close:
            with client_cm as client:  # Use the new client instance here
                self.assertIsNotNone(client.session)
        mock_session_close.assert_called_once()

    @patch("requests.Session.request")
    def test_base_url_stripping(self, mock_request):
        client_with_slash = HTTPClient(base_url=self.base_url + "/", use_jwt=False)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_request.return_value = mock_response

        client_with_slash.get("test_endpoint")  # Note: no leading slash on endpoint
        mock_request.assert_called_once_with(
            "GET",
            f"{self.base_url}/test_endpoint",  # Should be correctly joined
            timeout=client_with_slash.timeout,  # Default timeout
            params=None,
            headers={},  # No API key for this client
        )
        client_with_slash.close()

        mock_request.reset_mock()

        client_with_slash.get("/test_endpoint2")  # With leading slash on endpoint
        mock_request.assert_called_once_with(
            "GET",
            f"{self.base_url}/test_endpoint2",  # Should be correctly joined
            timeout=client_with_slash.timeout,
            params=None,
            headers={},  # No API key for this client
        )
        client_with_slash.close()

    # JWT Authentication Tests

    @patch("requests.Session.request")
    def test_jwt_token_generation_success(self, mock_request):
        """Test successful JWT token generation and usage."""
        # Create client with JWT enabled
        jwt_client = HTTPClient(
            base_url=self.base_url,
            api_key=self.api_key,
            use_jwt=True,
            timeout=5,
        )

        # Mock JWT token generation response
        jwt_response = MagicMock()
        jwt_response.status_code = 200
        jwt_response.json.return_value = {
            "jwt_token": "test-jwt-token",
            "expires_in": 14400,
            "token_type": "Bearer",
        }

        # Mock actual API response
        api_response = MagicMock()
        api_response.status_code = 200
        api_response.json.return_value = {"data": "success"}

        # Configure mock to return JWT response first, then API response
        mock_request.side_effect = [jwt_response, api_response]

        response = jwt_client.get("/test_endpoint")
        self.assertEqual(response, {"data": "success"})

        # Verify JWT token generation call
        self.assertEqual(mock_request.call_count, 2)
        jwt_call = mock_request.call_args_list[0]
        self.assertEqual(jwt_call[1]["url"], f"{self.base_url}/jwt-token")
        self.assertEqual(jwt_call[1]["headers"]["X-API-Key"], self.api_key)

        # Verify actual API call uses JWT token
        api_call = mock_request.call_args_list[1]
        self.assertEqual(api_call[0][0], "GET")
        self.assertEqual(
            api_call[1]["headers"]["Authorization"], "Bearer test-jwt-token"
        )

        jwt_client.close()

    @patch("requests.Session.request")
    def test_jwt_token_generation_failure_fallback(self, mock_request):
        """Test fallback to API key when JWT token generation fails."""
        # Create client with JWT enabled
        jwt_client = HTTPClient(
            base_url=self.base_url,
            api_key=self.api_key,
            use_jwt=True,
            timeout=5,
        )

        # Mock JWT token generation failure
        jwt_response = MagicMock()
        jwt_response.status_code = 401
        jwt_response.json.return_value = {"error": "Invalid API key"}

        # Mock actual API response
        api_response = MagicMock()
        api_response.status_code = 200
        api_response.json.return_value = {"data": "success"}

        # Configure mock to return JWT failure first, then API success
        mock_request.side_effect = [jwt_response, api_response]

        response = jwt_client.get("/test_endpoint")
        self.assertEqual(response, {"data": "success"})

        # Verify both calls were made
        self.assertEqual(mock_request.call_count, 2)

        # Verify fallback to API key
        api_call = mock_request.call_args_list[1]
        self.assertEqual(api_call[1]["headers"]["X-API-Key"], self.api_key)

        jwt_client.close()

    @patch("requests.Session.request")
    def test_jwt_token_retry_on_expiration(self, mock_request):
        """Test JWT token refresh when token expires."""
        # Create client with JWT enabled
        jwt_client = HTTPClient(
            base_url=self.base_url,
            api_key=self.api_key,
            use_jwt=True,
            timeout=5,
        )

        # Mock initial JWT token generation
        jwt_response1 = MagicMock()
        jwt_response1.status_code = 200
        jwt_response1.json.return_value = {
            "jwt_token": "test-jwt-token-1",
            "expires_in": 14400,
            "token_type": "Bearer",
        }

        # Mock expired token response
        expired_response = MagicMock()
        expired_response.status_code = 401
        expired_response.json.return_value = {
            "error": "Token expired",
            "code": "expired_token",
        }

        # Mock new JWT token generation
        jwt_response2 = MagicMock()
        jwt_response2.status_code = 200
        jwt_response2.json.return_value = {
            "jwt_token": "test-jwt-token-2",
            "expires_in": 14400,
            "token_type": "Bearer",
        }

        # Mock successful API response
        api_response = MagicMock()
        api_response.status_code = 200
        api_response.json.return_value = {"data": "success"}

        # Configure mock sequence: JWT gen -> expired response -> JWT regen -> success
        mock_request.side_effect = [
            jwt_response1,
            expired_response,
            jwt_response2,
            api_response,
        ]

        response = jwt_client.get("/test_endpoint")
        self.assertEqual(response, {"data": "success"})

        # Verify all 4 calls were made (initial JWT, expired request, new JWT, retry)
        self.assertEqual(mock_request.call_count, 4)

        jwt_client.close()

    def test_client_without_jwt(self):
        """Test client behavior when JWT is disabled."""
        no_jwt_client = HTTPClient(
            base_url=self.base_url, api_key=self.api_key, use_jwt=False
        )

        # Should not have JWT manager
        self.assertIsNone(no_jwt_client._jwt_manager)
        self.assertFalse(no_jwt_client.use_jwt)

        no_jwt_client.close()


if __name__ == "__main__":
    unittest.main()
