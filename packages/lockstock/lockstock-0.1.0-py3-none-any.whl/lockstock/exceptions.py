"""Exception types for LockStock protocol."""


class LockStockError(Exception):
    """Base exception for all LockStock errors."""

    pass


class AuthenticationError(LockStockError):
    """Raised when agent authentication fails (invalid signature, unauthorized task, etc.)."""

    pass


class MemoryGapError(LockStockError):
    """
    Raised when agent has a memory gap (discontinuous sequence).

    This indicates the agent tried to resume from an invalid state,
    possibly due to data loss or corruption.
    """

    pass


class SplitBrainError(LockStockError):
    """
    Raised when split brain is detected (two instances of same agent).

    This is a CRITICAL security event indicating:
    - Agent was cloned
    - Agent is running on multiple hosts simultaneously
    - State has diverged
    """

    pass


class CircuitBreakerError(LockStockError):
    """
    Raised when circuit breaker trips due to velocity anomaly.

    This indicates the agent is making requests too rapidly,
    which could signal:
    - Infinite loop
    - Rogue behavior
    - Compromised agent
    """

    pass


class ServerError(LockStockError):
    """Raised when server returns an error."""

    pass


class NetworkError(LockStockError):
    """Raised when network communication fails."""

    pass
