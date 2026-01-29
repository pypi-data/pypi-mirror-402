"""Tests for ExecutorClient."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from trading_service_utils.client.executor_client import ExecutorClient


@pytest.fixture
def executor_client():
    """Create a test ExecutorClient instance."""
    return ExecutorClient(
        executor_url="http://localhost:8000",
        timeout=5.0,
        retries=3,
        retry_delay=0.1,  # Short delay for tests
    )


@pytest.fixture
def sample_order_payload():
    """Create a sample order payload."""
    return {
        "token_id": "test_token_123",
        "amount": 100.0,
        "side": "buy",
        "price": 0.5,
    }


class TestExecutorClientInit:
    """Test ExecutorClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        client = ExecutorClient(executor_url="http://localhost:8000")
        assert client.executor_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.retries == 3
        assert client.retry_delay == 2.0
        assert client.user_agent == "trading-service-utils/executor-client"
        assert client.endpoint == "/api/v1/orders"
        assert client.full_url == "http://localhost:8000/api/v1/orders"

    def test_init_with_custom_values(self):
        """Test initialization with custom parameters."""
        client = ExecutorClient(
            executor_url="http://executor:9000/",
            timeout=10.0,
            retries=5,
            retry_delay=1.0,
            user_agent="test-agent",
            endpoint="/custom/endpoint",
        )
        assert client.executor_url == "http://executor:9000"
        assert client.timeout == 10.0
        assert client.retries == 5
        assert client.retry_delay == 1.0
        assert client.user_agent == "test-agent"
        assert client.endpoint == "/custom/endpoint"
        assert client.full_url == "http://executor:9000/custom/endpoint"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slashes are removed from executor_url."""
        client = ExecutorClient(executor_url="http://localhost:8000///")
        assert client.executor_url == "http://localhost:8000"
        assert client.full_url == "http://localhost:8000/api/v1/orders"


class TestSendOrderSuccess:
    """Test successful order sending scenarios."""

    @pytest.mark.asyncio
    async def test_send_order_success_200(self, executor_client, sample_order_payload):
        """Test successful order with 200 status code."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = '{"status": "accepted"}'

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await executor_client.send_order(sample_order_payload)

            assert result is True
            mock_client_instance.post.assert_called_once()
            call_kwargs = mock_client_instance.post.call_args.kwargs
            assert call_kwargs["json"] == sample_order_payload
            assert call_kwargs["headers"]["Content-Type"] == "application/json"
            assert "User-Agent" in call_kwargs["headers"]

    @pytest.mark.asyncio
    async def test_send_order_success_201(self, executor_client, sample_order_payload):
        """Test successful order with 201 status code."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 201
        mock_response.text = '{"order_id": "12345"}'

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await executor_client.send_order(sample_order_payload)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_order_correct_url(self, sample_order_payload):
        """Test that order is sent to the correct URL."""
        client = ExecutorClient(
            executor_url="http://test-executor:7000",
            endpoint="/v2/trades",
        )
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            await client.send_order(sample_order_payload)

            call_args = mock_client_instance.post.call_args
            assert call_args.args[0] == "http://test-executor:7000/v2/trades"


class TestSendOrderClientErrors:
    """Test 4xx client error scenarios (no retry)."""

    @pytest.mark.asyncio
    async def test_send_order_400_bad_request(self, executor_client, sample_order_payload):
        """Test that 400 errors are not retried."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Invalid payload"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await executor_client.send_order(sample_order_payload)

            assert result is False
            # Should only be called once (no retries for 4xx)
            assert mock_client_instance.post.call_count == 1

    @pytest.mark.asyncio
    async def test_send_order_404_not_found(self, executor_client, sample_order_payload):
        """Test that 404 errors are not retried."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await executor_client.send_order(sample_order_payload)

            assert result is False
            assert mock_client_instance.post.call_count == 1

    @pytest.mark.asyncio
    async def test_send_order_422_validation_error(self, executor_client, sample_order_payload):
        """Test that 422 validation errors are not retried."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 422
        mock_response.text = "Validation Error"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await executor_client.send_order(sample_order_payload)

            assert result is False
            assert mock_client_instance.post.call_count == 1


