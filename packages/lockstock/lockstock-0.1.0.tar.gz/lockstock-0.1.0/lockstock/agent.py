"""LockStock Agent implementation."""

import hashlib
import hmac
import json
import os
import subprocess
import time
from typing import Optional

import requests

from .exceptions import (
    AuthenticationError,
    CircuitBreakerError,
    LockStockError,
    MemoryGapError,
    NetworkError,
    ServerError,
    SplitBrainError,
)
from .types import AgentPassport, Matrix, Task, VerifyResponse, ActionRecord


class LockStockAgent:
    """
    LockStock Agent with cryptographic identity and memory continuity.

    Features:
    - Cryptographic identity verification
    - Persistent memory across restarts
    - Clone detection (split brain prevention)
    - Agent teleportation (migrate between hosts)
    - Velocity monitoring and circuit breaker

    Usage:
        agent = LockStockAgent(
            server_url="https://lockstock.example.com",
            client_id="my-agent",
            secret="agent-secret-key"
        )

        # Bootstrap (first time)
        agent.bootstrap()

        # Perform actions
        response = agent.authenticate(Task.QUERY)

        # Export passport for migration
        passport = agent.export_passport()
        save_to_storage(passport)

        # Resume on new host
        passport = load_from_storage()
        agent = LockStockAgent.from_passport(
            passport,
            server_url="...",
            secret="..."
        )
    """

    def __init__(
        self,
        server_url: str,
        client_id: str,
        secret: str,
        passport: Optional[AgentPassport] = None,
    ):
        """
        Initialize agent.

        Args:
            server_url: LockStock server URL
            client_id: Unique agent identifier
            secret: Shared secret for HMAC signatures
            passport: Optional existing passport for resuming session
        """
        self.server_url = server_url.rstrip("/")
        self.client_id = client_id
        self.secret = secret
        self.passport = passport
        self.bootstrapped = passport is not None

    @classmethod
    def from_passport(
        cls, passport: AgentPassport, server_url: str, secret: str
    ) -> "LockStockAgent":
        """
        Create agent from existing passport (Agent Teleportation).

        This enables moving an agent from Server A to Server B without
        losing memory or identity.

        Args:
            passport: Existing agent passport
            server_url: New server URL
            secret: Agent secret

        Returns:
            Agent instance with restored state
        """
        return cls(
            server_url=server_url,
            client_id=passport.agent_id,
            secret=secret,
            passport=passport,
        )

    @classmethod
    def from_liberty(cls, agent_id: str, server_url: str = "http://localhost:3000") -> "LockStockAgent":
        """
        Create agent by retrieving secret from Liberty hardware vault.

        This is the recommended way to initialize agents in production.
        The secret is never in plaintext in your code or environment variables.

        Prerequisites:
            1. Liberty must be installed: https://gitlab.com/deciphergit/liberty
            2. Agent must be bound: liberty bind --agent <agent_id> --token <genesis_token>

        Flow:
            1. Calls `liberty show <agent_id>` to retrieve secret from hardware vault
            2. Liberty decrypts secret using hardware fingerprint (CPU + MAC + Disk)
            3. Creates agent instance with retrieved secret

        Args:
            agent_id: Agent identifier (from provisioning)
            server_url: LockStock server URL

        Returns:
            Agent instance with hardware-bound secret

        Raises:
            PermissionError: If Liberty cannot decrypt vault (hardware mismatch)
            FileNotFoundError: If Liberty is not installed
            ValueError: If secret retrieval fails

        Example:
            # After running: liberty bind --agent agent_abc123 --token xyz789
            agent = LockStockAgent.from_liberty("agent_abc123")
            agent.authenticate(Task.DEPLOY)
        """
        try:
            # Call Liberty CLI to retrieve secret from hardware vault
            # Preserve LIBERTY_VAULT environment variable if set
            env = os.environ.copy() if hasattr(os, 'environ') else None

            result = subprocess.run(
                ["liberty", "show", agent_id],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
                env=env,
            )

            # Parse output: "agent_id = secret_value"
            output = result.stdout.strip()
            if " = " not in output:
                raise ValueError(f"Unexpected Liberty output format: {output}")

            _, secret = output.split(" = ", 1)
            secret = secret.strip()

            if not secret:
                raise ValueError(f"Liberty returned empty secret for {agent_id}")

            return cls(
                server_url=server_url,
                client_id=agent_id,
                secret=secret,
            )

        except subprocess.CalledProcessError as e:
            if e.returncode == 1 and "No vault found" in e.stdout:
                raise FileNotFoundError(
                    f"Liberty vault not found. Run: liberty init && liberty bind --agent {agent_id} --token <genesis_token>"
                ) from e
            elif "No secret named" in e.stdout:
                raise ValueError(
                    f"Agent '{agent_id}' not found in Liberty vault. Run: liberty bind --agent {agent_id} --token <genesis_token>"
                ) from e
            else:
                raise PermissionError(
                    f"Liberty failed to retrieve secret (hardware mismatch?): {e.stderr or e.stdout}"
                ) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(
                "Liberty CLI not found. Install from: https://gitlab.com/deciphergit/liberty"
            ) from e
        except subprocess.TimeoutExpired:
            raise TimeoutError(
                f"Liberty timed out retrieving secret for {agent_id}"
            )

    def bootstrap(self) -> None:
        """
        Bootstrap the agent (first-time initialization).

        This creates the agent's cryptographic identity on the server.
        Only call this once per agent lifetime.

        Raises:
            ServerError: If bootstrap fails
            NetworkError: If communication fails
        """
        try:
            response = requests.post(
                f"{self.server_url}/bootstrap",
                json={"client_id": self.client_id},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Initialize passport
            root_matrix = Matrix.from_dict(data["root_matrix"])
            self.passport = AgentPassport(
                agent_id=self.client_id,
                last_sequence=0,
                last_hash=data["root_hash"],
                state_matrix=root_matrix,
                last_server_timestamp=0,
                action_history=[],
            )
            self.bootstrapped = True

        except requests.RequestException as e:
            raise NetworkError(f"Bootstrap failed: {e}")
        except Exception as e:
            raise ServerError(f"Bootstrap failed: {e}")

    def authenticate(self, task: Task, metadata: Optional[dict] = None) -> VerifyResponse:
        """
        Authenticate an action with the server.

        This proves the agent's identity and advances its state.

        Args:
            task: Task to perform
            metadata: Optional metadata to include

        Returns:
            VerifyResponse with new state

        Raises:
            AuthenticationError: If authentication fails
            CircuitBreakerError: If velocity limit exceeded
            MemoryGapError: If memory gap detected
            SplitBrainError: If clone detected
        """
        if not self.bootstrapped:
            raise LockStockError("Agent not bootstrapped. Call bootstrap() first.")

        # Generate next state using proper generator matrix multiplication
        from .types import get_generator
        generator = get_generator(task)
        new_matrix = self.passport.state_matrix.multiply(generator)

        # Create signature
        timestamp = int(time.time())
        signature = self._generate_signature(
            task, self.passport.last_hash, new_matrix, timestamp
        )

        # Build request
        request_data = {
            "client_id": self.client_id,
            "task": task.value,
            "parent_hash": self.passport.last_hash,
            "state_matrix": new_matrix.to_dict(use_matrix_notation=True),  # Server expects a11/a12/a21/a22
            "signature": signature,
            "timestamp": timestamp,
        }

        try:
            response = requests.post(
                f"{self.server_url}/verify",
                json=request_data,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            verify_response = VerifyResponse.from_dict(data)

            if verify_response.accepted:
                # Update passport
                action_record = ActionRecord(
                    sequence=self.passport.last_sequence + 1,
                    task=task,
                    state_hash=verify_response.state_hash,
                    parent_hash=self.passport.last_hash,
                    server_timestamp=verify_response.server_timestamp,
                )

                self.passport.action_history.append(action_record)
                self.passport.last_sequence += 1
                self.passport.last_hash = verify_response.state_hash
                self.passport.state_matrix = verify_response.state_matrix
                self.passport.last_server_timestamp = verify_response.server_timestamp

                return verify_response

            else:
                # Handle rejection
                reason = verify_response.reason
                if "velocity" in reason.lower() or "circuit breaker" in reason.lower():
                    raise CircuitBreakerError(reason)
                elif "memory gap" in reason.lower():
                    raise MemoryGapError(reason)
                elif "split brain" in reason.lower() or "clone" in reason.lower():
                    raise SplitBrainError(reason)
                else:
                    raise AuthenticationError(reason)

        except requests.RequestException as e:
            raise NetworkError(f"Authentication failed: {e}")

    def _generate_signature(
        self, task: Task, parent_hash: str, state_matrix: Matrix, timestamp: int
    ) -> str:
        """
        Generate HMAC signature for request.

        CRITICAL: Must match Rust server's crypto.rs format exactly:
        - Pipe separators (|)
        - Capitalized task name (Deploy not deploy)
        - Matrix order: a11,a12,a21,a22 (maps to a,b,c,d)

        Args:
            task: Task being performed
            parent_hash: Hash of parent state
            state_matrix: New state matrix
            timestamp: Request timestamp

        Returns:
            Hex-encoded HMAC signature
        """
        # Construct message to sign (must match Rust server format)
        # Format: "client_id|Task|parent_hash|a11,a12,a21,a22|timestamp"
        task_name = task.name.capitalize()  # DEPLOY -> Deploy, RESTART -> Restart
        message = (
            f"{self.client_id}|{task_name}|{parent_hash}|"
            f"{state_matrix.a},{state_matrix.b},{state_matrix.c},{state_matrix.d}|"
            f"{timestamp}"
        )

        # Generate HMAC-SHA256
        signature = hmac.new(
            self.secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        return signature

    def export_passport(self) -> dict:
        """
        Export agent passport for storage (Agent Teleportation).

        This enables moving the agent to a different host without
        losing memory.

        Returns:
            Passport dictionary ready for serialization

        Example:
            passport = agent.export_passport()
            with open("passport.json", "w") as f:
                json.dump(passport, f)

            # Later, on different host:
            with open("passport.json", "r") as f:
                passport = json.load(f)
            agent = LockStockAgent.from_passport(passport, ...)
        """
        if not self.passport:
            raise LockStockError("No passport to export. Bootstrap first.")
        return self.passport.export()

    def get_action_timeline(self) -> list:
        """
        Get the 'Golden Thread' - complete action history.

        Returns:
            List of formatted action descriptions
        """
        if not self.passport:
            return []
        return self.passport.get_action_timeline()

    def get_status(self) -> dict:
        """
        Get agent status summary.

        Returns:
            Dictionary with agent status
        """
        if not self.passport:
            return {
                "agent_id": self.client_id,
                "bootstrapped": False,
            }

        return {
            "agent_id": self.passport.agent_id,
            "bootstrapped": True,
            "current_sequence": self.passport.last_sequence,
            "last_hash": self.passport.last_hash[:16] + "...",
            "total_actions": len(self.passport.action_history),
            "last_server_timestamp": self.passport.last_server_timestamp,
        }

    def sync(self) -> dict:
        """
        Sync with server after crash (Optimistic Recovery).

        This recovers from scenarios where the agent sent a request,
        the server accepted it, but the agent crashed before saving
        the new state locally.

        The server returns its view of the agent's state (sequence_id
        and state_matrix). The agent checks if it recognizes this state:
        - If YES: Fast-forward to match server
        - If NO: CRITICAL ALERT (possible clone or catastrophic data loss)

        Returns:
            Server state: {"sequence_id": int, "state_hash": str, "state_matrix": Matrix}

        Raises:
            SplitBrainError: If server state is unknown (possible clone active)
            NetworkError: If communication fails
        """
        if not self.bootstrapped:
            raise LockStockError("Agent not bootstrapped. Call bootstrap() first.")

        try:
            response = requests.post(
                f"{self.server_url}/sync",
                json={"client_id": self.client_id},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            server_sequence = data["sequence_id"]
            server_hash = data["state_hash"]
            server_matrix = Matrix.from_dict(data["state_matrix"])

            # Check if we recognize this state
            if server_sequence == self.passport.last_sequence:
                # We're already in sync
                print(f"✅ Already in sync at sequence {server_sequence}")
                return data

            elif server_sequence > self.passport.last_sequence:
                # Server is ahead - check if we have this hash in our history
                known_hashes = {action.state_hash for action in self.passport.action_history}
                known_hashes.add(self.passport.last_hash)

                if server_hash in known_hashes:
                    # We recognize this state - fast-forward
                    print(f"⚠️  Recovering: Fast-forwarding from seq {self.passport.last_sequence} to {server_sequence}")
                    self.passport.last_sequence = server_sequence
                    self.passport.last_hash = server_hash
                    self.passport.state_matrix = server_matrix
                    return data
                else:
                    # Server has a state we don't recognize - CRITICAL
                    raise SplitBrainError(
                        f"CRITICAL: Server at sequence {server_sequence} with unknown hash {server_hash[:16]}... "
                        f"Possible clone active or catastrophic data loss. "
                        f"Agent last known sequence: {self.passport.last_sequence}"
                    )

            else:
                # Agent is ahead of server - this shouldn't happen normally
                print(f"⚠️  WARNING: Agent sequence {self.passport.last_sequence} > Server sequence {server_sequence}")
                return data

        except requests.RequestException as e:
            raise NetworkError(f"Sync failed: {e}")

    def rotate_secret(self, new_secret: str) -> None:
        """
        Rotate the HMAC secret using dual-window protocol.

        This implements two-phase commit to prevent lockout on crash:

        Phase 1 (PROPOSE_ROTATION):
        - Agent signs request with OLD secret
        - Server stores NEW secret as "pending" while keeping OLD active
        - Agent atomically saves NEW secret to disk (critical crash boundary)

        Phase 2 (CONFIRM_ROTATION):
        - Agent signs request with NEW secret
        - Server matches against pending secret and promotes to active
        - OLD secret is retired

        Crash Recovery:
        - If crash after disk write but before confirm: Agent reboots with NEW secret,
          server auto-confirms by matching against pending
        - If crash before disk write: Agent reboots with OLD secret,
          server still accepts OLD secret

        Args:
            new_secret: The new HMAC secret key

        Raises:
            LockStockError: If not bootstrapped
            NetworkError: If communication fails
            AuthenticationError: If rotation fails
        """
        if not self.bootstrapped:
            raise LockStockError("Agent not bootstrapped. Call bootstrap() first.")

        # Calculate hash of new secret for Phase 1
        new_secret_hash = hashlib.sha256(new_secret.encode()).hexdigest()

        # Phase 1: PROPOSE (signed with OLD secret)
        print("🔄 Phase 1: Proposing key rotation...")
        print(f"   Server will store new secret as PENDING while keeping old secret ACTIVE")

        try:
            # This must use the OLD secret (self.secret)
            new_matrix = Matrix(
                a=(self.passport.state_matrix.a + 1) % 65537,
                b=self.passport.state_matrix.b,
                c=self.passport.state_matrix.c,
                d=(self.passport.state_matrix.d + 1) % 65537,
            )

            timestamp = int(time.time())
            signature = self._generate_signature(
                Task.PROPOSE_ROTATION,
                self.passport.last_hash,
                new_matrix,
                timestamp,
            )

            response = requests.post(
                f"{self.server_url}/verify",
                json={
                    "client_id": self.client_id,
                    "task": Task.PROPOSE_ROTATION.value,
                    "parent_hash": self.passport.last_hash,
                    "state_matrix": new_matrix.to_dict(),
                    "signature": signature,
                    "timestamp": timestamp,
                    "metadata": {"next_secret_hash": new_secret_hash},
                },
                timeout=10,
            )
            response.raise_for_status()

        except requests.RequestException as e:
            raise NetworkError(f"Rotation proposal failed: {e}")

        # CRITICAL CRASH BOUNDARY: Write to disk NOW
        # If we crash after this point, we have the new key and server has it as pending
        print("💾 CRITICAL: Saving new secret to disk...")
        old_secret = self.secret
        self.secret = new_secret

        # Phase 2: CONFIRM (signed with NEW secret)
        print("🔄 Phase 2: Confirming key rotation...")
        print(f"   Server will promote PENDING secret to ACTIVE")

        try:
            confirm_matrix = Matrix(
                a=(new_matrix.a + 1) % 65537,
                b=new_matrix.b,
                c=new_matrix.c,
                d=(new_matrix.d + 1) % 65537,
            )

            timestamp = int(time.time())
            # This signature uses the NEW secret
            signature = self._generate_signature(
                Task.CONFIRM_ROTATION,
                self.passport.last_hash,
                confirm_matrix,
                timestamp,
            )

            response = requests.post(
                f"{self.server_url}/verify",
                json={
                    "client_id": self.client_id,
                    "task": Task.CONFIRM_ROTATION.value,
                    "parent_hash": self.passport.last_hash,
                    "state_matrix": confirm_matrix.to_dict(),
                    "signature": signature,
                    "timestamp": timestamp,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Update passport
            verify_response = VerifyResponse.from_dict(data)
            if verify_response.accepted:
                self.passport.last_hash = verify_response.state_hash
                self.passport.state_matrix = verify_response.state_matrix
                self.passport.last_sequence += 1
                print("✅ Key rotation complete. Old secret retired, new secret active.")
            else:
                # Rotation failed - rollback to old secret
                self.secret = old_secret
                raise AuthenticationError(f"Rotation confirmation failed: {verify_response.reason}")

        except requests.RequestException as e:
            # Rotation failed - rollback to old secret
            self.secret = old_secret
            raise NetworkError(f"Rotation confirmation failed: {e}")
