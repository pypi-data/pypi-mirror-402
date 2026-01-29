import pytest

from nearorder.bisect import binary_search
from test.utils import show_disorder_metrics


def test_mid_hit_dirty_data():
    nums = [1, 2, 3, 5, 8, 6, 7, 10, 9]
    index = binary_search(nums, 10)
    show_disorder_metrics(nums)
    assert index == 7


def test_mid_hit_normal_data():
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    index = binary_search(nums, 1)
    show_disorder_metrics(nums)
    assert index == 0


def test_mid_hit_k():
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    index = binary_search(nums, 5)
    show_disorder_metrics(nums)
    assert index == 4


def test_mid_hit_dirty_data_desc():
    nums = [9, 10, 8, 4, 6, 7, 3, 1, 2]
    index = binary_search(nums, 9, order="desc")
    show_disorder_metrics(nums, order="desc")
    assert index == 0


def test_mid_hit_normal_data_desc():
    nums = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    index = binary_search(nums, 4, order="desc")
    show_disorder_metrics(nums, order="desc")
    assert index == 6


def test_invalid_window_size():
    nums = []
    with pytest.raises(ValueError):
        binary_search(nums, 1, window_size=-1)


def test_no_exist_data():
    nums = []
    index = binary_search(nums, 1)
    assert index is None
