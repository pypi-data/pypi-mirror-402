"""Generic Executor Client for sending trading signals."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ExecutorClient:
    """Async client for communicating with the Executor Service."""

    def __init__(
        self,
        executor_url: str,
        timeout: float = 30.0,
        retries: int = 3,
        retry_delay: float = 2.0,
        user_agent: str = "trading-service-utils/executor-client",
        endpoint: str = "/api/v1/orders",
    ):
        """Initialize the executor client.

        Args:
            executor_url: Base URL of the executor service (e.g. http://executor-polymarket:8000)
            timeout: HTTP request timeout in seconds.
            retries: Number of retry attempts.
            retry_delay: Delay between retries in seconds.
            user_agent: User-Agent header string.
            endpoint: API endpoint path.
        """
        self.executor_url = executor_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        self.endpoint = endpoint
        self.full_url = f"{self.executor_url}{self.endpoint}"

    async def send_order(self, order_payload: Dict[str, Any]) -> bool:
        """Send a trading order payload to the executor.

        Args:
            order_payload: The full JSON payload for the order.

        Returns:
            True if the order was successfully accepted by the executor.
        """
        timeout_config = httpx.Timeout(self.timeout)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }

        # Basic validation logging
        token_id = order_payload.get("token_id", "N/A")
        amount = order_payload.get("amount", "N/A")
        logger.info(f"Sending order -> {self.full_url} | Token: {token_id} | Amount: {amount}")
        logger.debug(f"Payload: {order_payload}")

        for attempt in range(1, self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    response = await client.post(
                        self.full_url,
                        json=order_payload,
                        headers=headers,
                    )

                    if response.is_success:
                        logger.info(
                            "✅ Order sent successfully. Status: %s. Response: %s",
                            response.status_code,
                            response.text,
                        )
                        return True
                    else:
                        logger.warning(
                            "⚠️ Executor returned HTTP %s: %s (Attempt %d/%d)",
                            response.status_code,
                            response.text,
                            attempt,
                            self.retries,
                        )
                        # Do not retry 4xx errors (Bad Request)
                        if 400 <= response.status_code < 500:
                            return False

            except httpx.TimeoutException:
                logger.warning(
                    "⏰ Timeout connecting to executor (Attempt %d/%d)",
                    attempt,
                    self.retries,
                )
            except httpx.RequestError as e:
                logger.warning(
                    "🔌 Network error: %s (Attempt %d/%d)", e, attempt, self.retries
                )
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}", exc_info=True)
                return False

            # Wait before retry (if not last attempt)
            if attempt < self.retries:
                logger.info(f"⏳ Retrying in {self.retry_delay}s...")
                await asyncio.sleep(self.retry_delay)

        logger.error("❌ Failed to send order after %d attempts.", self.retries)
        return False
