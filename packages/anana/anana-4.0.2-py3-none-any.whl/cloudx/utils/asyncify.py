import asyncio
import contextvars
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

def asyncify(func: Callable) -> Callable:
    """
    Converts a synchronous function to an asynchronous function or wraps an asynchronous function for safe execution.

    Parameters:
        func (Callable): The function to be converted or wrapped.

    Returns:
        Callable: An asynchronous version of the input function.
    
    Example:
        @asyncify
        def blocking_function(x, y):
            import time
            time.sleep(2)
            return x + y

        @asyncify
        async def async_function_with_blocking_code():
            import time
            time.sleep(2)  # Blocking call in an async function

        async def main():
            result = await blocking_function(2, 3)
            print(result)
            await async_function_with_blocking_code()

        asyncio.run(main())
    Notes:
        - This decorator works need to be the first decorators applied to the function.
        - It utilizes a `ThreadPoolExecutor` to run the blocking function in a separate 
          thread, allowing the event loop to continue processing other tasks.
    """
    executor = ThreadPoolExecutor()

    # Check if the function is synchronous
    if not asyncio.iscoroutinefunction(func):
        async def sync_wrapper(*asyncify_args, **asyncify_kwargs):
            # Capture the current context
            current_context = contextvars.copy_context()
            loop = asyncio.get_event_loop()

            # Use the copied context when running the blocking function in the executor
            return await loop.run_in_executor(executor, lambda: current_context.run(func, *asyncify_args, **asyncify_kwargs))

        return sync_wrapper
    
    # If the function is asynchronous
    async def async_wrapper(*asyncify_args, **asyncify_kwargs):
        # Capture the current context
        current_context = contextvars.copy_context()
        loop = asyncio.get_event_loop()

        # Run the async function in the executor while maintaining the context
        return await loop.run_in_executor(executor, lambda: current_context.run(asyncio.run, func(*asyncify_args, **asyncify_kwargs)))

    return async_wrapper
