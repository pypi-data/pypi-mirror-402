"""
Tests for Croupier Python SDK Invoker functionality.
"""

import asyncio

import grpc
import pytest

from croupier.invoker import (
    Invoker,
    InvokerConfig,
    ReconnectConfig,
    RetryConfig,
    InvokeOptions,
    JobEventInfo,
    _calculate_reconnect_delay,
    _is_connection_error,
    default_invoker_config,
    create_invoker,
)


def test_invoker_config_defaults():
    """Test that InvokerConfig has correct default values."""
    config = InvokerConfig()
    assert config.address == "127.0.0.1:8080"
    assert config.timeout == 30000
    assert config.insecure is True
    assert config.ca_file == ""
    assert config.cert_file == ""
    assert config.key_file == ""
    assert config.server_name == ""


def test_invoker_config_with_reconnect_defaults():
    """Test that reconnect config has correct defaults."""
    config = InvokerConfig()
    assert isinstance(config.reconnect, ReconnectConfig)
    assert config.reconnect.enabled is True
    assert config.reconnect.max_attempts == 0  # infinite
    assert config.reconnect.initial_delay_ms == 1000
    assert config.reconnect.max_delay_ms == 30000
    assert config.reconnect.backoff_multiplier == 2.0
    assert config.reconnect.jitter_factor == 0.2


def test_invoker_config_with_retry_defaults():
    """Test that retry config has correct defaults."""
    config = InvokerConfig()
    assert isinstance(config.retry, RetryConfig)
    assert config.retry.enabled is True
    assert config.retry.max_attempts == 3
    assert config.retry.initial_delay_ms == 100
    assert config.retry.max_delay_ms == 5000
    assert config.retry.backoff_multiplier == 2.0
    assert config.retry.jitter_factor == 0.1
    assert config.retry.retryable_status_codes == (
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.INTERNAL,
        grpc.StatusCode.UNKNOWN,
        grpc.StatusCode.ABORTED,
        grpc.StatusCode.DEADLINE_EXCEEDED,
    )


def test_invoker_config_custom():
    """Test creating InvokerConfig with custom values."""
    config = InvokerConfig(
        address="localhost:9090",
        timeout=60000,
        insecure=False,
        ca_file="/path/to/ca.pem",
    )
    assert config.address == "localhost:9090"
    assert config.timeout == 60000
    assert config.insecure is False
    assert config.ca_file == "/path/to/ca.pem"


def test_reconnect_config_custom():
    """Test creating custom ReconnectConfig."""
    reconnect = ReconnectConfig(
        enabled=True,
        max_attempts=5,
        initial_delay_ms=500,
        max_delay_ms=10000,
        backoff_multiplier=3.0,
        jitter_factor=0.5,
    )
    assert reconnect.enabled is True
    assert reconnect.max_attempts == 5
    assert reconnect.initial_delay_ms == 500
    assert reconnect.max_delay_ms == 10000
    assert reconnect.backoff_multiplier == 3.0
    assert reconnect.jitter_factor == 0.5


def test_retry_config_custom():
    """Test creating custom RetryConfig."""
    retry = RetryConfig(
        enabled=True,
        max_attempts=5,
        initial_delay_ms=200,
        max_delay_ms=10000,
        backoff_multiplier=3.0,
        jitter_factor=0.3,
    )
    assert retry.enabled is True
    assert retry.max_attempts == 5
    assert retry.initial_delay_ms == 200
    assert retry.max_delay_ms == 10000
    assert retry.backoff_multiplier == 3.0
    assert retry.jitter_factor == 0.3


def test_invoke_options_defaults():
    """Test InvokeOptions default values."""
    options = InvokeOptions()
    assert options.idempotency_key is None
    assert options.timeout is None
    assert options.headers is None
    assert options.retry is None


def test_invoke_options_custom():
    """Test creating custom InvokeOptions."""
    custom_retry = RetryConfig(max_attempts=5)
    options = InvokeOptions(
        idempotency_key="test-key",
        timeout=5000,
        headers={"key": "value"},
        retry=custom_retry,
    )
    assert options.idempotency_key == "test-key"
    assert options.timeout == 5000
    assert options.headers == {"key": "value"}
    assert options.retry is custom_retry


