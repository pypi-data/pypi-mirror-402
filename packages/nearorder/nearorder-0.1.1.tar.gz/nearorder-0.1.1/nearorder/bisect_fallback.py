from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .types import Cmp, Order, T, RandomAccess


@dataclass
class SearchState:
    fallback_count: int = -1
    cmp_count: int = 0
    search_route: List[Tuple[int, int, bool]] = field(default_factory=list)


def binary_search_with_fallback(
    xs: RandomAccess[T],
    k: T,
    *,
    cmp: Cmp = lambda a, b: a - b,
    order: Order = "asc",
    state: SearchState | None = None,
) -> Optional[int]:
    """
    A binary search implementation with a fallback mechanism.

    Under ideal conditions, this function behaves similarly to a standard
    binary search. When comparison results become unreliable, local disorder
    is encountered, or the search state degrades, fallback logic is triggered
    to ensure reachability of the result.

    It should be noted that in the worst case, where fallback is repeatedly
    activated, the algorithm may degrade into traversing the entire sequence,
    resulting in near O(n) time complexity.

    :param xs: A sized, random-access container providing ``__len__`` and
           integer-based ``__getitem__``. The elements are assumed to be
           globally ordered with possible local disorder.
    :type xs: RandomAccess[T]
    :param k: The value to search for.
    :type k: T
    :param cmp: Comparison function used to determine relative ordering.
    :type cmp: Cmp
    :param order: Global ordering of the sequence, ascending or descending.
    :type order: Order
    :param state: Optional search state object for tracking fallback behavior.
    :type state: SearchState | None
    :return: The index of the target if found; otherwise, None.
    :rtype: int | None
    """

    stack = [(0, len(xs) - 1, False)]  # fallback stack

    # normalize direction: asc = +1, desc = -1
    order_sign = 1 if order == "asc" else -1

    while stack:
        left, right, is_fallback = stack.pop()
        if state is not None:
            if is_fallback:
                state.fallback_count += 1
            state.search_route.append((left, right, is_fallback))

        if left > right:
            continue

        mid = (left + right) // 2

        c = cmp(xs[mid], k)
        if state is not None:
            state.cmp_count += 1
        if c == 0:
            return mid

        # normalized binary decision
        cmp_mid = c * order_sign

        if cmp_mid < 0:
            # k in right half
            stack.append((left, mid - 1, True))  # fallback
            left = mid + 1  # main path
        else:
            # k in left half
            stack.append((mid + 1, right, True))  # fallback
            right = mid - 1  # main path

        # continue main path
        if left <= right:
            stack.append((left, right, False))

    return None
