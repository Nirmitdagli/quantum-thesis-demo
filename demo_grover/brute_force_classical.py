"""Classical brute-force search baseline for key search."""

import time
from typing import Tuple


def brute_force_search(n_qubits: int, marked_state: int) -> Tuple[float, int]:
    """Search through all 2^n states sequentially until the target is found.

    Returns:
        (runtime_seconds, found_state)
    """
    N = 2 ** n_qubits
    start = time.perf_counter()
    for state in range(N):
        if state == marked_state:
            elapsed = time.perf_counter() - start
            return elapsed, state
    elapsed = time.perf_counter() - start
    return elapsed, -1