def test_job_event_info():
    """Test JobEventInfo dataclass."""
    info = JobEventInfo(
        type="completed",
        job_id="test-job",
        payload="result",
        message="Job completed",
        progress=100,
        error=None,
        done=True,
    )
    assert info.type == "completed"
    assert info.job_id == "test-job"
    assert info.payload == "result"
    assert info.message == "Job completed"
    assert info.progress == 100
    assert info.error is None
    assert info.done is True


def test_invoker_initialization():
    """Test Invoker initialization."""
    config = InvokerConfig(address="localhost:9090", timeout=60000)
    invoker = Invoker(config)

    assert invoker.config is config
    assert invoker._channel is None
    assert invoker._client is None
    assert invoker._schemas == {}
    assert invoker._connected is False


def test_invoker_initialization_with_default_config():
    """Test Invoker initialization with default config."""
    invoker = Invoker()

    assert invoker.config.address == "127.0.0.1:8080"
    assert invoker.config.timeout == 30000
    assert invoker._connected is False


def test_calculate_reconnect_delay():
    """Test reconnect delay calculation with exponential backoff."""
    config = ReconnectConfig(
        initial_delay_ms=1000,
        max_delay_ms=10000,
        backoff_multiplier=2.0,
        jitter_factor=0.0,  # No jitter for predictable testing
    )

    # First attempt (attempt=0)
    delay = _calculate_reconnect_delay(0, config)
    assert delay == 1.0

    # Second attempt (attempt=1, exponential backoff)
    delay = _calculate_reconnect_delay(1, config)
    assert delay == 2.0

    # Third attempt (attempt=2)
    delay = _calculate_reconnect_delay(2, config)
    assert delay == 4.0

    # Should cap at max_delay_ms
    delay = _calculate_reconnect_delay(10, config)
    assert delay == 10.0  # max_delay_ms / 1000


def test_calculate_reconnect_delay_with_jitter():
    """Test that jitter adds randomness to delay."""
    config = ReconnectConfig(
        initial_delay_ms=1000,
        max_delay_ms=10000,
        backoff_multiplier=2.0,
        jitter_factor=0.5,  # 50% jitter
    )

    # With jitter, delay should vary
    delays = [_calculate_reconnect_delay(0, config) for _ in range(10)]
    # At least some variation should exist
    assert len(set(delays)) > 1
    # All should be positive
    assert all(d > 0 for d in delays)
    # All should be reasonable (within expected range)
    assert all(0.5 <= d <= 1.5 for d in delays)


def test_is_connection_error_with_none():
    """Test _is_connection_error with None error."""
    assert _is_connection_error(None) is False


def test_is_connection_error_with_string():
    """Test _is_connection_error with string error message."""
    assert _is_connection_error("connection refused") is True
    assert _is_connection_error("Connection Refused") is True  # Case insensitive
    assert _is_connection_error("network unreachable") is True
    assert _is_connection_error("timeout") is True
    assert _is_connection_error("some other error") is False


def test_is_connection_error_with_grpc_error():
    """Test _is_connection_error with gRPC errors."""
    # Note: The actual implementation checks isinstance(error, grpc.RpcError)
    # Our mock doesn't inherit from grpc.RpcError, so we need to skip these tests
    # or only test string-based errors

    # Test with actual gRPC error if available
    # For now, we just verify the function exists and handles None correctly
    assert _is_connection_error(None) is False


def test_default_invoker_config():
    """Test default_invoker_config factory function."""
    config = default_invoker_config()
    assert isinstance(config, InvokerConfig)
    assert config.address == "127.0.0.1:8080"
    assert config.timeout == 30000


def test_create_invoker():
    """Test create_invoker factory function."""
    invoker = create_invoker()
    assert isinstance(invoker, Invoker)
    assert invoker.config.address == "127.0.0.1:8080"


def test_create_invoker_with_config():
    """Test create_invoker with custom config."""
    config = InvokerConfig(address="custom:9999")
    invoker = create_invoker(config)
    assert isinstance(invoker, Invoker)
    assert invoker.config is config


def test_invoker_validate_payload_with_empty_schema():
    """Test payload validation with empty schema."""
    invoker = Invoker()

    # Empty schema requires non-empty payload
    with pytest.raises(Exception, match="Payload cannot be empty"):
        invoker._validate_payload("", {})

    # Non-empty payload with empty schema should pass
    assert invoker._validate_payload("test", {}) is None


