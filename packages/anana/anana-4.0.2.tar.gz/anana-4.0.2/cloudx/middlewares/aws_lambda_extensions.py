"""Post-invocation async sidecar for AWS Lambda deployments of cloudx."""

from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Optional, Tuple
from urllib import request as urllib_request

from ..utils.logger import logger

# ---------------------------------------------------------------------------
# Public constants / configuration knobs
# ---------------------------------------------------------------------------
# Extension name for registration
# Note: AWS docs say this must be the "full file name" for external extensions,
# but for internal extensions (threads), we use a descriptive name.
# If registration fails with 403, it likely means internal extensions registered
# from Python code aren't supported in production AWS Lambda.
LAMBDA_EXTENSION_NAME = "cloudx_async_extension"
HTTP_LISTEN_HOST = "0.0.0.0"
HTTP_LISTEN_PORT = 2772  # Common port used by AWS docs / samples
# Internal extensions can only register for INVOKE events, not SHUTDOWN
# Per AWS docs: "Internal extensions are started and stopped by the runtime process,
# so they are not permitted to register for the Shutdown event."
SUPPORTED_EVENTS: Tuple[str, ...] = ("INVOKE",)  # Internal extension - INVOKE only
SCHEMA_VERSION = "2020-08-15"
DEST_HOST = "sandbox"  # Resolves to 127.0.0.1 inside the Lambda sandbox
# Soft deadline buffer (seconds) for post-invoke work before yielding back to runtime
SOFT_DEADLINE_BUFFER = 0.9

# ---------------------------------------------------------------------------
# Internal types and state
# ---------------------------------------------------------------------------
AsyncTask = Tuple[Optional[Callable[[Any], None]], Any]
_TaskBuckets = MutableMapping[str, List[AsyncTask]]

_tasks_by_request_id: _TaskBuckets = {}
_tasks_lock = threading.Lock()
_extension_active = False
_stop_signal = threading.Event()
_http_server: Optional[ThreadingHTTPServer] = None
_start_lock = threading.Lock()  # ensures idempotent start
# Signal events for each request_id - signaled when teardowns are queued
_teardown_signals: Dict[str, threading.Event] = {}
_signals_lock = threading.Lock()
# Signal events for each request_id - signaled when teardowns are queued
_teardown_signals: Dict[str, threading.Event] = {}
_signals_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def _http(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> Tuple[int, Dict[str, str], bytes]:
    """Perform an HTTP call tailored for the Lambda Runtime/Logs APIs.

    Parameters
    ----------
    method: HTTP verb to issue (``"GET"``, ``"POST"``, ``"PUT"``).
    url: Fully qualified runtime endpoint URL.
    headers: Optional request headers.
    payload: Optional JSON-serialisable body that will be encoded as UTF-8.
    timeout: Optional socket timeout forwarded to ``urllib``.

    Returns
    -------
    status, headers, body: Tuple containing the status code, response headers, and raw body.
    """

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib_request.Request(url=url, data=data, headers=headers or {}, method=method)
    with urllib_request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), dict(resp.headers.items()), resp.read()


def _ensure_runtime_api() -> str:
    """Return the Lambda runtime endpoint or raise if the code is not executing in Lambda."""
    api = os.environ.get("AWS_LAMBDA_RUNTIME_API")
    if not api:
        raise EnvironmentError("AWS_LAMBDA_RUNTIME_API is not set")
    return api


