from nearorder.types import Cmp


def filter_window(
    xs, k, index: int, *, window_size: int, cmp: Cmp = lambda a, b: a - b
):
    """
    Linearly scan and filter matching elements within a window around a given index.

    This function centers a window on the specified index, applies boundary
    clamping, and sequentially traverses all elements within the window.
    Elements are selected if the comparison function indicates equality
    with the target value.

    This operation is always a linear scan, with time complexity proportional
    to the window size, and does not depend on the global ordering of the
    sequence.

    :param xs: The sequence to operate on.
    :type xs: Sequence[T]
    :param k: The target value used for matching.
    :type k: T
    :param index: The index used as the window center.
    :type index: int
    :param window_size: The size of the window.
    :type window_size: int
    :param cmp: Comparison function used to test equality.
    :type cmp: Cmp
    :return: All elements within the window that match the target value.
    :rtype: list[T]
    """
    start = max(index - window_size // 2, 0)
    end = min(index + window_size // 2, len(xs) - 1)
    return [xs[i] for i in range(start, end + 1) if cmp(xs[i], k) == 0]
