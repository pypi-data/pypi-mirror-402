import asyncio
import functools
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, TypeVar, Coroutine

log = logging.getLogger(__name__)

T = TypeVar('T')


def background_task(
        interval: int,
        name: str = None,
        max_workers: int = 0,
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, None]]]:
    """
    Decorator that turns a coroutine into a background task
    with proper cancellation handling for a graceful shutdown.

    Args:
        interval: Interval in seconds between each execution
        name: Name of the task for logging (optional)
        max_workers: Maximum number of workers. 0 means no ThreadPoolExecutor

    Returns:
        The decorated function that runs at regular intervals
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, None]]:
        task_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            try:
                if max_workers > 0:
                    with ThreadPoolExecutor(max_workers=max_workers) as pool:
                        try:
                            kwargs['pool'] = pool
                            await _run_task_loop(func, task_name, interval, *args, **kwargs)
                        finally:
                            # When task is finished (normal or cancelled by SIGTERM) then shutdown the pool and cancel any futures
                            pool.shutdown(wait=False, cancel_futures=True)
                else:
                    await _run_task_loop(func, task_name, interval, *args, **kwargs)
            except asyncio.CancelledError:
                log.info(f"{task_name} cancelled, shutting down gracefully")
            finally:
                log.info(f"{task_name} shut down complete")

        return wrapper

    return decorator


async def _run_task_loop(
        func: Callable[..., Coroutine[Any, Any, T]],
        task_name: str,
        interval: int,
        *args: Any,
        **kwargs: Any
) -> None:
    """Runs the function in a loop with cancellation handling."""
    while True:
        try:
            await func(*args, **kwargs)
        except Exception:
            log.exception(f"Error in {task_name}")

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            log.info(f"{task_name} received cancellation signal, shutting down gracefully")
            break