# ---------------------------------------------------------------------------
# Extension registration / subscription
# ---------------------------------------------------------------------------
def _register_extension(retry_count: int = 2, initial_delay: float = 0.01) -> str:
    """Register the sidecar with the runtime API and return the extension identifier.
    
    Tries immediate registration first (no delay - best performance), then retries
    with minimal delays only if needed. Uses exponential backoff with very small delays
    to avoid performance impact.
    
    Args:
        retry_count: Number of retry attempts after initial try (default: 2)
        initial_delay: Initial delay in seconds before first retry (default: 0.01 = 10ms)
    
    Returns:
        Extension identifier string
        
    Raises:
        RuntimeError: If all registration attempts fail
    """
    api = _ensure_runtime_api()
    last_error = None
    
    # Try immediate registration first (no delay - best performance)
    try:
        status, headers, _ = _http(
            "POST",
            f"http://{api}/2020-01-01/extension/register",
            headers={"Lambda-Extension-Name": LAMBDA_EXTENSION_NAME, "Content-Type": "application/json"},
            payload={"events": list(SUPPORTED_EVENTS)},
            timeout=5,
        )
        if status < 400:
            ext_id = headers.get("Lambda-Extension-Identifier")
            if ext_id:
                return ext_id
            raise RuntimeError("Missing Lambda-Extension-Identifier header")
        last_error = RuntimeError(f"Extension registration failed with status {status}")
    except Exception as exc:
        last_error = exc
    
    # Only retry if immediate registration failed (with minimal delays)
    # These delays only occur on failure, so they don't impact successful registrations
    for attempt in range(retry_count):
        delay = initial_delay * (2 ** attempt)  # Exponential backoff
        time.sleep(delay)
        
        try:
            status, headers, _ = _http(
                "POST",
                f"http://{api}/2020-01-01/extension/register",
                headers={"Lambda-Extension-Name": LAMBDA_EXTENSION_NAME, "Content-Type": "application/json"},
                payload={"events": list(SUPPORTED_EVENTS)},
                timeout=5,
            )
            if status < 400:
                ext_id = headers.get("Lambda-Extension-Identifier")
                if ext_id:
                    logger.debug(f"Extension registered successfully on retry attempt {attempt + 1}")
                    return ext_id
                raise RuntimeError("Missing Lambda-Extension-Identifier header")
            last_error = RuntimeError(f"Extension registration failed with status {status}")
        except Exception as exc:
            last_error = exc
    
    # All attempts failed
    raise last_error or RuntimeError("Extension registration failed after all retry attempts")


def _subscribe_telemetry(ext_id: str) -> None:
    """Subscribe the extension to runtimeDone telemetry for the provided identifier."""
    api = _ensure_runtime_api()
    dest_uri = f"http://{DEST_HOST}:{HTTP_LISTEN_PORT}/logs"
    body = {
        "schemaVersion": SCHEMA_VERSION,
        "destination": {"protocol": "HTTP", "URI": dest_uri},
        "types": ["platform"],
        "buffering": {"maxItems": 256, "maxBytes": 131072, "timeoutMs": 250},
        "filter": {"filterPattern": "{ $.type = \"platform.runtimeDone\" }"},
    }
    _http(
        "PUT",
        f"http://{api}/2020-08-15/logs",
        headers={"Lambda-Extension-Identifier": ext_id, "Content-Type": "application/json"},
        payload=body,
        timeout=5,
    )


# ---------------------------------------------------------------------------
# Task draining logic
# ---------------------------------------------------------------------------
def _drain_for_request(request_id: str, soft_deadline_epoch: Optional[float]) -> None:
    """Run queued async tasks for ``request_id`` while observing an optional deadline."""
    with _tasks_lock:
        tasks = _tasks_by_request_id.pop(request_id, None)
    if not tasks:
        return

    if soft_deadline_epoch is None:
        for cb, payload in tasks:
            if cb is not None:
                cb(payload)
        return

    now = time.time
    i = 0
    n = len(tasks)
    while i < n:
        if now() > soft_deadline_epoch:
            # Put back the remaining tasks (i..end) preserving order
            remaining = tasks[i:]
            if remaining:
                with _tasks_lock:
                    bucket = _tasks_by_request_id.setdefault(request_id, [])
                    bucket[:0] = remaining
            return
        cb, payload = tasks[i]
        if cb is not None:
            cb(payload)
        i += 1


# ---------------------------------------------------------------------------
# Telemetry ingestion HTTP server
# ---------------------------------------------------------------------------
class _LogsHandler(BaseHTTPRequestHandler):
    """Receive telemetry batches and trigger draining of request-specific queues."""

    server_version = "CloudXSidecar/1.0"

    def log_message(self, *_: Any) -> None:  # Suppress stdlib logging noise
        return

    def do_POST(self) -> None:  # noqa: N802 (HTTP method name)
        if self.path != "/logs":
            self.send_response(404)
            self.end_headers()
            return
        try:
            payload_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(payload_length) if payload_length > 0 else b"[]"
            records: Iterable[Dict[str, Any]] = json.loads(body.decode("utf-8"))
            soft_deadline = time.time() + SOFT_DEADLINE_BUFFER
            for record in records:
                if record.get("type") == "platform.runtimeDone":
                    request_id = (record.get("record") or {}).get("requestId")
                    if request_id:
                        _drain_for_request(request_id, soft_deadline)
        finally:
            self.send_response(200)
            self.end_headers()


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------
def _event_next(ext_id: str) -> Dict[str, Any]:
    """Block until the runtime delivers the next extension event."""
    api = _ensure_runtime_api()
    _, _, body = _http(
        "GET",
        f"http://{api}/2020-01-01/extension/event/next",
        headers={"Lambda-Extension-Identifier": ext_id},
        timeout=None,
    )
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return {}