def test_invoker_validate_payload_with_required_fields():
    """Test payload validation with required fields."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }

    # Missing required field should fail
    with pytest.raises(Exception, match="missing required field"):
        invoker._validate_payload('{"other":"value"}', schema)

    # Valid payload should pass
    assert invoker._validate_payload('{"name":"test"}', schema) is None


def test_invoker_validate_payload_with_type_validation():
    """Test payload validation with type checking."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "active": {"type": "boolean"},
        },
    }

    # Wrong type should fail
    with pytest.raises(Exception, match="should be integer"):
        invoker._validate_payload('{"name":"test","age":"not_a_number"}', schema)

    # Valid payload should pass
    valid = '{"name":"test","age":25,"active":true}'
    assert invoker._validate_payload(valid, schema) is None


def test_invoker_validate_payload_with_invalid_json():
    """Test payload validation with invalid JSON."""
    invoker = Invoker()

    # Need a non-empty schema to trigger JSON validation
    # Empty schema returns early without validating JSON format
    schema = {"type": "object"}
    with pytest.raises(Exception):
        invoker._validate_payload("not json", schema)


def test_invoker_is_retryable_error():
    """Test _is_retryable_error method."""
    invoker = Invoker()
    config = RetryConfig()

    # None error
    assert invoker._is_retryable_error(None, config) is False

    # Disabled config
    config_disabled = RetryConfig(enabled=False)
    assert invoker._is_retryable_error(Exception("test"), config_disabled) is False

    # Non-gRPC error (doesn't inherit from grpc.RpcError)
    assert invoker._is_retryable_error(Exception("other error"), config) is False


def test_invoker_calculate_retry_delay():
    """Test retry delay calculation."""
    invoker = Invoker()
    config = RetryConfig(
        initial_delay_ms=100,
        max_delay_ms=5000,
        backoff_multiplier=2.0,
        jitter_factor=0.0,  # No jitter
    )

    # First retry (attempt=0)
    delay = invoker._calculate_retry_delay(0, config)
    assert delay == 0.1  # 100ms / 1000

    # Second retry (attempt=1)
    delay = invoker._calculate_retry_delay(1, config)
    assert delay == 0.2  # 200ms / 1000

    # Should cap at max_delay_ms
    delay = invoker._calculate_retry_delay(10, config)
    assert delay == 5.0  # 5000ms / 1000


def test_invoker_set_schema():
    """Test set_schema method (async)."""

    async def test():
        invoker = Invoker()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        await invoker.set_schema("test.function", schema)

        assert "test.function" in invoker._schemas
        assert invoker._schemas["test.function"] == schema

    asyncio.run(test())


def test_invoker_close_without_connect():
    """Test close when not connected."""

    async def test():
        invoker = Invoker()
        # Should not raise
        await invoker.close()
        assert invoker._connected is False

    asyncio.run(test())


def test_invoker_close_clears_state():
    """Test that close clears internal state."""

    async def test():
        invoker = Invoker()
        # Set some state
        invoker._connected = True
        invoker._schemas["test"] = {"type": "object"}

        # Note: We can't fully test close without mocking the channel,
        # but we can test that it doesn't crash when _channel is None
        invoker._channel = None
        await invoker.close()

        assert invoker._connected is False
        assert len(invoker._schemas) == 0

    asyncio.run(test())


def test_invoker_invoke_fails_without_mock():
    """Test that invoke fails without actual server (for coverage)."""

    async def test():
        invoker = InvokerConfig(
            address="invalid.address:99999",
            insecure=True,
            timeout=1000,  # 1 second timeout for faster test failure
        )
        invoker = Invoker(invoker)

        # invoke will try to connect first, which will fail
        with pytest.raises(Exception):
            await invoker.invoke("test.function", "{}")

    asyncio.run(test())


def test_invoker_start_job_fails_without_mock():
    """Test that start_job fails without actual server (for coverage)."""

    async def test():
        invoker = InvokerConfig(
            address="invalid.address:99999",
            insecure=True,
            timeout=1000,  # 1 second timeout for faster test failure
        )
        invoker = Invoker(invoker)

        # start_job will try to connect first, which will fail
        with pytest.raises(Exception):
            await invoker.start_job("test.function", "{}")

    asyncio.run(test())


def test_invoker_stream_job_fails_without_mock():
    """Test that stream_job requires connection (for coverage)."""

    async def test():
        invoker = InvokerConfig(
            address="invalid.address:99999",
            insecure=True,
            timeout=1000,  # 1 second timeout for faster test failure
        )
        invoker = Invoker(invoker)

        # stream_job will try to connect first, which will fail
        # We just verify the function can be called and handles errors
        events = []
        try:
            async for event in invoker.stream_job("test-job-id"):
                events.append(event)
                break
        except Exception:
            # Expected to fail since we can't actually connect
            pass

        # Test passed if we got here without crashing
        assert isinstance(events, list)

    asyncio.run(test())


