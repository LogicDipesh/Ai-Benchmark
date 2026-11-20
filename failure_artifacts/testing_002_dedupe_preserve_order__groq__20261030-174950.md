# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: groq
- Model: openai/gpt-oss-120b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 2088
- Written (UTC): 20261030-174950
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

@pytest.mark.parametrize(
    "input_list, expected",
    [
        ([], []),  # empty list
        ([1, 2, 3, 4], [1, 2, 3, 4]),  # no duplicates
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([1, 2, 1, 3, 2, 4, 3], [1, 2, 3, 4]),  # interleaved duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        (["a", 1, "a", 1, (2, 3), (2, 3)], ["a", 1, (2, 3)]),  # mixed hashable types
        ([None, None, 0, False, 0], [None, 0, False]),  # falsy values
        (list(range(1000)) + list(range(500)), list(range(1000))),  # large list with partial overlap
    ],
)
def test_dedupe_preserve_order_various_cases(input_list, expected):
    """Verify deduplication and order preservation across typical scenarios."""
    result = dedupe_preserve_order(input_list)
    assert result == expected
    # Ensure the original list is unchanged
    assert input_list == input_list[:]  # simple identity check for immutability


def test_original_list_not_modified():
    """The function should not mutate its argument."""
    original = [1, 2, 2, 3]
    copy = original.copy()
    dedupe_preserve_order(original)
    assert original == copy


@pytest.mark.parametrize(
    "unhashable_item",
    [
        [1, 2],          # list
        {"a": 1},        # dict
        set([1, 2]),     # set
        bytearray(b"ab") # bytearray
    ],
)
def test_unhashable_items_raise_type_error(unhashable_item):
    """Passing unhashable items should raise a TypeError."""
    with pytest.raises(TypeError):
        dedupe_preserve_order([unhashable_item, unhashable_item])


def test_custom_hashable_object():
    """Objects with custom __hash__ and __eq__ should be deduped correctly."""
    class Item:
        def __init__(self, value):
            self.value = value

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return isinstance(other, Item) and self.value == other.value

        def __repr__(self):
            return f"Item({self.value!r})"

    a = Item(1)
    b = Item(1)
    c = Item(2)
    d = Item(1)
    result = dedupe_preserve_order([a, b, c, d])
    assert result == [a, c]  # b and d are considered duplicates of a
```
```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list, expected",
    [
        ([], []),  # empty list
        ([1, 2, 3, 4], [1, 2, 3, 4]),  # no duplicates
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([1, 2, 1, 3, 2, 4, 3], [1, 2, 3, 4]),  # interleaved duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        (["a", 1, "a", 1, (2, 3), (2, 3)], ["a", 1, (2, 3)]),  # mixed hashable types
        ([None, None, 0, False, 0], [None, 0, False]),  # falsy values
        (list(range(1000)) + list(range(500)), list(range(1000))),  # large list with partial overlap
    ],
)
def test_dedupe_preserve_order_various_cases(input_list, expected):
    """Verify deduplication and order preservation across typical scenarios."""
    result = dedupe_preserve_order(input_list)
    assert result == expected
    # Ensure the original list is unchanged
    assert input_list == input_list[:]  # simple identity check for immutability


def test_original_list_not_modified():
    """The function should not mutate its argument."""
    original = [1, 2, 2, 3]
    copy = original.copy()
    dedupe_preserve_order(original)
    assert original == copy


@pytest.mark.parametrize(
    "unhashable_item",
    [
        [1, 2],          # list
        {"a": 1},        # dict
        set([1, 2]),     # set
        bytearray(b"ab") # bytearray
    ],
)
def test_unhashable_items_raise_type_error(unhashable_item):
    """Passing unhashable items should raise a TypeError."""
    with pytest.raises(TypeError):
        dedupe_preserve_order([unhashable_item, unhashable_item])


def test_custom_hashable_object():
    """Objects with custom __hash__ and __eq__ should be deduped correctly."""
    class Item:
        def __init__(self, value):
            self.value = value

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return isinstance(other, Item) and self.value == other.value

        def __repr__(self):
            return f"Item({self.value!r})"

    a = Item(1)
    b = Item(1)
    c = Item(2)
    d = Item(1)
    result = dedupe_preserve_order([a, b, c, d])
    assert result == [a, c]  # b and d are considered duplicates of a
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list, expected",
    [
        ([], []),  # empty list
        ([1, 2, 3, 4], [1, 2, 3, 4]),  # no duplicates
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([1, 2, 1, 3, 2, 4, 3], [1, 2, 3, 4]),  # interleaved duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        (["a", 1, "a", 1, (2, 3), (2, 3)], ["a", 1, (2, 3)]),  # mixed hashable types
        ([None, None, 0, False, 0], [None, 0, False]),  # falsy values
        (list(range(1000)) + list(range(500)), list(range(1000))),  # large list with partial overlap
    ],
)
def test_dedupe_preserve_order_various_cases(input_list, expected):
    """Verify deduplication and order preservation across typical scenarios."""
    result = dedupe_preserve_order(input_list)
    assert result == expected
    # Ensure the original list is unchanged
    assert input_list == input_list[:]  # simple identity check for immutability


def test_original_list_not_modified():
    """The function should not mutate its argument."""
    original = [1, 2, 2, 3]
    copy = original.copy()
    dedupe_preserve_order(original)
    assert original == copy


@pytest.mark.parametrize(
    "unhashable_item",
    [
        [1, 2],          # list
        {"a": 1},        # dict
        set([1, 2]),     # set
        bytearray(b"ab") # bytearray
    ],
)
def test_unhashable_items_raise_type_error(unhashable_item):
    """Passing unhashable items should raise a TypeError."""
    with pytest.raises(TypeError):
        dedupe_preserve_order([unhashable_item, unhashable_item])


def test_custom_hashable_object():
    """Objects with custom __hash__ and __eq__ should be deduped correctly."""
    class Item:
        def __init__(self, value):
            self.value = value

        def __hash__(self):
            return hash(self.value)

        def __eq__(self, other):
            return isinstance(other, Item) and self.value == other.value

        def __repr__(self):
            return f"Item({self.value!r})"

    a = Item(1)
    b = Item(1)
    c = Item(2)
    d = Item(1)
    result = dedupe_preserve_order([a, b, c, d])
    assert result == [a, c]  # b and d are considered duplicates of a
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
