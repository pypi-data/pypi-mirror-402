"""
infinity_ml: Python client for GPU-accelerated media generation.

    # Set your API key (or use INFINITY_API_KEY env var)
    import os
    os.environ["INFINITY_API_KEY"] = "your-api-key"

    from infinity_ml import run, submit, status, result

    # Simple usage (blocking)
    result = run("black-forest-labs/flux-dev", {"prompt": "A cat astronaut"})

    # Or use the client classes directly
    from infinity_ml import InfinitySyncClient, InfinityAsyncClient

    client = InfinitySyncClient(api_key="your-api-key")
    handle = client.submit("black-forest-labs/flux-dev", {"prompt": "A cat"})
    for event in handle.iter_events():
        print(event)
    result = handle.get()
"""

import os

from .client import (
    AsyncClient,  # Alias for InfinityAsyncClient
    AsyncRequestHandle,
    InfinityAsyncClient,
    InfinityClient,  # Legacy alias for InfinitySyncClient
    InfinityClientError,
    InfinitySyncClient,
    JobFailedError,
    SyncClient,  # Alias for InfinitySyncClient
    SyncRequestHandle,
    TimeoutError,
)
from .models import (
    AnyJSON,
    AudioResult,
    Completed,
    Failed,
    GenerationResult,
    ImageResult,
    InProgress,
    Queued,
    Status,
    VideoResult,
)

__version__ = "0.2.1"

# Default server URL (can be overridden via INFINITY_SERVER_URL env var)
DEFAULT_URL = os.environ.get("INFINITY_SERVER_URL", "https://api.infinity.inc")

# ─────────────────────────────────────────────────────────────────────────────
# Module-level convenience functions (mirrors fal_client)
# ─────────────────────────────────────────────────────────────────────────────

# Shared default client (lazily initialized)
_default_client: "InfinitySyncClient | None" = None
_default_async_client: "InfinityAsyncClient | None" = None


def _get_client() -> InfinitySyncClient:
    """Get or create the default sync client."""
    global _default_client
    if _default_client is None:
        _default_client = InfinitySyncClient()
    return _default_client


def _get_async_client() -> InfinityAsyncClient:
    """Get or create the default async client."""
    global _default_async_client
    if _default_async_client is None:
        _default_async_client = InfinityAsyncClient()
    return _default_async_client


def run(
    application: str,
    arguments: dict,
    *,
    timeout: float | None = None,
) -> dict:
    """
    Run an application with the given arguments (blocking).

    Args:
        application: Model name (e.g., "black-forest-labs/flux-dev")
        arguments: Model parameters as dict (e.g., {"prompt": "A cat"})
        timeout: Max seconds to wait

    Returns: Raw JSON response dict

    Example:
        result = run("black-forest-labs/flux-dev", {"prompt": "A cat"})
        print(result["images"][0]["download_url"])
    """
    return _get_client().run(application, arguments, timeout=timeout)


def submit(
    application: str,
    arguments: dict,
) -> SyncRequestHandle:
    """
    Submit a job (non-blocking).

    Args:
        application: Model name (e.g., "black-forest-labs/flux-dev")
        arguments: Model parameters as dict

    Returns: SyncRequestHandle for polling status and getting result

    Example:
        handle = submit("black-forest-labs/flux-dev", {"prompt": "A cat"})
        print(handle.request_id)
        result = handle.get()  # Blocks until complete
    """
    return _get_client().submit(application, arguments)


def subscribe(
    application: str,
    arguments: dict,
    *,
    on_enqueue=None,
    on_queue_update=None,
) -> dict:
    """
    Submit and subscribe to status updates until complete.

    Args:
        application: Model name
        arguments: Model parameters
        on_enqueue: Callback when job is enqueued (receives request_id)
        on_queue_update: Callback on each status update

    Returns: Raw JSON response dict
    """
    return _get_client().subscribe(
        application,
        arguments,
        on_enqueue=on_enqueue,
        on_queue_update=on_queue_update,
    )


def status(
    application: str,
    request_id: str,
    *,
    with_logs: bool = False,
) -> Status:
    """
    Get status of a request by ID.

    Returns: Queued, InProgress, Completed, or Failed
    """
    return _get_client().status(application, request_id, with_logs=with_logs)


def result(
    application: str,
    request_id: str,
) -> dict:
    """
    Get result of a completed request.

    Returns: Raw JSON response dict
    """
    return _get_client().result(application, request_id)


def cancel(
    application: str,
    request_id: str,
) -> None:
    """Cancel a request (if supported by server)."""
    return _get_client().cancel(application, request_id)


def health() -> dict:
    """
    Check if the server is healthy.

    Returns: {"status": "ok"} if healthy

    Example:
        import infinity_ml
        print(infinity_ml.health())  # {"status": "ok"}
    """
    return _get_client().health()


# ─────────────────────────────────────────────────────────────────────────────
# Async module-level functions
# ─────────────────────────────────────────────────────────────────────────────


async def run_async(
    application: str,
    arguments: dict,
    *,
    timeout: float | None = None,
) -> dict:
    """Async version of run()."""
    return await _get_async_client().run(application, arguments, timeout=timeout)


async def submit_async(
    application: str,
    arguments: dict,
) -> AsyncRequestHandle:
    """Async version of submit()."""
    return await _get_async_client().submit(application, arguments)


async def subscribe_async(
    application: str,
    arguments: dict,
    *,
    on_enqueue=None,
    on_queue_update=None,
) -> dict:
    """Async version of subscribe()."""
    return await _get_async_client().subscribe(
        application,
        arguments,
        on_enqueue=on_enqueue,
        on_queue_update=on_queue_update,
    )


async def status_async(
    application: str,
    request_id: str,
    *,
    with_logs: bool = False,
) -> Status:
    """Async version of status()."""
    return await _get_async_client().status(application, request_id, with_logs=with_logs)


async def result_async(
    application: str,
    request_id: str,
) -> dict:
    """Async version of result()."""
    return await _get_async_client().result(application, request_id)


async def cancel_async(
    application: str,
    request_id: str,
) -> None:
    """Async version of cancel()."""
    return await _get_async_client().cancel(application, request_id)


# ─────────────────────────────────────────────────────────────────────────────
# Exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    # Client classes (primary names)
    "InfinitySyncClient",
    "InfinityAsyncClient",
    # Client classes (aliases for convenience/compatibility)
    "SyncClient",
    "AsyncClient",
    "InfinityClient",
    # Request handles
    "SyncRequestHandle",
    "AsyncRequestHandle",
    # Status types
    "Status",
    "Queued",
    "InProgress",
    "Completed",
    "Failed",
    # Result types
    "ImageResult",
    "VideoResult",
    "AudioResult",
    "GenerationResult",
    "AnyJSON",
    # Exceptions
    "InfinityClientError",
    "JobFailedError",
    "TimeoutError",
    # Module-level functions (sync)
    "run",
    "submit",
    "subscribe",
    "status",
    "result",
    "cancel",
    "health",
    # Module-level functions (async)
    "run_async",
    "submit_async",
    "subscribe_async",
    "status_async",
    "result_async",
    "cancel_async",
]
