"""Error handling and retry mechanisms for Google Scholar crawler."""

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
import logging
import random
from typing import Any

import aiohttp
import requests


logger = logging.getLogger(__name__)


class GoogleScholarError(Exception):
    """Base exception for Google Scholar crawler errors."""

    pass


class RateLimitError(GoogleScholarError):
    """Raised when rate limiting is detected."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class BlockedError(GoogleScholarError):
    """Raised when IP/bot detection occurs."""

    pass


class CaptchaError(GoogleScholarError):
    """Raised when CAPTCHA is encountered."""

    pass


class ParseError(GoogleScholarError):
    """Raised when HTML parsing fails."""

    pass


class NetworkError(GoogleScholarError):
    """Raised for network-related issues."""

    pass


class RetryConfig:
    """Configuration for retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retry_on: list[type[Exception]] | None = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or [
            RateLimitError,
            NetworkError,
            requests.exceptions.RequestException,
            aiohttp.ClientError,
        ]

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(self.base_delay * (self.exponential_base**attempt), self.max_delay)
        if self.jitter:
            # Add ±25% jitter
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        return max(0, delay)


class ErrorHandler:
    """Handle and classify errors from Google Scholar."""

    def __init__(self) -> None:
        self.error_patterns = {
            "rate_limit": [
                "unusual traffic",
                "rate limit",
                "too many requests",
                "please try again later",
                "temporarily unavailable",
            ],
            "blocked": [
                "blocked",
                "access denied",
                "forbidden",
                "your ip has been blocked",
                "bot detected",
            ],
            "captcha": [
                "captcha",
                "please complete",
                "verify you are human",
                "security check",
            ],
            "network": ["connection", "timeout", "network", "dns", "ssl"],
        }

    def classify_error(
        self,
        response: requests.Response | None = None,
        content: str = "",
        exception: Exception | None = None,
    ) -> str:
        """
        Classify error type based on response, content, or exception.
        Returns:
            Error type: 'rate_limit', 'blocked', 'captcha', 'network', or 'unknown'
        """
        # Check HTTP status codes first
        if response:
            if response.status_code == 429:
                return "rate_limit"
            elif response.status_code in [403, 401]:
                return "blocked"
            elif response.status_code >= 500:
                return "network"
        # Check exception types
        if exception:
            if isinstance(
                exception,
                requests.exceptions.ConnectionError
                | requests.exceptions.Timeout
                | aiohttp.ClientError,
            ):
                return "network"
        # Check content patterns
        content_lower = content.lower()
        for error_type, patterns in self.error_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                return error_type
        return "unknown"

    def create_appropriate_error(
        self,
        error_type: str,
        message: str,
        response: requests.Response | None = None,
    ) -> GoogleScholarError:
        """Create appropriate exception based on error type."""
        if error_type == "rate_limit":
            retry_after = self._extract_retry_after(response)
            return RateLimitError(message, retry_after)
        elif error_type == "blocked":
            return BlockedError(message)
        elif error_type == "captcha":
            return CaptchaError(message)
        elif error_type == "network":
            return NetworkError(message)
        else:
            return GoogleScholarError(message)

    def _extract_retry_after(self, response: requests.Response | None) -> float | None:
        """Extract retry-after value from response headers."""
        if not response:
            return None
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return None


