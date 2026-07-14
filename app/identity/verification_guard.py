import logging
from collections.abc import Callable
from threading import BoundedSemaphore
from typing import TypeVar


Result = TypeVar("Result")
logger = logging.getLogger(__name__)


class VerificationCapacityError(RuntimeError):
    """Raised when password verification capacity is unavailable in this process."""


class PasswordVerificationGuard:
    """Process-local concurrency bound for memory-intensive password verification."""

    def __init__(self, max_concurrency: int, wait_timeout_seconds: float) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        if wait_timeout_seconds < 0:
            raise ValueError("wait_timeout_seconds must not be negative")
        self._semaphore = BoundedSemaphore(max_concurrency)
        self._wait_timeout_seconds = wait_timeout_seconds

    def run(self, operation: Callable[[], Result]) -> Result:
        acquired = self._semaphore.acquire(timeout=self._wait_timeout_seconds)
        if not acquired:
            logger.warning("password_verification_limiter_timeout")
            raise VerificationCapacityError
        try:
            return operation()
        finally:
            self._semaphore.release()
