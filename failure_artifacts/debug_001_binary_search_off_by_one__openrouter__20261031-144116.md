# Failure artifact: debug_001_binary_search_off_by_one (debugging)

- Provider: openrouter
- Model: cohere/north-mini-code:free
- Score: 0.0
- Status: error
- Error: execution_error; truncated_at_cap
- Latency (ms): 62664
- Written (UTC): 20261031-144116
- Run id: not recorded (evaluators do not receive one); match by timestamp + problem + provider.
- Test file on disk: problems/debugging/test_debug_001.py

## Prompt sent

```
Fix the bug in the following binary search implementation.
The function should return the index of `target` in a sorted array,
or -1 if the target is not found. The bug causes it to miss some
valid targets.


Broken code:
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return -1


Return ONLY one Python code block and nothing else. No explanation, no preamble, no tests, no text outside the block.
```

## Raw model response

```

```

## Executed code

```python

```

## Test file content

```python
import pytest
from solution import binary_search


def test_found_at_start():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0


def test_found_in_middle():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2


def test_found_at_end():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4


def test_not_found():
    assert binary_search([1, 2, 3, 4, 5], 6) == -1


def test_empty():
    assert binary_search([], 1) == -1


def test_single_found():
    assert binary_search([5], 5) == 0


def test_single_not_found():
    assert binary_search([5], 3) == -1

```

## How to reproduce the detail

The bench ran this code sandboxed: it was saved as solution.py next to the test file (copied as test_solution.py) in a fresh temp dir, then `python -m pytest test_solution.py -v --tb=short` with a 10 s timeout and Python-level network blocked. To see the per-test detail the row does not carry, save the executed code above as solution.py, copy the test file next to it as test_solution.py, and run the same pytest command. If the failure was sandbox_timeout, run with a timeout: without the sandbox, a hanging solution hangs instead of timing out.

Diagnostic only: this file changes no score, no row, and no database entry.
