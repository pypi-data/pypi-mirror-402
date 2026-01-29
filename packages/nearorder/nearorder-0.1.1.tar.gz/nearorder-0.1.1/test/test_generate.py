from nearorder.math.generate import (
    base_sequence,
    block_shuffle,
    break_runs,
    inject_adjacent_swaps,
    partial_shuffle,
)


def test_base_sequence():
    seq = base_sequence(10)
    assert seq == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_inject_adjacent_swaps():
    seq = base_sequence(10)
    swapped_seq = inject_adjacent_swaps(seq, swaps=1, seed=114)
    assert len(swapped_seq) == len(seq)
    # Check that approximately 20% of the elements have been swapped
    swap_count = sum(1 for a, b in zip(seq, swapped_seq) if a != b)
    assert 1 <= swap_count <= 3  # Allowing some variance


def test_block_shuffle():
    seq = base_sequence(16)
    shuffled_seq = block_shuffle(seq, block_size=4, seed=114)
    assert len(shuffled_seq) == len(seq)
    # Check that all elements are still present
    assert sorted(shuffled_seq) == sorted(seq)
    # Check that blocks of size 4 have been shuffled
    blocks = [shuffled_seq[i : i + 4] for i in range(0, len(shuffled_seq), 4)]
    original_blocks = [seq[i : i + 4] for i in range(0, len(seq), 4)]
    assert blocks != original_blocks  # Ensure that the order of blocks has changed


def test_block_shuffle_size_less_than_1():
    seq = base_sequence(10)
    shuffled_seq = block_shuffle(seq, block_size=0)
    assert shuffled_seq == seq  # No change expected


def test_break_runs():
    seq = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    broken_seq = break_runs(seq, every=3)
    assert len(broken_seq) == len(seq)
    # Check that no run exceeds the every limit
    current_run_length = 1
    for i in range(1, len(broken_seq)):
        if broken_seq[i] == broken_seq[i - 1] + 1:
            current_run_length += 1
            assert current_run_length <= 3
        else:
            current_run_length = 1


def test_partial_shuffle():
    seq = base_sequence(10)
    shuffled_seq = partial_shuffle(seq, ratio=0.3, seed=114)
    assert len(shuffled_seq) == len(seq)
    # Check that all elements are still present
    assert sorted(shuffled_seq) == sorted(seq)
    # Check that approximately 30% of the elements have been moved
    move_count = sum(1 for a, b in zip(seq, shuffled_seq) if a != b)
    assert 2 <= move_count <= 4  # Allowing some variance