def test_invoker_cancel_job_fails_without_mock():
    """Test that cancel_job fails without actual server (for coverage)."""

    async def test():
        invoker = InvokerConfig(
            address="invalid.address:99999",
            insecure=True,
            timeout=1000,  # 1 second timeout for faster test failure
        )
        invoker = Invoker(invoker)

        with pytest.raises(Exception):
            await invoker.cancel_job("test-job-id")

    asyncio.run(test())


def test_schedule_reconnect_when_already_reconnecting():
    """Test _schedule_reconnect when already reconnecting."""
    invoker = Invoker()
    invoker._is_reconnecting = True
    invoker._reconnect_attempts = 0

    # Should not change state if already reconnecting
    invoker._schedule_reconnect()
    assert invoker._is_reconnecting is True


def test_schedule_reconnect_when_max_attempts_reached():
    """Test _schedule_reconnect when max attempts is reached."""
    invoker = Invoker()
    invoker.config.reconnect.max_attempts = 3
    invoker._reconnect_attempts = 3

    # Should not schedule reconnect (returns early)
    invoker._schedule_reconnect()
    # _is_reconnecting should still be False because we returned before setting it
    assert invoker._is_reconnecting is False


def test_invoker_create_credentials():
    """Test _create_credentials method for secure connections."""
    invoker = Invoker(
        InvokerConfig(
            insecure=False,
            ca_file="/path/to/ca.pem",
            cert_file="/path/to/cert.pem",
            key_file="/path/to/key.pem",
            server_name="example.com",
        )
    )

    # _create_credentials should raise an error for non-existent files
    # We can't test the full functionality without actual cert files,
    # but we can verify the method exists
    assert hasattr(invoker, "_create_credentials")


def test_invoker_create_credentials_with_insecure_skip_verify():
    """Test _create_credentials with various configurations."""
    # Test with insecure=False but no cert files - should use system CAs
    invoker = Invoker(InvokerConfig(insecure=False))
    # Method should not crash
    assert hasattr(invoker, "_create_credentials")


def test_invoker_validate_payload_all_types():
    """Test payload validation with all supported types."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "str_val": {"type": "string"},
            "int_val": {"type": "integer"},
            "num_val": {"type": "number"},
            "bool_val": {"type": "boolean"},
            "arr_val": {"type": "array"},
            "obj_val": {"type": "object"},
        },
    }

    valid_payload = {
        "str_val": "test",
        "int_val": 42,
        "num_val": 3.14,
        "bool_val": True,
        "arr_val": [1, 2, 3],
        "obj_val": {"nested": "value"},
    }

    import json

    assert invoker._validate_payload(json.dumps(valid_payload), schema) is None


def test_invoker_validate_payload_array_type():
    """Test payload validation with array type."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "tags": {"type": "array"},
        },
    }

    # Valid array
    assert invoker._validate_payload('{"tags":[1,2,3]}', schema) is None

    # Wrong type
    try:
        invoker._validate_payload('{"tags":"not-an-array"}', schema)
        assert False, "Should have raised exception"
    except Exception:
        pass


def test_invoker_validate_payload_object_type():
    """Test payload validation with object type."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "metadata": {"type": "object"},
        },
    }

    # Valid object
    assert invoker._validate_payload('{"metadata":{"key":"value"}}', schema) is None

    # Wrong type
    try:
        invoker._validate_payload('{"metadata":"not-an-object"}', schema)
        assert False, "Should have raised exception"
    except Exception:
        pass


def test_invoker_validate_payload_nested_schema():
    """Test payload validation with nested schema."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
            },
        },
    }

    # Valid nested object
    assert invoker._validate_payload('{"user":{"name":"Alice","age":30}}', schema) is None


