"""Type definitions for LockStock protocol."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Task(Enum):
    """Authorized task types for agent actions."""

    BOOTSTRAP = "bootstrap"
    DEPLOY = "deploy"
    RESTART = "restart"
    BACKUP = "backup"
    UPDATE = "update"
    QUERY = "query"
    EXECUTE = "execute"
    PROPOSE_ROTATION = "propose_rotation"  # Phase 1 of dual-window key rotation
    CONFIRM_ROTATION = "confirm_rotation"  # Phase 2 of dual-window key rotation
    SYNC = "sync"  # Crash recovery probe


FIELD_MODULUS = 65537  # Field modulus for finite field arithmetic


@dataclass
class Matrix:
    """2x2 matrix over finite field F₆₅₅₃₇ (the 'soul' of an agent)."""

    a: int  # Maps to a11 in server notation
    b: int  # Maps to a12 in server notation
    c: int  # Maps to a21 in server notation
    d: int  # Maps to a22 in server notation

    def to_dict(self, use_matrix_notation=False):
        """Convert to dictionary for JSON serialization.

        Args:
            use_matrix_notation: If True, use a11/a12/a21/a22 keys (server format).
                                If False, use a/b/c/d keys (client format).
        """
        if use_matrix_notation:
            # Server format (matrix notation)
            return {
                "a11": self.a,
                "a12": self.b,
                "a21": self.c,
                "a22": self.d,
            }
        else:
            # Client format (single letters)
            return {
                "a": self.a,
                "b": self.b,
                "c": self.c,
                "d": self.d,
            }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary."""
        # Handle both formats: {a, b, c, d} and {a11, a12, a21, a22}
        if "a11" in data:
            # Server format (matrix notation)
            return cls(
                a=data["a11"],
                b=data["a12"],
                c=data["a21"],
                d=data["a22"],
            )
        else:
            # Client format (single letters)
            return cls(
                a=data["a"],
                b=data["b"],
                c=data["c"],
                d=data["d"],
            )

    def multiply(self, other: "Matrix") -> "Matrix":
        """Multiply this matrix by another matrix in F_65537.

        Standard matrix multiplication: [[a, b], [c, d]] × [[e, f], [g, h]]
        Result: [[ae+bg, af+bh], [ce+dg, cf+dh]] mod FIELD_MODULUS
        """
        def mod(x):
            """Modulo operation ensuring result is in [0, FIELD_MODULUS)"""
            return ((x % FIELD_MODULUS) + FIELD_MODULUS) % FIELD_MODULUS

        a11 = mod(self.a * other.a + self.b * other.c)
        a12 = mod(self.a * other.b + self.b * other.d)
        a21 = mod(self.c * other.a + self.d * other.c)
        a22 = mod(self.c * other.b + self.d * other.d)

        return Matrix(a=a11, b=a12, c=a21, d=a22)

    def __repr__(self):
        return f"Matrix([[{self.a}, {self.b}], [{self.c}, {self.d}]])"


def get_generator(task: Task) -> Matrix:
    """Get the generator matrix for a specific task.

    These are Burau representation generators for the braid group B3.
    Each task has a distinct, invertible generator matrix.
    """
    if task == Task.DEPLOY:
        return Matrix(a=1, b=1, c=0, d=1)
    elif task == Task.RESTART:
        return Matrix(a=1, b=0, c=1, d=1)
    elif task == Task.BACKUP:
        return Matrix(a=2, b=1, c=1, d=1)
    elif task == Task.ROLLBACK:
        return Matrix(a=1, b=1, c=1, d=2)
    else:
        raise ValueError(f"Unknown task: {task}")


