"""
Async Task Management for NetworkDoctor
"""
import asyncio
from typing import List, Callable, Any, Coroutine
from asyncio import Semaphore


class AsyncExecutor:
    """Manages async task execution with concurrency control"""
    
    def __init__(self, max_concurrent: int = 10):
        """
        Initialize async executor.
        
        Args:
            max_concurrent: Maximum concurrent tasks
        """
        self.semaphore = Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
    
    async def execute(self, coro: Coroutine) -> Any:
        """
        Execute a coroutine with semaphore control.
        
        Args:
            coro: Coroutine to execute
            
        Returns:
            Coroutine result
        """
        async with self.semaphore:
            return await coro
    
    async def execute_batch(
        self,
        coros: List[Coroutine],
        return_exceptions: bool = False
    ) -> List[Any]:
        """
        Execute multiple coroutines concurrently.
        
        Args:
            coros: List of coroutines
            return_exceptions: Return exceptions instead of raising
            
        Returns:
            List of results
        """
        tasks = [self.execute(coro) for coro in coros]
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    
    async def execute_with_timeout(
        self,
        coro: Coroutine,
        timeout: float
    ) -> Any:
        """
        Execute coroutine with timeout.
        
        Args:
            coro: Coroutine to execute
            timeout: Timeout in seconds
            
        Returns:
            Coroutine result
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        async with self.semaphore:
            return await asyncio.wait_for(coro, timeout=timeout)


async def run_parallel(
    tasks: List[Callable],
    max_concurrent: int = 10
) -> List[Any]:
    """
    Run tasks in parallel with concurrency limit.
    
    Args:
        tasks: List of async functions
        max_concurrent: Maximum concurrent executions
        
    Returns:
        List of results
    """
    executor = AsyncExecutor(max_concurrent)
    coros = [task() if callable(task) else task for task in tasks]
    return await executor.execute_batch(coros)







