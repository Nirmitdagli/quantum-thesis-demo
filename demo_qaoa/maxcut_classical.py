"""Classical greedy heuristic for the MaxCut problem."""

from typing import List, Tuple, Set


def greedy_maxcut(
    n_nodes: int, edges: List[Tuple[int, int]]
) -> Tuple[int, Set[int], Set[int]]:
    """Greedy MaxCut: assign each node to the partition that maximizes cut edges.

    Returns:
        (cut_value, set_a, set_b)
    """
    set_a: Set[int] = set()
    set_b: Set[int] = set()

    # Build adjacency list
    adj: dict = {i: [] for i in range(n_nodes)}
    for i, j in edges:
        adj[i].append(j)
        adj[j].append(i)

    for node in range(n_nodes):
        cut_if_a = sum(1 for nb in adj[node] if nb in set_b)
        cut_if_b = sum(1 for nb in adj[node] if nb in set_a)
        if cut_if_a >= cut_if_b:
            set_a.add(node)
        else:
            set_b.add(node)

    cut_value = sum(1 for i, j in edges if (i in set_a) != (j in set_a))
    return cut_value, set_a, set_b
