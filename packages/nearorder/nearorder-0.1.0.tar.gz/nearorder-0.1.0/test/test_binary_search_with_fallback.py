from nearorder.bisect_fallback import SearchState, binary_search_with_fallback
from test.utils import disorder_metrics, show_disorder_metrics_with_state


def test_worst_case_1():
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]
    state = SearchState()
    index = binary_search_with_fallback(nums, k=0, state=state)

    show_disorder_metrics_with_state(nums, state)

    assert index == 11


def test_worst_case_2():
    nums = [1, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 0]
    state = SearchState()
    index = binary_search_with_fallback(nums, k=1, order="desc", state=state)

    show_disorder_metrics_with_state(nums, state, order="desc")

    assert index == 0


def test_k_not_found():
    nums = [1, 2, 3, 4, 5]
    index = binary_search_with_fallback(nums, k=6)
    assert index is None
