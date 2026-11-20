# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: groq
- Model: openai/gpt-oss-120b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 3969
- Written (UTC): 20261101-191952
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
    original = [1, 2, 3, 4, 5]
    result = dedupe_preserve_order(original)
    assert result == original
    # ensure a new list is returned, not the original object
    assert result is not original


def test_all_duplicates():
    original = ['a', 'a', 'a', 'a']
    assert dedupe_preserve_order(original) == ['a']


def test_mixed_duplicates_preserve_order():
    original = [3, 1, 2, 3, 1, 4, 2, 5]
    expected = [3, 1, 2, 4, 5]
    assert dedupe_preserve_order(original) == expected


def test_with_none_and_false():
    original = [None, False, None, 0, False, 0]
    expected = [None, False, 0]
    assert dedupe_preserve_order(original) == expected


def test_unhashable_item_raises_type_error():
    with pytest.raises(TypeError):
        dedupe_preserve_order([1, [2, 3], 1])


def test_custom_hashable_objects():
    class Item:
        def __init__(self, key):
            self.key = key

        def __hash__(self):
            return hash(self.key)

        def __eq__(self, other):
            return isinstance(other, Item) and self.key == other.key

        def __repr__(self):
            return f"Item({self.key!r})"

    a = Item('x')
    b = Item('y')
    c = Item('x')  # duplicate of a based on key
    d = Item('z')
    original = [a, b, c, d, a]
    result = dedupe_preserve_order(original)
    assert result == [a, b, d]  # c is considered duplicate of a, second a is also duplicate


def test_input_is_not_modified():
    original = [1, 2, 2, 3]
    copy = original.copy()
    dedupe_preserve_order(original)
    assert original == copy
```
```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order

def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_all_unique():
    original = [1, 2, 3, 4, 5]
    result = dedupe_preserve_order(original)
    assert result == original
    # ensure a new list is returned, not the original object
    assert result is not original


def test_all_duplicates():
    original = ['a', 'a', 'a', 'a']
    assert dedupe_preserve_order(original) == ['a']


def test_mixed_duplicates_preserve_order():
    original = [3, 1, 2, 3, 1, 4, 2, 5]
    expected = [3, 1, 2, 4, 5]
    assert dedupe_preserve_order(original) == expected


def test_with_none_and_false():
    original = [None, False, None, 0, False, 0]
    expected = [None, False, 0]
    assert dedupe_preserve_order(original) == expected


def test_unhashable_item_raises_type_error():
    with pytest.raises(TypeError):
        dedupe_preserve_order([1, [2, 3], 1])


def test_custom_hashable_objects():
    class Item:
        def __init__(self, key):
            self.key = key

        def __hash__(self):
            return hash(self.key)

        def __eq__(self, other):
            return isinstance(other, Item) and self.key == other.key

        def __repr__(self):
            return f"Item({self.key!r})"

    a = Item('x')
    b = Item('y')
    c = Item('x')  # duplicate of a based on key
    d = Item('z')
    original = [a, b, c, d, a]
    result = dedupe_preserve_order(original)
    assert result == [a, b, d]  # c is considered duplicate of a, second a is also duplicate


def test_input_is_not_modified():
    original = [1, 2, 2, 3]
    copy = original.copy()
    dedupe_preserve_order(original)
    assert original == copy
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order

def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_all_unique():
    original = [1, 2, 3, 4, 5]
    result = dedupe_preserve_order(original)
    assert result == original
    # ensure a new list is returned, not the original object
    assert result is not original


def test_all_duplicates():
    original = ['a', 'a', 'a', 'a']
    assert dedupe_preserve_order(original) == ['a']


def test_mixed_duplicates_preserve_order():
    original = [3, 1, 2, 3, 1, 4, 2, 5]
    expected = [3, 1, 2, 4, 5]
    assert dedupe_preserve_order(original) == expected


def test_with_none_and_false():
    original = [None, False, None, 0, False, 0]
    expected = [None, False, 0]
    assert dedupe_preserve_order(original) == expected


def test_unhashable_item_raises_type_error():
    with pytest.raises(TypeError):
        dedupe_preserve_order([1, [2, 3], 1])


def test_custom_hashable_objects():
    class Item:
        def __init__(self, key):
            self.key = key

        def __hash__(self):
            return hash(self.key)

        def __eq__(self, other):
            return isinstance(other, Item) and self.key == other.key

        def __repr__(self):
            return f"Item({self.key!r})"

    a = Item('x')
    b = Item('y')
    c = Item('x')  # duplicate of a based on key
    d = Item('z')
    original = [a, b, c, d, a]
    result = dedupe_preserve_order(original)
    assert result == [a, b, d]  # c is considered duplicate of a, second a is also duplicate


def test_input_is_not_modified():
    original = [1, 2, 2, 3]
    copy = original.copy()
    dedupe_preserve_order(original)
    assert original == copy
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
