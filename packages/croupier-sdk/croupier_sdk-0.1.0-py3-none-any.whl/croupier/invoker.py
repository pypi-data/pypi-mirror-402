"""
Croupier Python SDK - Invoker Implementation

Provides client functionality for invoking functions registered with the Croupier platform.
Supports synchronous calls, asynchronous jobs, and event streaming.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import AsyncIterator, Callable, Dict, Optional, Any

import grpc
import grpc.aio

# Reuse the proto module loader from the main package
_GENERATED_ROOT = Path(__file__).resolve().parent.parent / "generated"


def _ensure_parent_packages(module_name: str) -> None:
    parts = module_name.split(".")[:-1]
    prefix = ""
    for part in parts:
        prefix = f"{prefix}.{part}" if prefix else part
        if prefix not in __import__("sys").modules:
            module = ModuleType(prefix)
            module.__path__ = []  # type: ignore[attr-defined]
            __import__("sys").modules[prefix] = module


def _load_proto_module(module_name: str) -> ModuleType:
    import importlib.util
    import sys

    if module_name in sys.modules:
        return sys.modules[module_name]

    relative = Path(*module_name.split("."))  # type: ignore[arg-type]
    file_path = _GENERATED_ROOT / relative.with_suffix(".py")
    if not file_path.exists():
        raise ImportError(f"Generated module {module_name} not found at {file_path}")

    _ensure_parent_packages(module_name)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load protobuf modules
function_pb2 = _load_proto_module("croupier.function.v1.function_pb2")
function_pb2_grpc = _load_proto_module("croupier.function.v1.function_pb2_grpc")

LOG = logging.getLogger(__name__)


@dataclass
class ReconnectConfig:
    """Configuration for automatic reconnection with exponential backoff."""

    enabled: bool = True
    max_attempts: int = 0  # 0 = infinite retries
    initial_delay_ms: int = 1000  # 1 second
    max_delay_ms: int = 30000  # 30 seconds
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.2  # Add randomness to delay (0-1)


def _default_reconnect_config() -> ReconnectConfig:
    """Create default reconnection configuration."""
    return ReconnectConfig()


@dataclass
class RetryConfig:
    """Configuration for retrying failed invocations."""

    enabled: bool = True
    max_attempts: int = 3  # Maximum retry attempts
    initial_delay_ms: int = 100  # Initial retry delay in milliseconds
    max_delay_ms: int = 5000  # Maximum retry delay in milliseconds
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1
    retryable_status_codes: tuple = (
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.INTERNAL,
        grpc.StatusCode.UNKNOWN,
        grpc.StatusCode.ABORTED,
        grpc.StatusCode.DEADLINE_EXCEEDED,
    )


def _default_retry_config() -> RetryConfig:
    """Create default retry configuration."""
    return RetryConfig()


def _calculate_reconnect_delay(attempt: int, config: ReconnectConfig) -> float:
    """
    Calculate reconnection delay using exponential backoff with jitter.

    Args:
        attempt: Reconnection attempt number (0-indexed)
        config: Reconnect configuration

    Returns:
        Delay in seconds
    """
    # Exponential backoff
    delay = config.initial_delay_ms * (config.backoff_multiplier**attempt)
    delay = min(delay, config.max_delay_ms)

    # Add jitter to prevent thundering herd
    jitter = delay * config.jitter_factor * (random.random() * 2 - 1)
    delay += jitter

    return max(delay, 0) / 1000.0  # Convert to seconds


def _is_connection_error(error: Exception) -> bool:
    """
    Check if an error is a connection-related error that should trigger reconnection.

    Args:
        error: The exception to check

    Returns:
        True if this is a connection error
    """
    if isinstance(error, grpc.RpcError):
        # gRPC errors that indicate connection problems
        code = error.code()
        # UNAVAILABLE (14) - Server unavailable
        # UNKNOWN (2) - Might be connection issue
        # INTERNAL (13) - Could be connection failure
        return code in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.UNKNOWN)

    # Check error message for connection-related strings
    error_str = str(error).lower()
    connection_keywords = [
        "connection",
        "connect",
        "network",
        "timeout",
        "unreachable",
        "refused",
        "reset",
    ]
    return any(keyword in error_str for keyword in connection_keywords)


@dataclass
class InvokerConfig:
    """Configuration for the Invoker connection."""

    address: str = "127.0.0.1:8080"
    timeout: int = 30000  # milliseconds
    insecure: bool = True
    ca_file: str = ""
    cert_file: str = ""
    key_file: str = ""
    server_name: str = ""
    reconnect: ReconnectConfig = field(default_factory=_default_reconnect_config)
    retry: RetryConfig = field(default_factory=_default_retry_config)


@dataclass
class InvokeOptions:
    """Options for function invocation."""

    idempotency_key: Optional[str] = None
    timeout: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    retry: Optional[RetryConfig] = None  # Override retry settings for this invocation


@dataclass
class JobEventInfo:
    """Information about a job event."""

    type: str  # "started" | "progress" | "completed" | "error" | "cancelled"
    job_id: str
    payload: Optional[str] = None
    message: Optional[str] = None
    progress: Optional[int] = None
    error: Optional[str] = None
    done: bool = False


class Invoker:
    """
    Client for invoking functions registered with the Croupier platform.

    Supports:
    - Synchronous function invocation
    - Asynchronous job execution with event streaming
    - Job cancellation
    - Payload validation with schemas
    - Automatic reconnection with exponential backoff
    """

    def __init__(self, config: Optional[InvokerConfig] = None):
        """Initialize the invoker with configuration."""
        self.config = config or InvokerConfig()
        self._channel: Optional[grpc.aio.Channel] = None
        self._client: Any = None  # type: ignore[attr-defined]
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._connected = False
        self._lock: Optional[asyncio.Lock] = None

        # Reconnection state
        self._reconnect_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0
        self._is_reconnecting = False
        self._stop_reconnect = asyncio.Event()

    async def connect(self) -> None:
        """Connect to the server."""
        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            if self._connected:
                return

            LOG.info(f"Connecting to server/agent at: {self.config.address}")

            # Set up connection options
            if self.config.insecure:
                self._channel = grpc.aio.insecure_channel(self.config.address)
            else:
                creds = self._create_credentials()
                self._channel = grpc.aio.secure_channel(self.config.address, creds)

            # Wait for channel ready with timeout
            try:
                timeout_sec = self.config.timeout / 1000.0
                await asyncio.wait_for(self._channel.channel_ready(), timeout=timeout_sec)
            except (grpc.RpcError, asyncio.TimeoutError, Exception) as e:
                error_msg = f"Failed to connect to {self.config.address}"
                if isinstance(e, asyncio.TimeoutError):
                    error_msg += f": connection timeout after {timeout_sec}s"
                elif isinstance(e, grpc.RpcError):
                    error_msg += f": {e.details()}"
                else:
                    error_msg += f": {e}"
                LOG.error(error_msg)

                # Schedule reconnection if enabled
                if self.config.reconnect.enabled:
                    self._schedule_reconnect()

                raise Exception(error_msg) from e

            self._client = function_pb2_grpc.FunctionServiceStub(self._channel)
            self._connected = True
            self._reconnect_attempts = 0  # Reset on success

            LOG.info(f"Connected to: {self.config.address}")

    async def invoke(
        self, function_id: str, payload: str, options: Optional[InvokeOptions] = None
    ) -> str:
        """Synchronously invoke a function."""
        options = options or InvokeOptions()

        # Client-side validation (before connect to fail fast)
        if function_id in self._schemas:
            schema = self._schemas[function_id]
            self._validate_payload(payload, schema)

        if not self._connected:
            await self.connect()

        # Execute with retry logic
        async def _invoke() -> str:
            # Build request
            request = function_pb2.InvokeRequest()
            request.function_id = function_id
            request.payload = payload.encode("utf-8")

            if options.idempotency_key:
                request.idempotency_key = options.idempotency_key

            if options.headers:
                for k, v in options.headers.items():
                    request.metadata[k] = v

            # Set timeout
            timeout_sec = (options.timeout or self.config.timeout) / 1000.0

            assert self._client is not None
            response = await self._client.Invoke(request, timeout=timeout_sec)
            return response.payload.decode("utf-8") if response.payload else ""

        try:
            return await self._execute_with_retry(_invoke, options)  # type: ignore[no-any-return]
        except grpc.RpcError as e:
            # On connection error, schedule reconnection
            if _is_connection_error(e) and self.config.reconnect.enabled:
                self._connected = False
                self._schedule_reconnect()
            raise Exception(f"invoke RPC failed: {e.details()}") from e

    async def start_job(
        self, function_id: str, payload: str, options: Optional[InvokeOptions] = None
    ) -> str:
        """Start an asynchronous job."""
        options = options or InvokeOptions()

        if not self._connected:
            await self.connect()

        # Client-side validation
        if function_id in self._schemas:
            schema = self._schemas[function_id]
            self._validate_payload(payload, schema)

        # Execute with retry logic
        async def _start_job() -> str:
            # Build request
            request = function_pb2.InvokeRequest()
            request.function_id = function_id
            request.payload = payload.encode("utf-8")

            if options.idempotency_key:
                request.idempotency_key = options.idempotency_key

            if options.headers:
                for k, v in options.headers.items():
                    request.metadata[k] = v

            # Set timeout
            timeout_sec = (options.timeout or self.config.timeout) / 1000.0

            assert self._client is not None
            response = await self._client.StartJob(request, timeout=timeout_sec)
            return response.job_id  # type: ignore[no-any-return]

        try:
            return await self._execute_with_retry(_start_job, options)  # type: ignore[no-any-return]
        except grpc.RpcError as e:
            if _is_connection_error(e) and self.config.reconnect.enabled:
                self._connected = False
                self._schedule_reconnect()
            raise Exception(f"start job RPC failed: {e.details()}") from e

    async def stream_job(self, job_id: str) -> AsyncIterator[JobEventInfo]:
        """Stream events from a running job."""
        if not self._connected:
            await self.connect()

        request = function_pb2.JobStreamRequest()
        request.job_id = job_id

        try:
            assert self._client is not None
            call = self._client.StreamJob(request)
            async for event in call:
                info = JobEventInfo(
                    type=event.type,
                    job_id=job_id,
                    payload=event.payload.decode("utf-8") if event.payload else None,
                    message=event.message,
                    progress=event.progress if event.HasField("progress") else None,
                    done=event.type in ("completed", "error", "cancelled"),
                )

                if event.type == "error":
                    info.error = event.message
                    info.done = True

                yield info

                if info.done:
                    break

        except grpc.RpcError as e:
            if _is_connection_error(e) and self.config.reconnect.enabled:
                self._connected = False
                self._schedule_reconnect()
            error_event = JobEventInfo(
                type="error",
                job_id=job_id,
                error=f"stream job RPC failed: {e.details()}",
                done=True,
            )
            yield error_event

    async def cancel_job(self, job_id: str) -> None:
        """Cancel a running job."""
        if not self._connected:
            await self.connect()

        request = function_pb2.CancelJobRequest()
        request.job_id = job_id

        try:
            assert self._client is not None
            await self._client.CancelJob(request, timeout=5.0)
        except grpc.RpcError as e:
            if _is_connection_error(e) and self.config.reconnect.enabled:
                self._connected = False
                self._schedule_reconnect()
            raise Exception(f"cancel job RPC failed: {e.details()}") from e

    async def set_schema(self, function_id: str, schema: Dict[str, Any]) -> None:
        """Set validation schema for a function."""
        self._schemas[function_id] = schema
        LOG.debug(f"Set schema for function: {function_id}")

    async def close(self) -> None:
        """Close the invoker."""
        if self._lock is None:
            self._lock = asyncio.Lock()

        # Cancel any pending reconnection
        self._stop_reconnect.set()
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            # Always clear schemas regardless of connection state
            self._schemas.clear()

            if not self._connected:
                return

            self._connected = False

            if self._channel:
                await self._channel.close()
                self._channel = None

            if self._client:
                self._client = None

            LOG.info("Invoker closed")

    def _create_credentials(self) -> grpc.ChannelCredentials:
        """Create SSL credentials for TLS connection."""
        try:
            # Load CA certificate
            ca_cert = None
            if self.config.ca_file:
                with open(self.config.ca_file, "rb") as f:
                    ca_cert = f.read()

            # Load client certificate and key
            cert_chain = None
            private_key = None
            if self.config.cert_file and self.config.key_file:
                with open(self.config.cert_file, "rb") as f:
                    cert_chain = f.read()
                with open(self.config.key_file, "rb") as f:
                    private_key = f.read()

            credentials = grpc.ssl_channel_credentials(
                root_certificates=ca_cert,
                certificate_chain=cert_chain,
                private_key=private_key,
            )

            # Note: server_name verification would require additional setup
            return credentials
        except Exception as e:
            raise Exception(f"Failed to create SSL credentials: {e}") from e

    def _validate_payload(self, payload: str, schema: Dict[str, Any]) -> None:
        """Validate payload against JSON Schema."""
        if not schema:
            if not payload:
                raise Exception("Payload cannot be empty")
            return

        try:
            payload_obj = json.loads(payload)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON payload: {e}") from e

        # Required field validation
        required = schema.get("required", [])
        if isinstance(required, list):
            for fieldname in required:
                if fieldname not in payload_obj:
                    raise Exception(
                        f"Payload validation failed: missing required field '{fieldname}'"
                    )

        # Type validation for properties
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for fieldname, value in payload_obj.items():
                if fieldname in properties:
                    field_schema = properties[fieldname]
                    expected_type = field_schema.get("type")

                    if expected_type:
                        # Type mapping from JSON Schema to Python types
                        type_map = {
                            "string": str,
                            "number": (int, float),
                            "integer": int,
                            "boolean": bool,
                            "array": list,
                            "object": dict,
                        }

                        expected_python_types = type_map.get(expected_type)
                        if expected_python_types:
                            if not isinstance(value, expected_python_types):  # type: ignore[arg-type]
                                actual_type = type(value).__name__
                                raise Exception(
                                    f"Payload validation failed: field '{field}' should be {expected_type}, got {actual_type}"
                                )

        LOG.debug(f"Payload validation for {len(payload)} characters completed")

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt with exponential backoff."""
        if self._is_reconnecting:
            return

        # Check max attempts
        if (
            self.config.reconnect.max_attempts > 0
            and self._reconnect_attempts >= self.config.reconnect.max_attempts
        ):
            LOG.error("Max reconnection attempts reached. Giving up.")
            return

        self._is_reconnecting = True

        # Cancel existing task if any
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()

        # Create new reconnection task
        self._stop_reconnect.clear()
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Background task that handles reconnection with exponential backoff."""
        try:
            while not self._stop_reconnect.is_set():
                # Check max attempts
                if (
                    self.config.reconnect.max_attempts > 0
                    and self._reconnect_attempts >= self.config.reconnect.max_attempts
                ):
                    LOG.error("Max reconnection attempts reached. Giving up.")
                    break

                # Calculate delay
                delay = _calculate_reconnect_delay(self._reconnect_attempts, self.config.reconnect)
                self._reconnect_attempts += 1

                LOG.info(
                    f"Scheduling reconnection attempt {self._reconnect_attempts} "
                    f"in {delay:.1f}s"
                )

                # Wait for delay or stop signal
                try:
                    await asyncio.wait_for(self._stop_reconnect.wait(), timeout=delay)
                    # Stop was signaled
                    break
                except asyncio.TimeoutError:
                    # Delay elapsed, proceed with reconnection
                    pass

                # Attempt reconnection
                try:
                    await self.connect()
                    # Success
                    LOG.info("Reconnection successful")
                    break
                except Exception as e:
                    LOG.warning(f"Reconnection attempt failed: {e}")
                    # Continue loop for next attempt

        except asyncio.CancelledError:
            LOG.debug("Reconnection task cancelled")
        finally:
            self._is_reconnecting = False

    def _is_retryable_error(self, error: Exception, config: RetryConfig) -> bool:
        """Check if an error should trigger a retry."""
        if not config.enabled:
            return False

        if isinstance(error, grpc.RpcError):
            return error.code() in config.retryable_status_codes

        return False

    def _calculate_retry_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        # Exponential backoff
        base_delay = config.initial_delay_ms
        exponential_delay = base_delay * (config.backoff_multiplier**attempt)

        # Cap at max delay
        capped_delay = min(exponential_delay, config.max_delay_ms)

        # Add jitter
        jitter = capped_delay * config.jitter_factor * (random.random() * 2 - 1)

        return max(capped_delay + jitter, 0) / 1000.0  # Convert to seconds

    async def _execute_with_retry(
        self, fn: Callable, options: Optional[InvokeOptions] = None
    ) -> Any:
        """Execute a function with retry logic."""
        retry_config = options.retry if options and options.retry else self.config.retry

        if not retry_config.enabled:
            return await fn()

        last_error: Optional[Exception] = None
        for attempt in range(retry_config.max_attempts + 1):
            try:
                return await fn()
            except Exception as e:
                last_error = e

                # Don't retry on the last attempt
                if attempt >= retry_config.max_attempts:
                    break

                # Check if error is retryable
                if not self._is_retryable_error(e, retry_config):
                    break

                # Calculate delay and wait
                delay = self._calculate_retry_delay(attempt, retry_config)
                LOG.info(
                    f"Retry attempt {attempt + 1}/{retry_config.max_attempts} after {delay:.1f}s"
                )
                await asyncio.sleep(delay)

        assert last_error is not None
        raise last_error


# Convenience functions
def default_invoker_config() -> InvokerConfig:
    """Create a default Invoker configuration."""
    return InvokerConfig()


def create_invoker(config: Optional[InvokerConfig] = None) -> Invoker:
    """Create a new Invoker instance."""
    return Invoker(config)


# Synchronous wrapper for backward compatibility
class SyncInvoker:
    """
    Synchronous wrapper around the async Invoker.

    Provides a blocking interface for applications that don't use asyncio.
    """

    def __init__(self, config: Optional[InvokerConfig] = None):
        self._async_invoker = Invoker(config)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need a new loop in a thread
                raise RuntimeError("Running event loop detected")
            return loop
        except RuntimeError:
            # Create new loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def connect(self) -> None:
        """Connect to the server."""
        loop = self._get_loop()
        loop.run_until_complete(self._async_invoker.connect())

    def invoke(
        self, function_id: str, payload: str, options: Optional[InvokeOptions] = None
    ) -> str:
        """Synchronously invoke a function."""
        loop = self._get_loop()
        return loop.run_until_complete(self._async_invoker.invoke(function_id, payload, options))

    def start_job(
        self, function_id: str, payload: str, options: Optional[InvokeOptions] = None
    ) -> str:
        """Start an asynchronous job."""
        loop = self._get_loop()
        return loop.run_until_complete(self._async_invoker.start_job(function_id, payload, options))

    def stream_job(self, job_id: str):
        """Stream events from a running job (returns iterator)."""
        loop = self._get_loop()
        async_gen = self._async_invoker.stream_job(job_id)

        class SyncIterator:
            def __init__(self, async_gen, loop):
                self._async_gen = async_gen
                self._loop = loop

            def __iter__(self):
                return self

            def __next__(self):
                try:
                    return self._loop.run_until_complete(self._async_gen.__anext__())
                except StopAsyncIteration:
                    raise StopIteration

        return SyncIterator(async_gen, loop)

    def cancel_job(self, job_id: str) -> None:
        """Cancel a running job."""
        loop = self._get_loop()
        loop.run_until_complete(self._async_invoker.cancel_job(job_id))

    def set_schema(self, function_id: str, schema: Dict[str, Any]) -> None:
        """Set validation schema for a function."""
        self._async_invoker._schemas[function_id] = schema
        LOG.debug(f"Set schema for function: {function_id}")

    def close(self) -> None:
        """Close the invoker."""
        loop = self._get_loop()
        loop.run_until_complete(self._async_invoker.close())


def create_sync_invoker(config: Optional[InvokerConfig] = None) -> SyncInvoker:
    """Create a new synchronous Invoker instance."""
    return SyncInvoker(config)


__all__ = [
    "ReconnectConfig",
    "InvokerConfig",
    "InvokeOptions",
    "JobEventInfo",
    "Invoker",
    "SyncInvoker",
    "default_invoker_config",
    "create_invoker",
    "create_sync_invoker",
]