class TestSendOrderServerErrors:
    """Test 5xx server error scenarios (with retry)."""

    @pytest.mark.asyncio
    async def test_send_order_500_retries(self, executor_client, sample_order_payload):
        """Test that 500 errors trigger retries."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await executor_client.send_order(sample_order_payload)

            assert result is False
            # Should retry 3 times
            assert mock_client_instance.post.call_count == 3

    @pytest.mark.asyncio
    async def test_send_order_503_retries_then_succeeds(
        self, executor_client, sample_order_payload
    ):
        """Test that retries can eventually succeed after server errors."""
        failed_response = MagicMock()
        failed_response.is_success = False
        failed_response.status_code = 503
        failed_response.text = "Service Unavailable"

        success_response = MagicMock()
        success_response.is_success = True
        success_response.status_code = 200
        success_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            # First two attempts fail, third succeeds
            mock_client_instance.post = AsyncMock(
                side_effect=[failed_response, failed_response, success_response]
            )

            result = await executor_client.send_order(sample_order_payload)

            assert result is True
            assert mock_client_instance.post.call_count == 3


class TestSendOrderNetworkErrors:
    """Test network error scenarios."""

    @pytest.mark.asyncio
    async def test_send_order_timeout_retries(self, executor_client, sample_order_payload):
        """Test that timeout errors trigger retries."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            result = await executor_client.send_order(sample_order_payload)

            assert result is False
            assert mock_client_instance.post.call_count == 3

    @pytest.mark.asyncio
    async def test_send_order_connection_error_retries(
        self, executor_client, sample_order_payload
    ):
        """Test that connection errors trigger retries."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            result = await executor_client.send_order(sample_order_payload)

            assert result is False
            assert mock_client_instance.post.call_count == 3

    @pytest.mark.asyncio
    async def test_send_order_network_error_then_success(
        self, executor_client, sample_order_payload
    ):
        """Test recovery after network errors."""
        success_response = MagicMock()
        success_response.is_success = True
        success_response.status_code = 200
        success_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            # First attempt: timeout, second: connection error, third: success
            mock_client_instance.post = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("Timeout"),
                    httpx.ConnectError("Connection error"),
                    success_response,
                ]
            )

            result = await executor_client.send_order(sample_order_payload)

            assert result is True
            assert mock_client_instance.post.call_count == 3


class TestSendOrderUnexpectedErrors:
    """Test unexpected error scenarios."""

    @pytest.mark.asyncio
    async def test_send_order_unexpected_exception(
        self, executor_client, sample_order_payload
    ):
        """Test that unexpected exceptions are handled."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(
                side_effect=ValueError("Unexpected error")
            )

            result = await executor_client.send_order(sample_order_payload)

            assert result is False
            # Should stop on first unexpected error
            assert mock_client_instance.post.call_count == 1

    @pytest.mark.asyncio
    async def test_send_order_keyboard_interrupt(
        self, executor_client, sample_order_payload
    ):
        """Test that keyboard interrupt is handled gracefully."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(side_effect=KeyboardInterrupt())

            with pytest.raises(KeyboardInterrupt):
                await executor_client.send_order(sample_order_payload)


class TestSendOrderTimeout:
    """Test timeout configuration."""

    @pytest.mark.asyncio
    async def test_send_order_custom_timeout(self, sample_order_payload):
        """Test that custom timeout is applied."""
        client = ExecutorClient(executor_url="http://localhost:8000", timeout=15.0)

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            await client.send_order(sample_order_payload)

            # Check that AsyncClient was created with correct timeout
            call_kwargs = MockClient.call_args.kwargs
            assert "timeout" in call_kwargs
            timeout_obj = call_kwargs["timeout"]
            assert isinstance(timeout_obj, httpx.Timeout)


class TestSendOrderLogging:
    """Test logging behavior."""

    @pytest.mark.asyncio
    async def test_send_order_logs_payload(self, executor_client, sample_order_payload):
        """Test that order details are logged."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with patch(
                "trading_service_utils.client.executor_client.logger"
            ) as mock_logger:
                await executor_client.send_order(sample_order_payload)

                # Check that info log was called with token_id and amount
                info_calls = mock_logger.info.call_args_list
                assert any(
                    "test_token_123" in str(call) and "100.0" in str(call)
                    for call in info_calls
                )

    @pytest.mark.asyncio
    async def test_send_order_missing_token_id(self, executor_client):
        """Test logging when token_id is missing."""
        payload = {"amount": 50.0}  # No token_id

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await executor_client.send_order(payload)

            assert result is True


class TestSendOrderRetryDelay:
    """Test retry delay behavior."""

    @pytest.mark.asyncio
    async def test_send_order_retry_delay_is_applied(
        self, executor_client, sample_order_payload
    ):
        """Test that retry delay is properly applied between attempts."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Error"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await executor_client.send_order(sample_order_payload)

                # Sleep should be called between retries (retries-1 times)
                assert mock_sleep.call_count == 2
                # Check that the delay is correct
                for call in mock_sleep.call_args_list:
                    assert call.args[0] == 0.1

    @pytest.mark.asyncio
    async def test_send_order_no_delay_on_last_attempt(
        self, executor_client, sample_order_payload
    ):
        """Test that no delay occurs after the final attempt."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await executor_client.send_order(sample_order_payload)

                # With 3 retries, sleep should only be called 2 times
                # (between 1st-2nd and 2nd-3rd, but not after 3rd)
                assert mock_sleep.call_count == 2


class TestSendOrderHeaders:
    """Test HTTP headers."""

    @pytest.mark.asyncio
    async def test_send_order_custom_user_agent(self, sample_order_payload):
        """Test that custom user agent is sent in headers."""
        client = ExecutorClient(
            executor_url="http://localhost:8000", user_agent="my-custom-agent/1.0"
        )

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            await client.send_order(sample_order_payload)

            call_kwargs = mock_client_instance.post.call_args.kwargs
            assert call_kwargs["headers"]["User-Agent"] == "my-custom-agent/1.0"

    @pytest.mark.asyncio
    async def test_send_order_content_type_header(
        self, executor_client, sample_order_payload
    ):
        """Test that Content-Type header is set correctly."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            await executor_client.send_order(sample_order_payload)

            call_kwargs = mock_client_instance.post.call_args.kwargs
            assert call_kwargs["headers"]["Content-Type"] == "application/json"