def _event_loop(ext_id: str) -> None:
    """Listen for runtime events as an internal extension.
    
    For internal extensions, we call /extension/event/next to:
    1. Wait for INVOKE events (Lambda notifies us of each invocation)
    2. Process any queued teardowns for that invocation
    3. Call /extension/event/next again to signal completion and wait for next invocation
    
    This keeps the execution environment alive until teardowns complete.
    Based on: https://aws.amazon.com/blogs/compute/running-code-after-returning-a-response-from-an-aws-lambda-function/
    """
    while not _stop_signal.is_set():
        try:
            # Call /extension/event/next - this blocks until Lambda sends an event
            # For INVOKE events, this is called BEFORE the handler runs
            event = _event_next(ext_id)
            event_type = event.get("eventType")
            
            if event_type == "INVOKE":
                # INVOKE event received - Lambda is about to invoke the handler
                # The handler runs and queues teardowns via start_async_task() during execution
                # After the handler returns, Lambda waits for us to call /extension/event/next again
                # We signal Lambda immediately, then wait for handler to signal teardowns are ready
                
                # Get request_id from event
                request_id = event.get("requestId")
                
                # Create a signal event for this request_id (if it doesn't exist)
                # The handler will signal this when teardowns are queued via start_async_task()
                with _signals_lock:
                    if request_id and request_id not in _teardown_signals:
                        _teardown_signals[request_id] = threading.Event()
                    signal = _teardown_signals.get(request_id) if request_id else None
                
                # Process teardowns asynchronously in a background thread
                # This allows Lambda to return the response immediately while teardowns run
                def process_teardowns_async():
                    # Wait for handler to signal completion
                    # Handler always signals via schedule_teardowns() -> _signal_handler_complete()
                    # This happens regardless of whether teardowns exist
                    if signal:
                        # Wait up to 30 seconds for handler to finish
                        signal.wait(timeout=30.0)
                    
                    # Check if teardowns were actually queued
                    teardowns_exist = False
                    if request_id:
                        with _tasks_lock:
                            teardowns_exist = request_id in _tasks_by_request_id and len(_tasks_by_request_id[request_id]) > 0
                    else:
                        with _tasks_lock:
                            teardowns_exist = len(_tasks_by_request_id) > 0
                    
                    # Process teardowns only if they exist
                    if teardowns_exist:
                        if request_id:
                            deadline = time.time() + SOFT_DEADLINE_BUFFER
                            _drain_for_request(request_id, deadline)
                        else:
                            deadline = time.time() + SOFT_DEADLINE_BUFFER
                            with _tasks_lock:
                                pending = list(_tasks_by_request_id.keys())
                            for rid in pending:
                                _drain_for_request(rid, deadline)
                    
                    # Clean up signal
                    if request_id:
                        with _signals_lock:
                            _teardown_signals.pop(request_id, None)
                
                # Start teardown processing in background thread (non-daemon to keep execution environment alive)
                threading.Thread(target=process_teardowns_async, daemon=False).start()
                
                # Call /extension/event/next again IMMEDIATELY to signal completion to Lambda
                # Lambda returns the response immediately after handler returns AND we call this
                # This call blocks until the next INVOKE event, which is correct behavior
                _event_next(ext_id)  # Signal completion and wait for next event
        except Exception as exc:
            logger.error(f"Error in extension event loop: {exc}")
            # Continue loop to avoid crashing
            time.sleep(0.1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def start_async_processor() -> None:
    """Initialise the internal Lambda extension when running inside Lambda.
    
    This registers an internal extension that runs as a separate thread within
    the Lambda process. The extension listens for INVOKE events and processes
    queued teardowns, allowing them to run after the handler returns.
    
    Based on: https://aws.amazon.com/blogs/compute/running-code-after-returning-a-response-from-an-aws-lambda-function/
    """
    global _extension_active, _http_server
    if _extension_active:
        return
    if "AWS_LAMBDA_RUNTIME_API" not in os.environ:
        _extension_active = False
        return

    with _start_lock:
        if _extension_active:
            return
        try:
            ext_id = _register_extension()
        except (RuntimeError, Exception) as exc:
            # Extension registration failed (e.g., 403 Forbidden)
            # Note: AWS Lambda may not allow internal extensions to be registered
            # from Python code in all environments (e.g., SAM, certain runtime versions).
            # This is expected behavior - teardowns will execute inline instead.
            error_msg = str(exc)
            if "403" in error_msg or "Forbidden" in error_msg:
                # 403 Forbidden in production AWS Lambda indicates that internal extensions
                # registered from Python code may not be supported. AWS Lambda may require
                # extensions to be separate processes (external extensions) deployed as layers,
                # rather than threads registered from within the function code.
                # This is expected behavior - teardowns will execute inline instead.
                logger.info(
                    f"Lambda extension registration not available (403 Forbidden). "
                    "Internal extensions registered from Python code may not be supported in production AWS Lambda. "
                    "Teardowns will execute inline (synchronously) instead of being deferred."
                )
            else:
                # Other errors should be logged as info (fallback works, so not a critical error)
                logger.info(
                    f"Failed to register Lambda extension: {exc}. "
                    "Teardowns will execute inline instead of being deferred."
                )
            _extension_active = False
            return

        try:
            # For internal extensions, we don't need the HTTP server for telemetry
            # We use INVOKE events instead of platform.runtimeDone telemetry
            # The event loop will process teardowns when INVOKE events arrive
            
            _extension_active = True
            # Start the event loop in a daemon thread
            # This thread will call /extension/event/next to wait for INVOKE events
            # and process teardowns, keeping the execution environment alive
            threading.Thread(target=_event_loop, args=(ext_id,), name=LAMBDA_EXTENSION_NAME, daemon=True).start()
        except Exception as exc:
            # If setup fails after registration, log and disable extension
            logger.warning(
                f"Failed to start Lambda extension components: {exc}. "
                "Teardowns will execute inline instead of being deferred."
            )
            _extension_active = False
            if _http_server:
                try:
                    _http_server.shutdown()
                except Exception:
                    pass


# Auto-register internal extension during INIT phase if running in Lambda
# Internal extensions run as separate threads and can be registered from within
# the function code. They use INVOKE events to process teardowns after the handler returns.
# Reference: https://aws.amazon.com/blogs/compute/running-code-after-returning-a-response-from-an-aws-lambda-function/
#
# Strategy: Try registration during INIT phase (module import), but also allow
# registration attempts from the handler if INIT phase registration failed.
# The retry logic in _register_extension() handles timing issues without fixed delays.
# If registration fails, it gracefully falls back to inline execution.
if "AWS_LAMBDA_RUNTIME_API" in os.environ:
    try:
        # Strategy 1: Register during module import (INIT phase)
        # This is the preferred timing - extensions should register during INIT
        # Retry logic handles cases where runtime API isn't immediately ready
        start_async_processor()
    except Exception:
        # Registration failed during INIT - will try again from handler if needed
        # Error is already logged in start_async_processor() as INFO
        pass


def stop_async_processor() -> None:
    """Signal background workers and HTTP server to shut down (testing convenience)."""
    _stop_signal.set()
    server = _http_server
    if server:
        try:
            server.shutdown()
        finally:
            try:
                server.server_close()
            except Exception:
                pass


def _signal_handler_complete(request_id: Optional[str]) -> None:
    """Signal the extension that the handler has completed.
    
    This is called when the handler finishes, regardless of whether teardowns exist.
    The extension will check for teardowns and process them if available.
    """
    if not _extension_active or not request_id:
        return
    
    with _signals_lock:
        signal = _teardown_signals.get(request_id)
        if signal:
            signal.set()


def start_async_task(
    async_task: Optional[Callable[[Any], None]] = None,
    args: Any = None,
    *,
    request_id: Optional[str] = None,
) -> None:
    """Queue work to run after the Lambda handler completes.

    Parameters
    ----------
    async_task: Callable executed after ``platform.runtimeDone``. ``None`` results in a no-op.
    args: Payload forwarded to ``async_task`` when it executes.
    request_id: Lambda invocation identifier; required for deferred execution.

    Notes
    -----
    When the extension is inactive (for example, during local tests) or `request_id` is
    missing, the work executes inline so behaviour remains deterministic.
    """
    if async_task is None:
        return

    if not _extension_active:
        async_task(args)
        return

    if not request_id:
        async_task(args)
        return

    with _tasks_lock:
        bucket = _tasks_by_request_id.setdefault(request_id, [])
        bucket.append((async_task, args))
    
    # Signal the extension that teardowns are queued for this request
    _signal_handler_complete(request_id)


def is_async_processor_active() -> bool:
    """Expose whether the Lambda sidecar has been successfully initialised."""

    return _extension_active
