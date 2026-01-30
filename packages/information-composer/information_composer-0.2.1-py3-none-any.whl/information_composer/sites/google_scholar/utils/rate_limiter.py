"""Rate limiting utilities for Google Scholar crawler."""

import asyncio
import time


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, rate_limit: float = 2.0, burst_size: int = 1):
        """
        Initialize rate limiter.
        Args:
            rate_limit: Minimum seconds between requests
            burst_size: Number of requests allowed in burst
        """
        self.rate_limit = rate_limit
        self.burst_size = burst_size
        self.last_request_time = 0.0
        self.request_times: list[float] = []

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        current_time = time.time()
        # Clean old requests outside the burst window
        cutoff_time = current_time - self.rate_limit
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        # If we're at burst limit, wait
        if len(self.request_times) >= self.burst_size:
            sleep_time = self.rate_limit - (current_time - self.request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                current_time = time.time()
        # Record this request
        self.request_times.append(current_time)
        self.last_request_time = current_time

    def get_wait_time(self) -> float:
        """Get time to wait before next request."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        return max(0, self.rate_limit - elapsed)


class ExponentialBackoff:
    """Exponential backoff for retry logic."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize exponential backoff.
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential calculation
            jitter: Whether to add random jitter
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.attempt = 0

    def get_delay(self) -> float:
        """Get delay for current attempt."""
        delay = min(
            self.base_delay * (self.exponential_base**self.attempt), self.max_delay
        )
        if self.jitter:
            import random

            delay *= 0.5 + random.random() * 0.5  # Add 0-50% jitter
        return delay

    async def sleep(self) -> None:
        """Sleep for the calculated delay and increment attempt."""
        delay = self.get_delay()
        await asyncio.sleep(delay)
        self.attempt += 1

    def reset(self) -> None:
        """Reset the attempt counter."""
        self.attempt = 0
