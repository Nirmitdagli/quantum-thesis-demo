"""Timing utility for measuring experiment execution time."""

import time
from typing import Optional


class Timer:
    """Context manager for measuring execution time."""

    def __init__(self, label: str = "") -> None:
        self.label = label
        self.start_time: Optional[float] = None
        self.elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.elapsed = time.perf_counter() - self.start_time
