"""
Absufyu: Multithread runner
---------------------------
Run a task multithreaded

Version: 6.3.0
Date updated: 20/01/2026 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "MultiThreadRunner",
]


# Library
# ---------------------------------------------------------------------------
import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

from absfuyu.core.dummy_func import tqdm
from absfuyu.logger import LoggerMixin


# Class
# ---------------------------------------------------------------------------
class MultiThreadRunner[T](LoggerMixin[logging.Logger], ABC):
    """
    Multi-thread batch runner with:
    - error aggregation
    - retry per task
    - cancellation on N failures
    - async + thread hybrid support


    Example:
    --------
    >>> class Test(MultiThreadRunner):
    ...     def get_tasks(self):
    ...         return list(range(1000))
    ...     def run_one(self, task):
    ...         print(task, end=" ")
    >>> e = Test().run()
    """

    # Abstract
    # ---------------------------
    @abstractmethod
    def get_tasks(self) -> Iterable[T]:
        raise NotImplementedError()

    @abstractmethod
    def run_one(self, task: T) -> None:
        raise NotImplementedError()

    # Main
    # ---------------------------
    def run(
        self,
        *,
        workers: int | None = None,
        desc: str = "Processing",
        max_failures: int | None = None,
        max_retries: int = 0,
        retry_backoff: float = 0.0,
        fallback_to_single: bool = True,
        tqdm_enabled: bool = True,
    ) -> None:
        """
        Run tasks in multi-thread mode.

        Parameters
        ----------
        max_failures : int | None, optional
            Cancel execution once this many failures occur.
            None = unlimited.

        max_retries : int, optional
            Retry count per task.

        retry_backoff : float, optional
            Seconds to sleep between retries.

        fallback_to_single : bool, optional
            Fallback to single-thread if multi-thread infra fails.

        tqdm_enabled : bool, optional
            Visualize in terminal with tqdm if available
        """
        self.errors: list[tuple[T, Exception]] = []
        tasks = list(self.get_tasks())

        if not tasks:
            return

        try:
            self._run_multi(
                tasks=tasks,
                workers=workers,
                desc=desc,
                max_failures=max_failures,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                tqdm_enabled=tqdm_enabled,
            )
        except Exception as exc:
            self.logger.warning(f"Multi-thread failed: {exc}")

            if not fallback_to_single:
                raise

            self.logger.info("Falling back to single-thread")
            self._run_single(
                tasks=tasks,
                desc=desc,
                max_failures=max_failures,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                tqdm_enabled=tqdm_enabled,
            )

    async def async_run(self, **kwargs) -> None:
        """
        Async wrapper for run().
        Suitable for asyncio applications.
        """
        await asyncio.to_thread(self.run, **kwargs)

    # Internal execution
    # ---------------------------
    def _run_multi(
        self,
        *,
        tasks: list[T],
        workers: int | None,
        desc: str,
        max_failures: int | None,
        max_retries: int,
        retry_backoff: float,
        tqdm_enabled: bool = True,
    ) -> None:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    self._run_with_retry,
                    task,
                    max_retries,
                    retry_backoff,
                ): task
                for task in tasks
            }

            ff = as_completed(futures)
            if tqdm_enabled:
                ff = tqdm(as_completed(futures), total=len(futures), desc=f"{desc} (multi-thread)")

            for future in ff:
                try:
                    future.result()
                except Exception:
                    # Should not happen (handled internally)
                    pass

                if max_failures is not None and len(self.errors) >= max_failures:
                    self.logger.info("[ABORT] Failure threshold reached, cancelling remaining tasks")
                    for f in futures:
                        f.cancel()
                    break

    def _run_single(
        self,
        *,
        tasks: list[T],
        desc: str,
        max_failures: int | None,
        max_retries: int,
        retry_backoff: float,
        tqdm_enabled: bool = True,
    ) -> None:
        if tqdm_enabled:
            tasks = tqdm(tasks, desc=f"{desc} (single-thread)")
        for task in tasks:
            self._run_with_retry(task, max_retries, retry_backoff)

            if max_failures is not None and len(self.errors) >= max_failures:
                self.logger.info("[ABORT] Failure threshold reached")
                break

    # Retry + error aggregation
    # ---------------------------
    def _run_with_retry(
        self,
        task: T,
        max_retries: int,
        retry_backoff: float,
    ) -> None:
        attempt = 0

        while True:
            try:
                self.run_one(task)
                return
            except Exception as exc:
                attempt += 1

                if attempt > max_retries:
                    self.errors.append((task, exc))
                    self.logger.info(f"[FAIL] {task} ({exc})")
                    return

                self.logger.info(f"[RETRY] {task} ({attempt}/{max_retries})")

                if retry_backoff > 0:
                    import time

                    time.sleep(retry_backoff)


if __name__ == "__main__":
    from typing import override

    from absfuyu.logger import AbsfuyuLogger

    class Test(MultiThreadRunner):
        CUSTOM_LOGGER = AbsfuyuLogger.default_config
        LOGGER_NAME = "APP"

        @override
        def get_tasks(self):
            self.logger.setLevel(10)
            return list(range(1000))

        @override
        def run_one(self, task):
            import random

            if random.random() < 0.7:
                raise ValueError()
            print(task, end=" ")

    e = Test()
    e.run(tqdm_enabled=False, max_failures=100, max_retries=5)