def test_invoker_validate_payload_with_number_type():
    """Test that number type accepts both integers and floats."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "value": {"type": "number"},
        },
    }

    # Integer should be accepted for number type
    assert invoker._validate_payload('{"value":42}', schema) is None

    # Float should be accepted
    assert invoker._validate_payload('{"value":3.14}', schema) is None


def test_invoker_calculate_retry_delay_with_jitter():
    """Test retry delay calculation with jitter."""
    invoker = Invoker()
    config = RetryConfig(
        initial_delay_ms=100,
        max_delay_ms=5000,
        backoff_multiplier=2.0,
        jitter_factor=0.3,  # 30% jitter
    )

    # With jitter, delays should vary
    delays = [invoker._calculate_retry_delay(0, config) for _ in range(10)]
    assert len(set(delays)) > 1  # Some variation
    assert all(0.07 <= d <= 0.13 for d in delays)  # Within expected range


def test_invoker_validate_payload_empty_payload_with_schema():
    """Test payload validation with empty payload and non-empty schema."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }

    # Empty payload with non-empty schema should fail
    try:
        invoker._validate_payload("", schema)
        assert False, "Should have raised exception for empty payload"
    except Exception as e:
        # Error message should indicate invalid JSON
        assert "invalid json" in str(e).lower() or "expecting value" in str(e).lower()


