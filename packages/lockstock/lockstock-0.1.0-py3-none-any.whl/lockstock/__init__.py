"""
LockStock: The TCP/IP of AI Agency

Cryptographic identity and memory continuity for AI agents.

Usage:
    from lockstock import LockStockAgent, Task

    agent = LockStockAgent(
        server_url="https://lockstock.example.com",
        client_id="my-agent",
        secret="agent-secret-key"
    )

    # Agent now has:
    # - Cryptographic identity
    # - Persistent memory
    # - Clone detection
    # - Teleportation capability
"""

from .agent import LockStockAgent
from .types import Task, AgentPassport, VerifyResponse
from .exceptions import (
    LockStockError,
    AuthenticationError,
    MemoryGapError,
    SplitBrainError,
    CircuitBreakerError,
)

__version__ = "0.1.0"
__all__ = [
    "LockStockAgent",
    "Task",
    "AgentPassport",
    "VerifyResponse",
    "LockStockError",
    "AuthenticationError",
    "MemoryGapError",
    "SplitBrainError",
    "CircuitBreakerError",
]
