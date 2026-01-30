import asyncio
from typing import Dict, Set, Callable, Any
from .logger import Logger

class TaskManager:
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.cancelled_tasks: Set[str] = set()
        self.task_functions: Dict[str, Callable] = {}
        self.task_args: Dict[str, tuple] = {}
        self.task_kwargs: Dict[str, dict] = {}

    async def create_task(self, task_id: str, coro_func: Callable, *args, **kwargs) -> asyncio.Task:
        """Create and track a task."""
        # Cancel existing task if it exists
        if task_id in self.active_tasks and not self.active_tasks[task_id].done():
            self.active_tasks[task_id].cancel()
            try:
                await self.active_tasks[task_id]
            except asyncio.CancelledError:
                pass

        # Store task information for recreation
        self.task_functions[task_id] = coro_func
        self.task_args[task_id] = args
        self.task_kwargs[task_id] = kwargs

        # Create new task
        task = asyncio.create_task(coro_func(*args, **kwargs))
        self.active_tasks[task_id] = task
        
        Logger.log_info(f"Created task: {task_id}")
        return task

    async def recreate_task(self, task_id: str) -> asyncio.Task:
        """Recreate a cancelled or failed task."""
        if task_id not in self.task_functions:
            raise ValueError(f"No task function stored for task_id: {task_id}")

        coro_func = self.task_functions[task_id]
        args = self.task_args[task_id]
        kwargs = self.task_kwargs[task_id]

        # Remove from cancelled set
        self.cancelled_tasks.discard(task_id)

        Logger.log_info(f"Recreating task: {task_id}")
        return await self.create_task(task_id, coro_func, *args, **kwargs)

    async def handle_task_completion(self, task_id: str):
        """Handle task completion and check for cancellation."""
        if task_id not in self.active_tasks:
            return

        task = self.active_tasks[task_id]
        
        try:
            result = await task
            Logger.log_success(f"Task {task_id} completed successfully")
            return result
        except asyncio.CancelledError:
            Logger.log_warning(f"Task {task_id} was cancelled")
            self.cancelled_tasks.add(task_id)
            raise
        except Exception as e:
            Logger.log_error(f"Task {task_id} failed: {e}")
            raise

    async def restart_cancelled_tasks(self):
        """Restart all cancelled tasks."""
        for task_id in list(self.cancelled_tasks):
            try:
                await self.recreate_task(task_id)
            except Exception as e:
                Logger.log_error(f"Failed to recreate task {task_id}: {e}")

    def cancel_task(self, task_id: str):
        """Cancel a specific task."""
        if task_id in self.active_tasks and not self.active_tasks[task_id].done():
            self.active_tasks[task_id].cancel()
            Logger.log_info(f"Cancelled task: {task_id}")

    def cancel_all_tasks(self):
        """Cancel all active tasks."""
        for task_id, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                Logger.log_info(f"Cancelled task: {task_id}")