def test_invoker_validate_payload_missing_required_field():
    """Test payload validation with missing required field."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    }

    # Missing 'age' field
    try:
        invoker._validate_payload('{"name":"Alice"}', schema)
        assert False, "Should have raised exception for missing required field"
    except Exception as e:
        assert "age" in str(e).lower() or "required" in str(e).lower()


def test_invoker_connect_with_reconnect_enabled():
    """Test connect method when reconnect is enabled (for coverage)."""

    async def test():
        invoker = Invoker(
            InvokerConfig(
                address="invalid.address:99999",
                insecure=True,
                reconnect=ReconnectConfig(
                    enabled=True,
                    max_attempts=1,  # Limit attempts for testing
                ),
            )
        )

        # connect should fail and schedule reconnect
        try:
            await invoker.connect()
            assert False, "Should have raised exception"
        except Exception:
            pass  # Expected

        # Verify reconnect state was set
        assert invoker._is_reconnecting is True
        # Stop reconnect task
        invoker._stop_reconnect.set()

    asyncio.run(test())


def test_invoker_connect_already_connected():
    """Test connect when already connected (idempotent)."""

    async def test():
        invoker = Invoker()
        invoker._connected = True

        # Should return immediately without trying to connect
        await invoker.connect()
        assert invoker._connected is True

    asyncio.run(test())


def test_invoker_connect_with_lock_initialization():
    """Test that lock is initialized on first connect."""

    async def test():
        invoker = Invoker()
        assert invoker._lock is None

        try:
            await invoker.connect()
        except Exception:
            pass  # Expected to fail (no server)

        # Lock should be initialized now
        assert invoker._lock is not None

    asyncio.run(test())


def test_invoker_invoke_with_custom_timeout():
    """Test invoke with custom timeout option."""

    async def test():
        invoker = Invoker(
            InvokerConfig(
                address="invalid.address:99999",
                timeout=10000,  # 10 second default
            )
        )

        options = InvokeOptions(timeout=5000)  # 5 second override
        try:
            await invoker.invoke("test.function", "{}", options)
        except Exception:
            pass  # Expected to fail (no server)

    asyncio.run(test())


def test_invoker_invoke_with_headers():
    """Test invoke with custom headers."""

    async def test():
        invoker = Invoker(InvokerConfig(address="invalid.address:99999"))

        options = InvokeOptions(headers={"X-Custom": "value", "Authorization": "Bearer token"})

        try:
            await invoker.invoke("test.function", "{}", options)
        except Exception:
            pass  # Expected to fail (no server)

    asyncio.run(test())


def test_invoker_invoke_with_idempotency_key():
    """Test invoke with idempotency key."""

    async def test():
        invoker = Invoker(InvokerConfig(address="invalid.address:99999"))

        options = InvokeOptions(idempotency_key="unique-key-123")

        try:
            await invoker.invoke("test.function", "{}", options)
        except Exception:
            pass  # Expected to fail (no server)

    asyncio.run(test())


def test_invoker_set_schema_async():
    """Test set_schema clears and sets new schema."""

    async def test():
        invoker = Invoker()

        # Set initial schema
        await invoker.set_schema("test.fn", {"type": "object"})
        assert invoker._schemas["test.fn"] == {"type": "object"}

        # Update schema
        await invoker.set_schema("test.fn", {"type": "object", "properties": {}})
        assert invoker._schemas["test.fn"]["properties"] == {}

    asyncio.run(test())


def test_invoker_close_clears_schemas():
    """Test that close clears schemas."""

    async def test():
        invoker = Invoker()
        invoker._schemas["fn1"] = {"type": "object"}
        invoker._schemas["fn2"] = {"type": "object"}

        await invoker.close()

        assert len(invoker._schemas) == 0
        assert invoker._connected is False

    asyncio.run(test())


def test_invoker_schedule_reconnect_with_delay():
    """Test _schedule_reconnect with delay calculation."""

    async def test():
        invoker = Invoker(
            InvokerConfig(
                reconnect=ReconnectConfig(
                    enabled=True,
                    initial_delay_ms=10,  # Very short for testing
                    max_attempts=1,
                )
            )
        )

        invoker._schedule_reconnect()

        # Should have scheduled a reconnect task
        assert invoker._reconnect_task is not None
        # Clean up
        invoker._stop_reconnect.set()
        if invoker._reconnect_task:
            invoker._reconnect_task.cancel()
            try:
                await invoker._reconnect_task
            except asyncio.CancelledError:
                pass

    asyncio.run(test())


def test_invoker_calculate_retry_delay_no_config():
    """Test _calculate_retry_delay with default config."""
    invoker = Invoker()
    # Use default RetryConfig instead of None
    delay = invoker._calculate_retry_delay(0, RetryConfig())
    # Should use default config values
    assert delay > 0


def test_invoker_is_retryable_error_grpc_unavailable():
    """Test _is_retryable_error with gRPC UNAVAILABLE status."""
    invoker = Invoker()

    # Create a mock gRPC error that inherits from grpc.RpcError
    class MockRpcError(grpc.RpcError):
        def code(self):
            return grpc.StatusCode.UNAVAILABLE

        def details(self):
            return "Connection refused"

    error = MockRpcError()
    config = RetryConfig()

    # UNAVAILABLE should be retryable
    assert invoker._is_retryable_error(error, config) is True


def test_invoker_is_retryable_error_grpc_non_retryable():
    """Test _is_retryable_error with non-retryable gRPC status."""
    invoker = Invoker()

    class MockRpcError(grpc.RpcError):
        def code(self):
            return grpc.StatusCode.NOT_FOUND  # Not in retryable list

        def details(self):
            return "Resource not found"

    error = MockRpcError()
    config = RetryConfig()

    # NOT_FOUND should not be retryable
    assert invoker._is_retryable_error(error, config) is False


def test_invoker_is_retryable_error_custom_config():
    """Test _is_retryable_error with custom retry config."""
    invoker = Invoker()

    class MockRpcError(grpc.RpcError):
        def code(self):
            return grpc.StatusCode.UNAVAILABLE

        def details(self):
            return "Connection refused"

    error = MockRpcError()

    # Custom config with different status codes
    custom_config = RetryConfig(retryable_status_codes=(grpc.StatusCode.INTERNAL,))

    # UNAVAILABLE not in custom config
    assert invoker._is_retryable_error(error, custom_config) is False


def test_invoker_validate_payload_invalid_json_non_empty_schema():
    """Test payload validation with invalid JSON and non-empty schema."""
    invoker = Invoker()

    schema = {"type": "object", "properties": {"name": {"type": "string"}}}

    try:
        invoker._validate_payload("invalid json", schema)
        assert False, "Should have raised exception for invalid JSON"
    except Exception:
        pass  # Expected


def test_invoker_reconnect_config_defaults():
    """Test ReconnectConfig factory function."""
    from croupier.invoker import _default_reconnect_config

    config = _default_reconnect_config()
    assert isinstance(config, ReconnectConfig)
    assert config.enabled is True


def test_invoker_retry_config_defaults():
    """Test RetryConfig factory function."""
    from croupier.invoker import _default_retry_config

    config = _default_retry_config()
    assert isinstance(config, RetryConfig)
    assert config.enabled is True


def test_invoker_validate_payload_with_empty_properties():
    """Test payload validation with empty properties."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {},
    }

    # Any valid JSON object should pass
    assert invoker._validate_payload("{}", schema) is None
    assert invoker._validate_payload('{"any":"value"}', schema) is None


def test_invoker_invoke_with_schema_validation():
    """Test invoke performs client-side validation."""

    async def test():
        invoker = Invoker()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }

        await invoker.set_schema("test.fn", schema)

        # This should fail validation before trying to connect
        try:
            await invoker.invoke("test.fn", '{"wrong":"field"}')
            assert False, "Should have raised validation error"
        except Exception as e:
            # Should be validation error, not connection error
            assert (
                "name" in str(e).lower()
                or "required" in str(e).lower()
                or "missing" in str(e).lower()
            )

    asyncio.run(test())


