import random

from nearorder.types import Order


def base_sequence(n: int, order: Order = "asc"):
    """Generate a base sequence of integers from 0 to n-1 in specified order."""
    xs = list(range(n))
    return xs if order == "asc" else xs[::-1]


def inject_adjacent_swaps(xs, swaps: int, seed=None):
    """Inject a number of adjacent swaps into the sequence."""
    rng = random.Random(seed)
    xs = xs[:]
    n = len(xs)

    for _ in range(swaps):
        i = rng.randrange(0, n - 1)
        xs[i], xs[i + 1] = xs[i + 1], xs[i]

    return xs


def block_shuffle(xs, block_size: int, seed=None):
    """Shuffle the sequence in blocks of specified size."""
    if block_size <= 1:
        return xs[:]  # critical fix: do nothing

    rng = random.Random(seed)
    xs = xs[:]
    n = len(xs)

    blocks = [xs[i : i + block_size] for i in range(0, n, block_size)]

    for i in range(len(blocks) - 1):
        if rng.random() < 0.5:
            blocks[i], blocks[i + 1] = blocks[i + 1], blocks[i]

    return [x for block in blocks for x in block]



def break_runs(xs, every: int):
    """Break monotonic runs by swapping every 'every'-th element with its predecessor."""
    xs = xs[:]
    for i in range(every, len(xs), every):
        xs[i - 1], xs[i] = xs[i], xs[i - 1]
    return xs


def partial_shuffle(xs, ratio: float, seed=None):
    """Randomly shuffle a portion of the sequence defined by ratio."""
    rng = random.Random(seed)
    xs = xs[:]
    n = len(xs)
    k = int(n * ratio)

    indices = rng.sample(range(n), k)
    values = [xs[i] for i in indices]
    rng.shuffle(values)

    for i, v in zip(indices, values):
        xs[i] = v

    return xs

