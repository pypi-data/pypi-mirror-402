from typing import Optional, Sequence

from .types import Cmp, Order, T


def binary_search(
    xs: Sequence[T],
    k,
    *,
    cmp: Cmp = lambda a, b: a - b,
    window_size: int = 1,
    order: Order = "asc",
) -> Optional[int]:
    """
    A robust binary search implementation.

    This function assumes the sequence is globally ordered while allowing
    limited local disorder. By relaxing comparison conditions and applying
    a window-based strategy, the search behavior remains close to that of
    a standard binary search in most cases.

    This implementation does not fall back to full sequence traversal.
    As a result, under severe disorder or unreliable comparison results,
    the target value may not be located.

    :param xs: The sequence to operate on, typically assumed to be globally
               ordered with possible local disorder.
    :type xs: Sequence[T]
    :param k: The value to search for.
    :type k: T
    :param cmp: Comparison function used to determine relative ordering.
    :type cmp: Cmp
    :param window_size: Window size used for the next binary step on both sides.
    :type window_size: int
    :param order: Global ordering of the sequence, ascending or descending.
    :type order: Order
    :return: An index determined by the precision of the comparison function;
             the result may be exact or approximate. Returns None if the
             target cannot be located.
    :rtype: int | None
    """

    if window_size <= 0:
        raise ValueError("window_size must be > 0")

    left = 0
    right = len(xs) - 1

    stack = []

    while left <= right:
        mid = (left + right) // 2
        stack.append((left, right))

        # 1. Hit
        if cmp(xs[mid], k) == 0:
            return mid

        # 2. Search in window
        window_left = max(0, mid - window_size)
        window_right = min(len(xs), mid + window_size + 1)

        c = 0
        for i in range(window_left, window_right):
            rt = cmp(xs[i], k)
            if rt == 0:
                return i
            if order == "asc":
                # xs[i] < k -> k in right side
                if rt < 0:
                    c += 1
                else:
                    c -= 1
            else:  # desc
                # xs[i] > k -> k in right side
                if rt > 0:
                    c += 1
                else:
                    c -= 1

        # 3. Shrink range
        if c > 0:
            left = mid + 1
        else:
            right = mid - 1

    return None