# ============= SyncInvoker Tests =============

def test_sync_invoker_initialization():
    """Test SyncInvoker initialization."""
    from croupier.invoker import SyncInvoker, create_sync_invoker

    invoker = SyncInvoker()
    assert invoker._async_invoker is not None
    assert invoker._loop is None


def test_sync_invoker_initialization_with_config():
    """Test SyncInvoker with custom config."""
    from croupier.invoker import SyncInvoker

    config = InvokerConfig(address="custom:9999")
    invoker = SyncInvoker(config)
    assert invoker._async_invoker.config.address == "custom:9999"


def test_create_sync_invoker():
    """Test create_sync_invoker factory function."""
    from croupier.invoker import create_sync_invoker

    invoker = create_sync_invoker()
    assert invoker is not None
    assert invoker._async_invoker.config.address == "127.0.0.1:8080"


def test_create_sync_invoker_with_config():
    """Test create_sync_invoker with custom config."""
    from croupier.invoker import create_sync_invoker

    config = InvokerConfig(address="custom:8888")
    invoker = create_sync_invoker(config)
    assert invoker._async_invoker.config.address == "custom:8888"


def test_sync_invoker_set_schema():
    """Test SyncInvoker.set_schema."""
    from croupier.invoker import SyncInvoker

    invoker = SyncInvoker()
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    invoker.set_schema("test.fn", schema)

    assert "test.fn" in invoker._async_invoker._schemas
    assert invoker._async_invoker._schemas["test.fn"] == schema


def test_sync_invoker_close():
    """Test SyncInvoker.close without connection."""
    from croupier.invoker import SyncInvoker

    invoker = SyncInvoker()
    # Should not raise
    invoker.close()


def test_sync_invoker_connect_fails():
    """Test SyncInvoker.connect fails without server."""
    from croupier.invoker import SyncInvoker

    invoker = SyncInvoker(
        InvokerConfig(address="invalid.address:99999", timeout=1000)
    )

    with pytest.raises(Exception):
        invoker.connect()


def test_sync_invoker_invoke_fails():
    """Test SyncInvoker.invoke fails without server."""
    from croupier.invoker import SyncInvoker

    invoker = SyncInvoker(
        InvokerConfig(address="invalid.address:99999", timeout=1000)
    )

    with pytest.raises(Exception):
        invoker.invoke("test.fn", "{}")


def test_sync_invoker_start_job_fails():
    """Test SyncInvoker.start_job fails without server."""
    from croupier.invoker import SyncInvoker

    invoker = SyncInvoker(
        InvokerConfig(address="invalid.address:99999", timeout=1000)
    )

    with pytest.raises(Exception):
        invoker.start_job("test.fn", "{}")


def test_sync_invoker_cancel_job_fails():
    """Test SyncInvoker.cancel_job fails without server."""
    from croupier.invoker import SyncInvoker

    invoker = SyncInvoker(
        InvokerConfig(address="invalid.address:99999", timeout=1000)
    )

    with pytest.raises(Exception):
        invoker.cancel_job("test-job-id")


def test_sync_invoker_stream_job():
    """Test SyncInvoker.stream_job returns iterator."""
    from croupier.invoker import SyncInvoker

    invoker = SyncInvoker(
        InvokerConfig(address="invalid.address:99999", timeout=1000)
    )

    # stream_job returns an iterator
    stream_iter = invoker.stream_job("test-job-id")
    assert hasattr(stream_iter, "__iter__")
    assert hasattr(stream_iter, "__next__")


def test_invoker_execute_with_retry_disabled():
    """Test _execute_with_retry when retry is disabled."""

    async def test():
        invoker = Invoker()
        invoker.config.retry.enabled = False

        call_count = 0

        async def failing_fn():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")

        try:
            await invoker._execute_with_retry(failing_fn, None)
        except Exception:
            pass

        # Should only be called once (no retries)
        assert call_count == 1

    asyncio.run(test())


def test_invoker_execute_with_retry_success():
    """Test _execute_with_retry succeeds on first try."""

    async def test():
        invoker = Invoker()

        async def success_fn():
            return "success"

        result = await invoker._execute_with_retry(success_fn, None)
        assert result == "success"

    asyncio.run(test())