@dataclass
class ActionRecord:
    """Single action in the agent's history (the 'golden thread')."""

    sequence: int
    task: Task
    state_hash: str
    parent_hash: str
    server_timestamp: int

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "sequence": self.sequence,
            "task": self.task.value,
            "state_hash": self.state_hash,
            "parent_hash": self.parent_hash,
            "server_timestamp": self.server_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary."""
        return cls(
            sequence=data["sequence"],
            task=Task(data["task"]),
            state_hash=data["state_hash"],
            parent_hash=data["parent_hash"],
            server_timestamp=data["server_timestamp"],
        )


@dataclass
class AgentPassport:
    """
    Agent Passport: The cryptographic "soul" of an AI agent.

    This contains everything needed to prove:
    1. Who the agent is (agent_id)
    2. What it has done (last_sequence)
    3. Where it left off (last_hash)
    4. Its accumulated state (state_matrix)

    Think of this as the agent's "autobiography" - a cryptographic
    proof of its entire existence and action history.
    """

    agent_id: str
    last_sequence: int
    last_hash: str
    state_matrix: Matrix
    last_server_timestamp: int
    action_history: List[ActionRecord]

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "agent_id": self.agent_id,
            "last_sequence": self.last_sequence,
            "last_hash": self.last_hash,
            "state_matrix": self.state_matrix.to_dict(),
            "last_server_timestamp": self.last_server_timestamp,
            "action_history": [action.to_dict() for action in self.action_history],
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            last_sequence=data["last_sequence"],
            last_hash=data["last_hash"],
            state_matrix=Matrix.from_dict(data["state_matrix"]),
            last_server_timestamp=data["last_server_timestamp"],
            action_history=[
                ActionRecord.from_dict(action) for action in data["action_history"]
            ],
        )

    def export(self) -> dict:
        """Export passport for storage (Agent Teleportation)."""
        return self.to_dict()

    @classmethod
    def import_passport(cls, data: dict) -> "AgentPassport":
        """Import passport from storage (Agent Teleportation)."""
        return cls.from_dict(data)

    def get_action_timeline(self) -> List[str]:
        """
        Get the 'Golden Thread' - complete action history.

        Returns:
            List of formatted action descriptions:
            ["Seq #1: BOOTSTRAP (hash: a3f4b2e1...)",
             "Seq #2: QUERY (hash: b2e1c9d7...)",
             ...]
        """
        return [
            f"Seq #{action.sequence}: {action.task.value.upper()} "
            f"(hash: {action.state_hash[:8]}...)"
            for action in self.action_history
        ]


@dataclass
class VerifyResponse:
    """Response from server after verification."""

    accepted: bool
    state_hash: Optional[str] = None
    state_matrix: Optional[Matrix] = None
    server_timestamp: Optional[int] = None
    reason: Optional[str] = None
    buffered: bool = False

    @classmethod
    def from_dict(cls, data: dict):
        """Create from API response."""
        # Handle both flat format (with 'status' key) and nested format
        status = data.get("status")

        if status == "accepted" or (not status and "state_hash" in data):
            # Flat format: {'status': 'accepted', 'state_hash': ..., ...}
            return cls(
                accepted=True,
                state_hash=data["state_hash"],
                state_matrix=Matrix.from_dict(data["state_matrix"]),
                server_timestamp=data["server_timestamp"],
            )
        elif status == "rejected" or "reason" in data:
            # Flat format: {'status': 'rejected', 'reason': ..., ...}
            return cls(
                accepted=False,
                reason=data["reason"],
                server_timestamp=data["server_timestamp"],
            )
        elif status == "buffered":
            # Flat format: {'status': 'buffered', 'reason': ..., ...}
            return cls(
                accepted=False,
                buffered=True,
                reason=data["reason"],
                server_timestamp=data["server_timestamp"],
            )
        elif "accepted" in data:
            # Nested format: {'accepted': {'state_hash': ..., ...}}
            return cls(
                accepted=True,
                state_hash=data["accepted"]["state_hash"],
                state_matrix=Matrix.from_dict(data["accepted"]["state_matrix"]),
                server_timestamp=data["accepted"]["server_timestamp"],
            )
        elif "rejected" in data:
            return cls(
                accepted=False,
                reason=data["rejected"]["reason"],
                server_timestamp=data["rejected"]["server_timestamp"],
            )
        elif "buffered" in data:
            return cls(
                accepted=False,
                buffered=True,
                reason=data["buffered"]["reason"],
                server_timestamp=data["buffered"]["server_timestamp"],
            )
        else:
            raise ValueError(f"Unknown response format: {data}")
