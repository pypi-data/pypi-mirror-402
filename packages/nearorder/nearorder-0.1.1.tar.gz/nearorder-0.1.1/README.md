# nearorder 

![codecov](https://codecov.io/gh/SHIINASAMA/nearorder/branch/main/graph/badge.svg)

`nearorder` is an experimental project for validating search strategies on mostly ordered sequences with sparse disorder, focusing on performance stability, fallback behavior, and long-term robustness.

## Key words

- experimental / validation

- mostly ordered

- sparse disorder

- performance stability / fallback

## Motivation

In many real-world engineering systems, the data being queried is **not fully sorted**, but it is also **far from being randomly disordered**.

The assumptions behind this project are based on practical observations rather than theoretical worst-case models:

-   The sequence is **globally monotonic** (ascending or descending as a whole).
    
-   Disorder exists, but it is **sparse and limited**.
    
-   Disordered elements:
    
    -   Are **few in number**
        
    -   Are **randomly distributed**
        
    -   Do **not cluster densely within a single local interval**
        
-   Data repair or correction is **post-hoc and relatively slow**.
    
-   Query operations are **high-frequency and performance-critical**.
    

Under these conditions, traditional binary search may fail or behave unpredictably when encountering local disorder, while linear scans are prohibitively expensive at scale.

This project does **not** attempt to design a universally optimal algorithm for arbitrary input.  
Instead, it focuses on **validating search strategies under realistic engineering assumptions**, where:

-   Correctness must be preserved
    
-   Performance degradation must be bounded and observable
    
-   Long-term stability is more important than theoretical optimality
    

In short, this is an **experiment-driven validation of a “good enough” solution under constrained, real-world disorder**, rather than a general-purpose algorithmic framework.

## Performance Analysis Summary

The experimental results in `analysis/` and `test/` consistently fall into four representative cases:

### 1\. Sparse Random Swaps (Low Disorder, The data the author has direct access to in practice.)

![](./analysis/image/1.vs.swap_count.png)

**Conclusion:**  
Performance remains stable and close to the ordered case; limited swaps do not meaningfully affect query time.

### 2\. Block-Level Disorder

![](./analysis/image/2.vs.block-size.png)

**Conclusion:**  
Spikes occur sporadically, but the average time doesn't show a clear increase or decrease with larger block sizes; it stays mostly flat with noise.

### 3\. Periodic Local Disorder

![](./analysis/image/3.vs.break_every.png)

**Conclusion:** 
The spikes suggest specific points where performance degrades notably, likely due to alignment issues, while average performance appears stable.

### 4\. Periodic Shuffle

![](./analysis/image/4.vs.partial_shuffle_ratio.png)

**Conclusion:**  
There's a noticeable increase in both average time and spike severity as disorder grows, peaking in intermediates before stabilizing somewhat at extremes.

### Overall Observation

At the 10⁵ scale, variations caused by reasonable levels of in-sequence disorder stay within a narrow and predictable performance range, making the approach suitable for long-term operation on mostly ordered data.

## Recommended Usage Pattern

For the type of data discussed above, a **two-phase search strategy** is recommended.

1.  **Phase One: Coarse Binary Search**  
    Apply binary search with **looser and more tolerant conditions** to obtain a *coarse* or *approximate index*.  
    At this stage, the goal is localization rather than exact matching.
    
2.  **Phase Two: Window-Based Refinement**  
    Using the coarse index as an anchor, collect data within a bounded window and perform targeted filtering and validation inside this range.


```python
from datetime import datetime

from nearorder.bisect import binary_search
from nearorder.filter import filter_window


def cmp(a: datetime, b: datetime) -> int:
    def datetime_to_days(dt: datetime) -> int:
        return (dt - datetime(1900, 1, 1)).days + 2

    rt = datetime_to_days(a) - datetime_to_days(b)
    return int(rt)


def cmp_precise(a: datetime, b: datetime) -> int:
    rt = a.timestamp() - b.timestamp()
    return int(rt)


index = binary_search(data, k, cmp=cmp)
assert index is not None
result = filter_window(data, k, index, window_size=24 * 4, cmp=cmp_precise)
assert len(result) > 0

```

## What This Project Is / Is Not

This project is:

- A validation of assumptions

- A performance experiment

- A reference implementation

This project is **NOT**:

- A general-purpose sorting library

- A theoretically optimal algorithm for arbitrary input

- A drop-in replacement for standard search

## License

Copyright (c) 2026 SHIINASAMA (Kaoru).  

This project is licensed under the MIT License. See the LICENSE file for details.