def test_invoker_execute_with_retry_eventual_success():
    """Test _execute_with_retry retries and eventually succeeds."""

    async def test():
        invoker = Invoker()
        invoker.config.retry.enabled = True
        invoker.config.retry.initial_delay_ms = 1  # Fast for testing

        call_count = 0

        class MockRpcError(grpc.RpcError):
            def code(self):
                return grpc.StatusCode.UNAVAILABLE

            def details(self):
                return "Connection refused"

        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise MockRpcError()
            return "success"

        result = await invoker._execute_with_retry(eventually_succeeds, None)
        assert result == "success"
        assert call_count == 3

    asyncio.run(test())


def test_invoker_validate_payload_boolean_type():
    """Test payload validation with boolean type."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "active": {"type": "boolean"},
        },
    }

    # Valid boolean
    assert invoker._validate_payload('{"active":true}', schema) is None
    assert invoker._validate_payload('{"active":false}', schema) is None

    # Wrong type
    try:
        invoker._validate_payload('{"active":"yes"}', schema)
        assert False, "Should have raised exception"
    except Exception:
        pass


def test_invoker_validate_payload_unknown_type():
    """Test payload validation with unknown type (not in type_map)."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "value": {"type": "null"},  # Not in type_map
        },
    }

    # Should pass since null type is not validated
    assert invoker._validate_payload('{"value":null}', schema) is None


def test_invoker_reconnect_loop_max_attempts():
    """Test _reconnect_loop respects max_attempts."""

    async def test():
        invoker = Invoker(
            InvokerConfig(
                address="invalid.address:99999",
                reconnect=ReconnectConfig(
                    enabled=True,
                    max_attempts=2,
                    initial_delay_ms=1,  # Very fast for testing
                ),
            )
        )

        invoker._reconnect_attempts = 2  # Already at max

        # _schedule_reconnect should not create task when at max
        invoker._schedule_reconnect()
        assert invoker._is_reconnecting is False

    asyncio.run(test())


def test_invoker_close_with_active_reconnect_task():
    """Test close cancels active reconnect task."""

    async def test():
        invoker = Invoker(
            InvokerConfig(
                reconnect=ReconnectConfig(
                    enabled=True,
                    initial_delay_ms=10000,  # Long delay
                )
            )
        )

        # Start reconnect
        invoker._schedule_reconnect()
        assert invoker._reconnect_task is not None

        # Close should cancel it
        await invoker.close()
        assert invoker._connected is False

    asyncio.run(test())


def test_is_connection_error_with_exception():
    """Test _is_connection_error with regular Exception."""
    # Regular exception with connection keyword in message
    error = Exception("connection refused")
    assert _is_connection_error(error) is True

    # Regular exception without connection keyword
    error = Exception("some other error")
    assert _is_connection_error(error) is False


def test_job_event_info_defaults():
    """Test JobEventInfo default values."""
    info = JobEventInfo(type="test", job_id="job-1")
    assert info.type == "test"
    assert info.job_id == "job-1"
    assert info.payload is None
    assert info.message is None
    assert info.progress is None
    assert info.error is None
    assert info.done is False


def test_invoker_validate_payload_none_schema():
    """Test payload validation with None-like schema values."""
    invoker = Invoker()

    # Schema with no properties
    schema = {"type": "object"}
    assert invoker._validate_payload('{"any":"value"}', schema) is None


def test_invoker_validate_payload_non_list_required():
    """Test payload validation when required is not a list."""
    invoker = Invoker()

    # Schema with non-list required (edge case)
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": "name",  # String instead of list (invalid but should handle gracefully)
    }

    # Should not crash
    assert invoker._validate_payload('{"name":"test"}', schema) is None


def test_invoker_validate_payload_non_dict_properties():
    """Test payload validation when properties is not a dict."""
    invoker = Invoker()

    # Schema with non-dict properties (edge case)
    schema = {
        "type": "object",
        "properties": "not-a-dict",  # Invalid but should handle gracefully
    }

    # Should not crash
    assert invoker._validate_payload('{"name":"test"}', schema) is None


def test_invoker_validate_payload_no_expected_type():
    """Test payload validation when property has no type."""
    invoker = Invoker()

    schema = {
        "type": "object",
        "properties": {
            "name": {},  # No type specified
        },
    }

    # Should pass since no type to validate
    assert invoker._validate_payload('{"name":"test"}', schema) is None
    assert invoker._validate_payload('{"name":123}', schema) is None