def with_retry(config: RetryConfig | None = None) -> Callable:
    """Decorator to add retry logic to async functions."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # _error_handler = ErrorHandler()  # Unused variable
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    # Check if this is a retryable error
                    if not any(isinstance(e, exc_type) for exc_type in config.retry_on):
                        # Not retryable, re-raise immediately
                        raise
                    if attempt == config.max_retries:
                        # Last attempt, re-raise
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_retries} retries"
                        )
                        raise
                    # Calculate delay and log retry
                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    # Special handling for rate limiting
                    if isinstance(e, RateLimitError) and e.retry_after:
                        delay = max(delay, e.retry_after)
                        logger.info(
                            f"Rate limited. Using server-suggested delay: {delay:.2f}s"
                        )
                    await asyncio.sleep(delay)
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            else:
                raise GoogleScholarError("Unknown error occurred")

        return wrapper

    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for failing services."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Call function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise GoogleScholarError(
                    "Circuit breaker is OPEN - service unavailable"
                )
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time >= timedelta(
            seconds=self.recovery_timeout
        )

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class HealthMonitor:
    """Monitor the health of Google Scholar access."""

    def __init__(self, window_size: int = 100) -> None:
        self.window_size = window_size
        self.recent_requests: list[dict] = []
        self.error_handler = ErrorHandler()

    def record_request(
        self,
        success: bool,
        response_time: float,
        error_type: str | None = None,
        status_code: int | None = None,
    ) -> None:
        """Record a request outcome."""
        request_data = {
            "timestamp": datetime.now(),
            "success": success,
            "response_time": response_time,
            "error_type": error_type,
            "status_code": status_code,
        }
        self.recent_requests.append(request_data)
        # Keep only recent requests
        if len(self.recent_requests) > self.window_size:
            self.recent_requests.pop(0)

    def get_health_metrics(self) -> dict[str, Any]:
        """Get current health metrics."""
        if not self.recent_requests:
            return {
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "error_distribution": {},
                "total_requests": 0,
            }
        successful_requests = sum(1 for r in self.recent_requests if r["success"])
        total_requests = len(self.recent_requests)
        success_rate = (
            successful_requests / total_requests if total_requests > 0 else 0.0
        )
        response_times = [
            r["response_time"] for r in self.recent_requests if r["success"]
        ]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )
        # Error distribution
        error_counts: dict[str, int] = {}
        for request in self.recent_requests:
            if not request["success"] and request["error_type"]:
                error_type = request["error_type"]
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return {
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "error_distribution": error_counts,
            "total_requests": total_requests,
            "recent_errors": error_counts,
        }

    def is_healthy(self, min_success_rate: float = 0.7) -> bool:
        """Check if the service is considered healthy."""
        metrics = self.get_health_metrics()
        success_rate = metrics.get("success_rate", 0.0)
        return (
            isinstance(success_rate, int | float) and success_rate >= min_success_rate
        )


# Global health monitor instance
health_monitor = HealthMonitor()


async def safe_request(
    session: requests.Session,
    url: str,
    method: str = "GET",
    retry_config: RetryConfig | None = None,
    **kwargs: Any,
) -> Any:
    """
    Make a safe HTTP request with error handling and monitoring.
    Args:
        session: Requests session
        url: URL to request
        method: HTTP method
        retry_config: Retry configuration
        **kwargs: Additional request parameters
    Returns:
        Response object
    Raises:
        Appropriate GoogleScholarError subclass
    """
    if retry_config is None:
        retry_config = RetryConfig()
    error_handler = ErrorHandler()
    start_time = datetime.now()

    @with_retry(retry_config)
    async def _make_request() -> Any:
        try:
            response = session.request(method, url, **kwargs)
            # Check for error indicators in response
            error_type = error_handler.classify_error(response, response.text)
            if error_type in ["rate_limit", "blocked", "captcha"]:
                error_msg = f"{error_type.replace('_', ' ').title()} detected"
                raise error_handler.create_appropriate_error(
                    error_type, error_msg, response
                )
            if not response.ok:
                error_type = error_handler.classify_error(response)
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                raise error_handler.create_appropriate_error(
                    error_type, error_msg, response
                )
            return response
        except requests.exceptions.RequestException as e:
            error_type = error_handler.classify_error(exception=e)
            raise error_handler.create_appropriate_error(error_type, str(e))

    try:
        response = await _make_request()
        # Record successful request
        response_time = (datetime.now() - start_time).total_seconds()
        status_code = (
            getattr(response, "status_code", 200)
            if hasattr(response, "status_code")
            else 200
        )
        health_monitor.record_request(True, response_time, status_code=status_code)
        return response
    except GoogleScholarError as e:
        # Record failed request
        response_time = (datetime.now() - start_time).total_seconds()
        error_type = type(e).__name__.replace("Error", "").lower()
        health_monitor.record_request(False, response_time, error_type=error_type)
        raise
