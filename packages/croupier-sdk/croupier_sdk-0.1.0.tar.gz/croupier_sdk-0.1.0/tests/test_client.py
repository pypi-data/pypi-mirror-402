import gzip
import json
import time

import croupier
import pytest


class FakeContext:
    def abort(self, code, details):  # pragma: no cover
        raise RuntimeError(f"abort({code}): {details}")


def test_register_function_validates_descriptor():
    client = croupier.CroupierClient()
    handler = lambda ctx, payload: "ok"  # noqa: E731

    with pytest.raises(ValueError):
        client.register_function(croupier.FunctionDescriptor(id="", version="1.0.0"), handler)
    with pytest.raises(ValueError):
        client.register_function(croupier.FunctionDescriptor(id="f1", version=""), handler)


def test_register_function_after_server_started():
    config = croupier.ClientConfig(service_id="test-service")
    client = croupier.CroupierClient(config)
    client.register_function(
        croupier.FunctionDescriptor(id="f1", version="1.0.0"),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    # Mock server as started
    client._server = "fake_server"  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="Cannot register new functions"):
        client.register_function(
            croupier.FunctionDescriptor(id="f2", version="1.0.0"),
            lambda ctx, payload: "ok",  # noqa: E731
        )


def test_connect_without_functions_raises_error():
    client = croupier.CroupierClient()

    with pytest.raises(RuntimeError, match="Register at least one function"):
        client.connect()


