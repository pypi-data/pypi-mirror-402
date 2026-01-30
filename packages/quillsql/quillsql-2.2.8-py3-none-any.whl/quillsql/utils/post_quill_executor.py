from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, Optional


class ParallelPostQuill:
    """
    Provides a thread-pooled, drop-in replacement for Quill.post_quill.

    Example
    -------
        parallel_post = ParallelPostQuill(
            quill_factory=lambda: Quill(...),
            max_workers=4,
        )

        # Synchronous (behaves like the original post_quill)
        response = parallel_post("report", payload)

        # Async-style execution
        future = parallel_post("report", payload, wait=False)
        response = future.result()
    """

    def __init__(
        self,
        quill_factory: Callable[[], "Quill"],
        max_workers: int = 5,
        executor: Optional[ThreadPoolExecutor] = None,
    ):
        if executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="post-quill",
            )
            self._owns_executor = True
        else:
            self._executor = executor
            self._owns_executor = False

        if not callable(quill_factory):
            raise ValueError("quill_factory must be callable and create Quill instances.")

        self._quill_factory = quill_factory
        self._thread_local = threading.local()

    def __call__(self, path: str, payload: dict, wait: bool = True):
        future: Future = self._executor.submit(self._invoke, path, payload)
        if wait:
            return future.result()
        return future

    def shutdown(self, wait: bool = True):
        if self._owns_executor:
            self._executor.shutdown(wait=wait)

    def _get_quill(self):
        quill = getattr(self._thread_local, "quill", None)
        if quill is None:
            quill = self._quill_factory()
            self._thread_local.quill = quill
        return quill

    def _invoke(self, path: str, payload: dict):
        quill = self._get_quill()
        return quill.post_quill(path, payload)

