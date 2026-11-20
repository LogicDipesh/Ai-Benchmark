# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: groq
- Model: openai/gpt-oss-120b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 2132
- Written (UTC): 20261031-174422
- Run id: not recorded (evaluators do not receive one); match by timestamp + problem + provider.

## Prompt sent

```
Write comprehensive tests for the following function:

def dedupe_preserve_order(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

The function removes duplicates from a list while preserving
the order of first occurrence. Write tests covering edge cases.
Output only the test code in a Python code block.


Return ONLY one Python code block containing the test code and nothing else. No explanation, no preamble, no text outside the block. Import the function from 'solution' module (e.g., 'from solution import is_valid').
```

## Raw model response

```
```python
import pytest
from solution import dedupe_preserve_order


def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_all_unique():
    lst = [1, 2, 3, 4]
    assert dedupe_preserve_order(lst) == lst


def test_all_duplicates():
    lst = ["a", "a", "a"]
    assert dedupe_preserve_order(lst) == ["a"]


def test_mixed_types():
    lst = [1, "1", 1.0, (2, 3), (2, 3), None, None, True, False, True]
    # 1 and 1.0 compare equal and have the same hash, so they are treated as duplicates.
    expected = [1, "1", (2, 3), None, True, False]
    assert dedupe_preserve_order(lst) == expected


def test_preserves_original_order():
    lst = [5, 3, 5, 2, 3, 1]
    assert dedupe_preserve_order(lst) == [5, 3, 2, 1]


def test_original_list_unchanged():
    lst = [1, 2, 1, 3]
    original = lst[:]
    dedupe_preserve_order(lst)
    assert lst == original


def test_large_input_performance():
    lst = list(range(1000)) + list(range(500))
    result = dedupe_preserve_order(lst)
    assert result == list(range(1000))


def test_unhashable_raises():
    lst = [{}, {}]  # dicts are unhashable
    with pytest.raises(TypeError):
        dedupe_preserve_order(lst)
```

```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order


def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_all_unique():
    lst = [1, 2, 3, 4]
    assert dedupe_preserve_order(lst) == lst


def test_all_duplicates():
    lst = ["a", "a", "a"]
    assert dedupe_preserve_order(lst) == ["a"]


def test_mixed_types():
    lst = [1, "1", 1.0, (2, 3), (2, 3), None, None, True, False, True]
    # 1 and 1.0 compare equal and have the same hash, so they are treated as duplicates.
    expected = [1, "1", (2, 3), None, True, False]
    assert dedupe_preserve_order(lst) == expected


def test_preserves_original_order():
    lst = [5, 3, 5, 2, 3, 1]
    assert dedupe_preserve_order(lst) == [5, 3, 2, 1]


def test_original_list_unchanged():
    lst = [1, 2, 1, 3]
    original = lst[:]
    dedupe_preserve_order(lst)
    assert lst == original


def test_large_input_performance():
    lst = list(range(1000)) + list(range(500))
    result = dedupe_preserve_order(lst)
    assert result == list(range(1000))


def test_unhashable_raises():
    lst = [{}, {}]  # dicts are unhashable
    with pytest.raises(TypeError):
        dedupe_preserve_order(lst)
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order


def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_all_unique():
    lst = [1, 2, 3, 4]
    assert dedupe_preserve_order(lst) == lst


def test_all_duplicates():
    lst = ["a", "a", "a"]
    assert dedupe_preserve_order(lst) == ["a"]


def test_mixed_types():
    lst = [1, "1", 1.0, (2, 3), (2, 3), None, None, True, False, True]
    # 1 and 1.0 compare equal and have the same hash, so they are treated as duplicates.
    expected = [1, "1", (2, 3), None, True, False]
    assert dedupe_preserve_order(lst) == expected


def test_preserves_original_order():
    lst = [5, 3, 5, 2, 3, 1]
    assert dedupe_preserve_order(lst) == [5, 3, 2, 1]


def test_original_list_unchanged():
    lst = [1, 2, 1, 3]
    original = lst[:]
    dedupe_preserve_order(lst)
    assert lst == original


def test_large_input_performance():
    lst = list(range(1000)) + list(range(500))
    result = dedupe_preserve_order(lst)
    assert result == list(range(1000))


def test_unhashable_raises():
    lst = [{}, {}]  # dicts are unhashable
    with pytest.raises(TypeError):
        dedupe_preserve_order(lst)
```

## Reference implementation (what the suite was tested against)

```python
def dedupe_preserve_order(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

```

## Mutants in this problem: mutant_001, mutant_002, mutant_003

## How to reproduce the detail

The bench ran this suite sandboxed: the executed test code was saved as test_generated.py, the reference as solution.py in a solution_dir, and pytest ran with `-v --tb=short` (10 s timeout, Python-level network blocked). First the suite must pass cleanly against the reference, else the row is reference_impl_failed; then each mutant's code replaces solution.py and the suite must fail it to count a kill. To see which mutants survived, re-run the suite above against the reference and then against each mutant from the problem YAML.

Diagnostic only: this file changes no score, no row, and no database entry.
