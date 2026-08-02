"""
Circuit breaker for external API calls (Konnect, OpenAI/Groq, etc.).

States:
  CLOSED   → normal operation, requests pass through
  OPEN     → too many failures, all calls fail fast with 503
  HALF_OPEN→ after cooldown, allow one probe request to test recovery

Usage:
    @konnect_breaker
    def call_konnect(...):
        ...

    # or inline:
    with konnect_breaker:
        call_konnect(...)
"""

import logging
import time
import threading
from enum import Enum
from typing import Callable, Optional, Any

logger = logging.getLogger(__name__)


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is OPEN (service unavailable)."""

    def __init__(self, service_name: str, cooldown_seconds: int):
        self.service_name = service_name
        self.cooldown_seconds = cooldown_seconds
        super().__init__(
            f"Service '{service_name}' indisponible (circuit ouvert). "
            f"Réessayez dans {cooldown_seconds}s."
        )


class _State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Thread-safe circuit breaker.

    Parameters
    ----------
    service_name : str
        Human-readable name (for logging / error messages).
    failure_threshold : int
        Number of consecutive failures before opening the circuit.
    cooldown_seconds : int
        Seconds to wait before trying a probe request (HALF_OPEN).
    success_threshold : int
        Consecutive successes in HALF_OPEN needed to close the circuit again.
    """

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        cooldown_seconds: int = 30,
        success_threshold: int = 2,
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.success_threshold = success_threshold

        self._state = _State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at: float = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> _State:
        with self._lock:
            if self._state == _State.OPEN:
                if time.time() - self._opened_at >= self.cooldown_seconds:
                    self._state = _State.HALF_OPEN
                    self._success_count = 0
                    logger.info(
                        "CircuitBreaker[%s]: OPEN → HALF_OPEN (cooldown elapsed)",
                        self.service_name,
                    )
            return self._state

    def record_success(self) -> None:
        with self._lock:
            if self._state == _State.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = _State.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(
                        "CircuitBreaker[%s]: HALF_OPEN → CLOSED (recovered)",
                        self.service_name,
                    )
            else:
                self._failure_count = 0

    def record_failure(self) -> None:
        with self._lock:
            if self._state == _State.HALF_OPEN:
                self._state = _State.OPEN
                self._opened_at = time.time()
                self._success_count = 0
                logger.warning(
                    "CircuitBreaker[%s]: HALF_OPEN → OPEN (probe failed)",
                    self.service_name,
                )
            else:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._state = _State.OPEN
                    self._opened_at = time.time()
                    logger.warning(
                        "CircuitBreaker[%s]: CLOSED → OPEN (%d consecutive failures)",
                        self.service_name,
                        self._failure_count,
                    )

    def allow_request(self) -> bool:
        """Return True if the call should proceed."""
        st = self.state  # triggers cooldown check
        if st == _State.CLOSED:
            return True
        if st == _State.HALF_OPEN:
            return True  # allow exactly one probe
        return False  # OPEN

    # -- Context-manager protocol -------------------------------------------

    def __enter__(self):
        if not self.allow_request():
            raise CircuitOpenError(self.service_name, self.cooldown_seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
        return False  # don't suppress exceptions

    # -- Decorator protocol -------------------------------------------------

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not self.allow_request():
                raise CircuitOpenError(self.service_name, self.cooldown_seconds)
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except CircuitOpenError:
                raise
            except Exception:
                self.record_failure()
                raise
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper


# ---------------------------------------------------------------------------
# Pre-configured breakers for EDUAI services
# ---------------------------------------------------------------------------

konnect_breaker = CircuitBreaker(
    service_name="konnect",
    failure_threshold=5,
    cooldown_seconds=30,
    success_threshold=2,
)

ai_provider_breaker = CircuitBreaker(
    service_name="ai_provider",
    failure_threshold=5,
    cooldown_seconds=60,
    success_threshold=2,
)
