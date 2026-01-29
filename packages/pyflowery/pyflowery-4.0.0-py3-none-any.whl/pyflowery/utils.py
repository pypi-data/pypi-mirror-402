import asyncio
import threading
from collections.abc import Coroutine
from logging import Logger
from typing import TypeVar

__all__ = ["call_async"]

R = TypeVar("R")


def call_async(
    coroutine: Coroutine[None, None, R],
    logger: Logger,
) -> asyncio.Task[R] | R:
    """
    Call an async function safely in both synchronous and asynchronous contexts.

    - If no event loop is running in this thread: runs the coroutine with asyncio.run and returns the result.
    - If an event loop is running in this thread: runs the coroutine in a new thread with its own loop and blocks
      until completion, returning the result.
    - Returns an asyncio.Task if you explicitly want to schedule in the current loop without blocking.

    Args:
        coroutine: the coroutine to await
        logger: standard library Logger for reporting what’s happening

    Returns:
        The completed result (R) or an asyncio.Task[R] if scheduled in a live loop without blocking.
    """
    name = coroutine.__qualname__

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # There's a running loop; run the coroutine in a separate thread to avoid deadlock
        logger.info("Event loop running; offloading %r to a background thread", name)

        result_container: dict[str, R] = {}

        def target():
            result_container["result"] = asyncio.run(coroutine)

        t = threading.Thread(target=target)
        t.start()
        t.join()  # Block until completion
        return result_container["result"]
    else:
        # No loop running; safe to run normally
        logger.info("No running event loop; running %r via asyncio.run", name)
        return asyncio.run(coroutine)