def test_connect_is_idempotent():
    config = croupier.ClientConfig(service_id="test-service")
    client = croupier.CroupierClient(config)
    client.register_function(
        croupier.FunctionDescriptor(id="f1", version="1.0.0"),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    # Mock server to prevent actual connection
    client._server = "fake_server"  # type: ignore[assignment]

    # Should not raise
    client.connect()


def test_build_manifest_contains_provider_and_functions():
    config = croupier.ClientConfig(service_id="svc-1", service_version="sv1")
    client = croupier.CroupierClient(config)
    client.register_function(
        croupier.FunctionDescriptor(id="f1", version="1.2.3", category="cat", enabled=True),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    raw = client._build_manifest()
    parsed = json.loads(raw.decode("utf-8"))
    assert parsed["provider"] == {
        "id": "svc-1",
        "version": "sv1",
        "lang": "python",
        "sdk": "croupier-python-sdk",
    }
    assert parsed["functions"][0]["id"] == "f1"
    assert parsed["functions"][0]["version"] == "1.2.3"
    assert parsed["functions"][0]["category"] == "cat"
    assert parsed["functions"][0]["enabled"] is True


def test_build_manifest_defaults_version():
    client = croupier.CroupierClient()
    # Use default version (not empty)
    client.register_function(
        croupier.FunctionDescriptor(id="f1"),  # version defaults to "1.0.0"
        lambda ctx, payload: "ok",  # noqa: E731
    )

    raw = client._build_manifest()
    parsed = json.loads(raw.decode("utf-8"))
    assert parsed["functions"][0]["version"] == "1.0.0"


def test_gzip_bytes_roundtrip():
    client = croupier.CroupierClient()
    original = b'{"hello":"world"}'
    compressed = client._gzip_bytes(original)
    assert gzip.decompress(compressed) == original


def test_start_job_streams_started_then_completed():
    client = croupier.CroupierClient()
    client.register_function(
        croupier.FunctionDescriptor(id="f1", version="1.0.0"),
        lambda ctx, payload: (time.sleep(0.05) or payload.decode("utf-8")),  # noqa: E731
    )

    req = croupier.function_pb2.InvokeRequest(function_id="f1", payload=b"hi")
    resp = client._handle_start_job(req, FakeContext())

    stream_req = croupier.function_pb2.JobStreamRequest(job_id=resp.job_id)
    events = list(client._handle_stream_job(stream_req, FakeContext()))
    assert events[0].type == "started"
    assert events[-1].type == "completed"
    assert events[-1].payload == b"hi"


def test_cancel_job_emits_cancelled_and_closes_stream():
    client = croupier.CroupierClient()
    client.register_function(
        croupier.FunctionDescriptor(id="f1", version="1.0.0"),
        lambda ctx, payload: (time.sleep(0.2) or "late"),  # noqa: E731
    )

    req = croupier.function_pb2.InvokeRequest(function_id="f1", payload=b"hi")
    resp = client._handle_start_job(req, FakeContext())

    stream_req = croupier.function_pb2.JobStreamRequest(job_id=resp.job_id)
    stream_iter = client._handle_stream_job(stream_req, FakeContext())

    first = next(stream_iter)
    assert first.type == "started"

    client._handle_cancel_job(
        croupier.function_pb2.CancelJobRequest(job_id=resp.job_id), FakeContext()
    )

    events = [first, *list(stream_iter)]
    assert any(e.type == "cancelled" for e in events)


def test_invoke_calls_registered_handler():
    client = croupier.CroupierClient()

    def handler(ctx, payload):
        return f"echo:{payload.decode('utf-8')}"

    client.register_function(
        croupier.FunctionDescriptor(id="echo", version="1.0.0"),
        handler,
    )

    req = croupier.function_pb2.InvokeRequest(function_id="echo", payload=b"test")
    resp = client._handle_invoke(req, FakeContext())

    assert resp.payload == b"echo:test"


def test_invoke_raises_for_unregistered_function():
    client = croupier.CroupierClient()

    req = croupier.function_pb2.InvokeRequest(function_id="unknown", payload=b"test")

    with pytest.raises(Exception):  # grpc context abort
        client._handle_invoke(req, FakeContext())


def test_start_job_emits_error_on_handler_failure():
    client = croupier.CroupierClient()

    def failing_handler(ctx, payload):
        raise ValueError("handler error")

    client.register_function(
        croupier.FunctionDescriptor(id="failing", version="1.0.0"),
        failing_handler,
    )

    req = croupier.function_pb2.InvokeRequest(function_id="failing", payload=b"test")
    resp = client._handle_start_job(req, FakeContext())

    stream_req = croupier.function_pb2.JobStreamRequest(job_id=resp.job_id)
    events = list(client._handle_stream_job(stream_req, FakeContext()))

    assert events[0].type == "started"
    assert events[1].type == "error"
    assert "handler error" in events[1].message


def test_stream_job_raises_for_missing_job_id():
    client = croupier.CroupierClient()

    req = croupier.function_pb2.JobStreamRequest(job_id="")
    with pytest.raises(Exception):
        list(client._handle_stream_job(req, FakeContext()))


def test_cancel_job_does_nothing_for_unknown_job():
    client = croupier.CroupierClient()

    # Should not raise
    client._handle_cancel_job(
        croupier.function_pb2.CancelJobRequest(job_id="unknown-job"), FakeContext()
    )


def test_client_config_defaults():
    config = croupier.ClientConfig()
    assert config.agent_addr == "127.0.0.1:19090"
    assert config.insecure is True
    assert config.service_version == "1.0.0"
    assert config.local_listen == "0.0.0.0:0"
    assert config.heartbeat_interval == 60
    assert config.timeout_seconds == 30
    assert config.provider_lang == "python"
    assert config.provider_sdk == "croupier-python-sdk"


def test_function_descriptor_defaults():
    desc = croupier.FunctionDescriptor(id="test.fn")
    assert desc.version == "1.0.0"
    assert desc.category is None
    assert desc.risk is None
    assert desc.entity is None
    assert desc.operation is None
    assert desc.enabled is True


def test_disconnect_clears_state():
    config = croupier.ClientConfig(service_id="test-service")
    client = croupier.CroupierClient(config)
    client.register_function(
        croupier.FunctionDescriptor(id="f1", version="1.0.0"),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    # Set some state
    client._session_id = "test-session"
    client._heartbeat_stop.set()

    # Should not raise
    client.disconnect()

    assert client._session_id == ""


def test_job_state_push_and_finished():
    state = croupier._JobState()

    event = croupier.function_pb2.JobEvent(type="test", payload=b"data")
    state.push(event, finished=False)

    result = state.queue.get(timeout=1)
    assert result.type == "test"
    assert result.payload == b"data"


def test_job_state_finished_sets_done():
    state = croupier._JobState()

    event = croupier.function_pb2.JobEvent(type="test", payload=b"data")
    state.push(event, finished=True)

    # Should mark as done
    assert state.done.is_set()


def test_ensure_parent_packages():
    # Test the helper function
    croupier._ensure_parent_packages("test.module.name")
    # Should not raise


def test_load_proto_module_caches():
    # First load
    module = croupier._load_proto_module("croupier.function.v1.function_pb2")
    # Second load should return cached
    module2 = croupier._load_proto_module("croupier.function.v1.function_pb2")
    assert module is module2


def test_load_proto_module_raises_for_missing():
    with pytest.raises(ImportError, match="Generated module"):
        croupier._load_proto_module("missing.module.name")


def test_function_descriptor_with_all_fields():
    """Test FunctionDescriptor with all fields set."""
    desc = croupier.FunctionDescriptor(
        id="test.function",
        version="2.0.0",
        category="test-category",
        risk="low",
        entity="player",
        operation="read",
        enabled=False,
    )

    assert desc.id == "test.function"
    assert desc.version == "2.0.0"
    assert desc.category == "test-category"
    assert desc.risk == "low"
    assert desc.entity == "player"
    assert desc.operation == "read"
    assert desc.enabled is False


def test_client_config_with_all_fields():
    """Test ClientConfig with custom values."""
    config = croupier.ClientConfig(
        agent_addr="custom.agent:19090",
        insecure=False,
        service_id="my-service",
        service_version="2.0.0",
        local_listen="127.0.0.1:8080",
        heartbeat_interval=30,
        timeout_seconds=60,
        cert_file="/path/to/cert.pem",
        key_file="/path/to/key.pem",
        ca_file="/path/to/ca.pem",
        control_addr="control.example.com:19091",
        provider_lang="python",
        provider_sdk="custom-sdk",
    )

    assert config.agent_addr == "custom.agent:19090"
    assert config.insecure is False
    assert config.service_id == "my-service"
    assert config.service_version == "2.0.0"
    assert config.local_listen == "127.0.0.1:8080"
    assert config.heartbeat_interval == 30
    assert config.timeout_seconds == 60
    assert config.cert_file == "/path/to/cert.pem"
    assert config.key_file == "/path/to/key.pem"
    assert config.ca_file == "/path/to/ca.pem"
    assert config.control_addr == "control.example.com:19091"
    assert config.provider_lang == "python"
    assert config.provider_sdk == "custom-sdk"


def test_function_service_delegates_to_client():
    """Test that _FunctionService methods delegate to client methods."""
    client = croupier.CroupierClient()
    service = croupier._FunctionService(client)

    # Verify that the service has a reference to the client
    assert service._client is client


def test_job_state_push_with_finished():
    """Test _JobState.push with finished=True sets done event."""
    state = croupier._JobState()

    event = croupier.function_pb2.JobEvent(type="test", payload=b"data")
    state.push(event, finished=True)

    # Should mark as done
    assert state.done.is_set()

    # Queue should have event and None terminator
    first = state.queue.get(timeout=1)
    assert first.type == "test"

    second = state.queue.get(timeout=1)
    assert second is None


def test_job_state_multiple_push():
    """Test _JobState with multiple pushes."""
    state = croupier._JobState()

    event1 = croupier.function_pb2.JobEvent(type="progress", payload=b"50")
    event2 = croupier.function_pb2.JobEvent(type="progress", payload=b"100")

    state.push(event1, finished=False)
    state.push(event2, finished=False)

    assert state.queue.qsize() == 2
    assert not state.done.is_set()

    state.push(croupier.function_pb2.JobEvent(type="done"), finished=True)
    assert state.done.is_set()


def test_client_has_initial_state():
    """Test that CroupierClient initializes with correct default state."""
    client = croupier.CroupierClient()

    assert client._handlers == {}
    assert client._descriptors == {}
    assert client._jobs == {}
    assert client._server is None
    assert client._channel is None
    assert client._agent_stub is None
    assert client._local_address == ""
    assert client._session_id == ""


def test_client_with_custom_config():
    """Test CroupierClient with custom config."""
    config = croupier.ClientConfig(service_id="test-service")
    client = croupier.CroupierClient(config)

    assert client._config is config
    assert client._config.service_id == "test-service"


def test_protobuf_modules_are_loaded():
    """Test that protobuf modules are loaded correctly."""
    # These should be available without errors
    assert hasattr(croupier, "function_pb2")
    assert hasattr(croupier, "function_pb2_grpc")
    assert hasattr(croupier, "local_pb2")
    assert hasattr(croupier, "local_pb2_grpc")
    assert hasattr(croupier, "control_pb2")
    assert hasattr(croupier, "control_pb2_grpc")


def test_function_handler_type():
    """Test that FunctionHandler is a callable type."""
    assert callable(croupier.FunctionHandler)
    # It should be a type annotation (Callable)
    import typing

    assert croupier.FunctionHandler == typing.Callable[[str, bytes], str]


def test_create_control_channel_insecure():
    """Test _create_control_channel with insecure config."""
    config = croupier.ClientConfig(
        service_id="test-service",
        control_addr="127.0.0.1:19091",
        insecure=True,
    )
    client = croupier.CroupierClient(config)

    channel = client._create_control_channel()
    assert channel is not None
    # Insecure channel should be created
    channel.close()


def test_create_control_channel_secure():
    """Test _create_control_channel with secure config."""
    config = croupier.ClientConfig(
        service_id="test-service",
        control_addr="127.0.0.1:19091",
        insecure=False,
    )
    client = croupier.CroupierClient(config)

    channel = client._create_control_channel()
    assert channel is not None
    # Secure channel should be created
    channel.close()


def test_build_manifest_with_all_descriptor_fields():
    """Test _build_manifest includes all descriptor fields."""
    config = croupier.ClientConfig(service_id="svc-1", service_version="sv1")
    client = croupier.CroupierClient(config)

    client.register_function(
        croupier.FunctionDescriptor(
            id="full.fn",
            version="2.0.0",
            category="cat",
            risk="low",
            entity="player",
            operation="read",
            enabled=True,
        ),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    raw = client._build_manifest()
    parsed = json.loads(raw.decode("utf-8"))

    fn = parsed["functions"][0]
    assert fn["id"] == "full.fn"
    assert fn["version"] == "2.0.0"
    assert fn["category"] == "cat"
    assert fn["risk"] == "low"
    assert fn["entity"] == "player"
    assert fn["operation"] == "read"
    assert fn["enabled"] is True


def test_build_manifest_with_minimal_descriptor():
    """Test _build_manifest with minimal descriptor fields."""
    client = croupier.CroupierClient()

    client.register_function(
        croupier.FunctionDescriptor(id="min.fn"),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    raw = client._build_manifest()
    parsed = json.loads(raw.decode("utf-8"))

    fn = parsed["functions"][0]
    assert fn["id"] == "min.fn"
    assert fn["version"] == "1.0.0"
    # Optional fields should not be present
    assert "category" not in fn
    assert "risk" not in fn
    assert "entity" not in fn
    assert "operation" not in fn


def test_build_manifest_with_empty_functions():
    """Test _build_manifest when no functions are registered."""
    client = croupier.CroupierClient()

    raw = client._build_manifest()
    parsed = json.loads(raw.decode("utf-8"))

    # Should only have provider, no functions
    assert "provider" in parsed
    assert "functions" not in parsed


def test_register_capabilities_without_control_addr():
    """Test _register_capabilities when control_addr is not set."""
    config = croupier.ClientConfig(service_id="test-service", control_addr=None)
    client = croupier.CroupierClient(config)
    client.register_function(
        croupier.FunctionDescriptor(id="f1", version="1.0.0"),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    # Should return early without error
    client._register_capabilities()


def test_ensure_parent_packages_creates_hierarchy():
    """Test _ensure_parent_packages creates parent module hierarchy."""
    # Clear any cached modules
    import sys

    test_module = "test._ensure_parent_module"
    for part in ["test", test_module]:
        if part in sys.modules:
            del sys.modules[part]

    croupier._ensure_parent_packages(test_module)
    # Should create parent module
    assert "test" in sys.modules
    # Clean up
    del sys.modules["test"]


def test_invoke_handler_returns_bytes():
    """Test invoke when handler returns bytes."""
    client = croupier.CroupierClient()

    def handler(ctx, payload):
        return b"binary response"

    client.register_function(
        croupier.FunctionDescriptor(id="bytes.fn", version="1.0.0"),
        handler,
    )

    req = croupier.function_pb2.InvokeRequest(function_id="bytes.fn", payload=b"test")
    resp = client._handle_invoke(req, FakeContext())

    assert resp.payload == b"binary response"


def test_invoke_handler_with_metadata():
    """Test invoke passes metadata to handler."""
    client = croupier.CroupierClient()
    received_ctx = None

    def handler(ctx, payload):
        nonlocal received_ctx
        received_ctx = ctx
        return "ok"

    client.register_function(
        croupier.FunctionDescriptor(id="meta.fn", version="1.0.0"),
        handler,
    )

    req = croupier.function_pb2.InvokeRequest(
        function_id="meta.fn", payload=b"test", metadata={"key": "value"}
    )
    client._handle_invoke(req, FakeContext())

    assert received_ctx is not None
    parsed = json.loads(received_ctx)
    assert parsed.get("key") == "value"


def test_invoke_handler_with_empty_payload():
    """Test invoke with None/empty payload."""
    client = croupier.CroupierClient()

    def handler(ctx, payload):
        return f"received:{len(payload)}"

    client.register_function(
        croupier.FunctionDescriptor(id="empty.fn", version="1.0.0"),
        handler,
    )

    req = croupier.function_pb2.InvokeRequest(function_id="empty.fn")
    resp = client._handle_invoke(req, FakeContext())

    assert resp.payload == b"received:0"


def test_start_job_for_unknown_function():
    """Test start_job returns error for unknown function."""
    client = croupier.CroupierClient()

    req = croupier.function_pb2.InvokeRequest(function_id="unknown.fn", payload=b"test")

    with pytest.raises(Exception):
        client._handle_start_job(req, FakeContext())


def test_build_manifest_with_disabled_function():
    """Test _build_manifest includes disabled functions correctly."""
    config = croupier.ClientConfig(service_id="svc-1", service_version="sv1")
    client = croupier.CroupierClient(config)

    # Note: enabled=False means the function is disabled
    # But the manifest still includes it with enabled=True (if enabled field is present)
    client.register_function(
        croupier.FunctionDescriptor(
            id="disabled.fn",
            version="1.0.0",
            category="cat",
            enabled=False,  # Disabled
        ),
        lambda ctx, payload: "ok",  # noqa: E731
    )

    raw = client._build_manifest()
    parsed = json.loads(raw.decode("utf-8"))

    # Verify the function is in the manifest
    fn = parsed["functions"][0]
    assert fn["id"] == "disabled.fn"
    # enabled=False means it won't add the enabled key (only adds when True)
    assert "enabled" not in fn


def test_module_version_info():
    """Test module version information."""
    assert hasattr(croupier, "__version__")
    assert hasattr(croupier, "__author__")
    assert hasattr(croupier, "__email__")
    assert croupier.__version__ == "1.0.0"


def test_module_exports():
    """Test module __all__ exports."""
    # These should all be importable
    from croupier import (
        ClientConfig,
        FunctionDescriptor,
        FunctionHandler,
        CroupierClient,
    )

    assert ClientConfig is not None
    assert FunctionDescriptor is not None
    assert FunctionHandler is not None
    assert CroupierClient is not None


def test_invoker_imports_from_module():
    """Test that invoker classes can be imported from main module."""
    from croupier import (
        InvokerConfig,
        InvokeOptions,
        JobEventInfo,
        Invoker,
        SyncInvoker,
        create_invoker,
        create_sync_invoker,
    )

    assert InvokerConfig is not None
    assert InvokeOptions is not None
    assert JobEventInfo is not None
    assert Invoker is not None
    assert SyncInvoker is not None
    assert create_invoker is not None
    assert create_sync_invoker is not None


def test_function_service_invoke_delegates():
    """Test that _FunctionService.Invoke delegates to client._handle_invoke."""
    client = croupier.CroupierClient()
    client.register_function(
        croupier.FunctionDescriptor(id="test.fn", version="1.0.0"),
        lambda ctx, payload: "delegated",  # noqa: E731
    )

    service = croupier._FunctionService(client)
    req = croupier.function_pb2.InvokeRequest(function_id="test.fn", payload=b"test")

    resp = service.Invoke(req, FakeContext())
    assert resp.payload == b"delegated"


def test_function_service_start_job_delegates():
    """Test that _FunctionService.StartJob delegates to client._handle_start_job."""
    client = croupier.CroupierClient()
    client.register_function(
        croupier.FunctionDescriptor(id="job.fn", version="1.0.0"),
        lambda ctx, payload: "result",  # noqa: E731
    )

    service = croupier._FunctionService(client)
    req = croupier.function_pb2.InvokeRequest(function_id="job.fn", payload=b"test")

    resp = service.StartJob(req, FakeContext())
    assert resp.job_id is not None
    assert "job.fn" in resp.job_id


def test_function_service_cancel_job_delegates():
    """Test that _FunctionService.CancelJob delegates to client._handle_cancel_job."""
    client = croupier.CroupierClient()
    service = croupier._FunctionService(client)

    req = croupier.function_pb2.CancelJobRequest(job_id="unknown-job")

    # Should not raise even for unknown job
    resp = service.CancelJob(req, FakeContext())
    assert resp.job_id == "unknown-job"


def test_load_proto_module_with_spec_none():
    """Test _load_proto_module when spec is None."""
    # This is hard to test directly, but we can verify the function handles it
    # by trying to load a module that doesn't exist
    with pytest.raises(ImportError, match="Generated module"):
        croupier._load_proto_module("nonexistent.module.path")
