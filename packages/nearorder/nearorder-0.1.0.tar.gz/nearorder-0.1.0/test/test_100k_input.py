from datetime import datetime

import pytest

from nearorder.bisect import binary_search
from nearorder.bisect_fallback import SearchState, binary_search_with_fallback
from nearorder.filter import filter_window
from test.utils import parse_csv_datetimes


@pytest.fixture(scope="module")
def data_with_k():
    data = parse_csv_datetimes("test_data/datetime_2020~2025.csv")
    k = datetime(
        year=2025,
        month=8,
        day=7,
        hour=23,
        minute=29,
        second=59,
    )
    return data, k


def cmp(a: datetime, b: datetime) -> int:
    def datetime_to_days(dt: datetime) -> int:
        return (dt - datetime(1900, 1, 1)).days + 2

    rt = datetime_to_days(a) - datetime_to_days(b)
    return int(rt)


def cmp_precise(a: datetime, b: datetime) -> int:
    rt = a.timestamp() - b.timestamp()
    return int(rt)


def test_binary_search_fallback(data_with_k):
    data, k = data_with_k
    state = SearchState()
    index = binary_search_with_fallback(data, k, cmp=cmp, state=state, order="desc")
    assert index is not None


def test_binary_search(data_with_k):
    data, k = data_with_k
    index = binary_search(data, k, cmp=cmp, window_size=5, order="desc")
    assert index is not None


# This test is expected to return None because this algorithm cannot fall back
def test_binary_search_precise(data_with_k):
    data, k = data_with_k
    index = binary_search(data, k, cmp=cmp_precise, window_size=5, order="desc")
    assert index is None


# This test is expected to return the correct index because it uses fallback,
# it will cost very more comparisons
def test_binary_search_fallback_precise(data_with_k):
    data, k = data_with_k
    state = SearchState()
    index = binary_search_with_fallback(
        data, k, cmp=cmp_precise, state=state, order="desc"
    )
    assert index == 6991


def test_filter_window(data_with_k):
    data, k = data_with_k
    index = binary_search(data, k, cmp=cmp, order="desc")
    assert index is not None
    result = filter_window(data, k, index, window_size=24 * 4, cmp=cmp_precise)
    assert len(result) == 1

