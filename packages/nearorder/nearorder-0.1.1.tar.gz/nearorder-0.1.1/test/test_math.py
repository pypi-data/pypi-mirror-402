from nearorder.math.metrics import local_inversion_ratio, max_monotonic_run


def test_local_inversion_ratio_len_less_then_2():
    assert local_inversion_ratio([1]) == 0.0


def test_max_monotonic_run_len_less_then_2():
    nums = [1]
    assert max_monotonic_run(nums) == len(nums)
