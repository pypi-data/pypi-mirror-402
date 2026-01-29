from typing import Sequence

from nearorder.types import Order


def inversion_count(xs: Sequence[int], *, order: Order = "asc") -> int:
    """
    Counts total number of inversions relative to expected order.
    O(n log n) using merge sort.
    """
    sign = 1 if order == "asc" else -1

    def merge_count(arr):
        if len(arr) <= 1:
            return arr, 0

        mid = len(arr) // 2
        left, inv_l = merge_count(arr[:mid])
        right, inv_r = merge_count(arr[mid:])

        merged = []
        i = j = inv_split = 0

        while i < len(left) and j < len(right):
            if sign * (left[i] - right[j]) <= 0:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                inv_split += len(left) - i
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, inv_l + inv_r + inv_split

    _, count = merge_count(list(xs))
    return count


def local_inversion_ratio(xs: Sequence[int], *, order: Order = "asc") -> float:
    """
    Ratio of adjacent inversions relative to expected order.
    """
    if len(xs) < 2:
        return 0.0

    sign = 1 if order == "asc" else -1
    inv = sum(1 for i in range(len(xs) - 1) if sign * (xs[i] - xs[i + 1]) > 0)
    return inv / (len(xs) - 1)


def max_monotonic_run(xs: Sequence[int], *, order: Order = "asc") -> int:
    """
    Length of the longest monotonic run consistent with expected order.
    """
    if len(xs) < 2:
        return len(xs)

    sign = 1 if order == "asc" else -1

    max_run = run = 1
    direction = 0  # 1 = forward, -1 = backward

    for i in range(1, len(xs)):
        diff = sign * (xs[i] - xs[i - 1])
        new_dir = 1 if diff > 0 else -1 if diff < 0 else 0

        if new_dir == 0 or (direction != 0 and new_dir != direction):
            run = 1
        else:
            run += 1

        direction = new_dir
        max_run = max(max_run, run)

    return max_run


def displacement_sum(xs: Sequence[int], *, order: Order = "asc") -> int:
    """
    Sum of absolute displacement from expected sorted positions.
    """
    sorted_xs = sorted(xs, reverse=(order == "desc"))
    index_map = {v: i for i, v in enumerate(sorted_xs)}

    return sum(abs(i - index_map[v]) for i, v in enumerate(xs))


def disorder_metrics(xs: Sequence[int], order: Order = "asc") -> dict:
    """
    Aggregate disorder metrics.
    """
    n = len(xs)
    max_inv = n * (n - 1) // 2

    inv = inversion_count(xs, order=order)

    return {
        "n": n,
        "inversion_count": inv,
        "inversion_ratio": inv / max_inv if max_inv else 0.0,
        "local_inversion_ratio": local_inversion_ratio(xs, order=order),
        "max_monotonic_run": max_monotonic_run(xs, order=order),
        "displacement_sum": displacement_sum(xs, order=order),
    }
