# Failure artifact: coding_001_palindrome_linked_list (coding)

- Provider: openrouter
- Model: cohere/north-mini-code:free
- Score: 0.0
- Status: error
- Error: execution_error; truncated_at_cap
- Latency (ms): 64754
- Written (UTC): 20261030-174937
- Run id: not recorded (evaluators do not receive one); match by timestamp + problem + provider.
- Test file on disk: problems/coding/test_coding_001.py

## Prompt sent

```
Implement a function `is_palindrome(head)` that checks if a singly
linked list is a palindrome. The linked list node is defined as:

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

Return True if the linked list is a palindrome, False otherwise.

You must implement the solution in a file called solution.py.
Return only a single Python code block, no prose.


Return ONLY one Python code block and nothing else. No explanation, no preamble, no tests, no text outside the block.
```

## Raw model response

```
```python
class ListNode:
    def __init__(self, val=0, next=None
```

## Executed code

```python
```python
class ListNode:
    def __init__(self, val=0, next=None
```

## Test file content

```python
import pytest
from solution import is_palindrome, ListNode


def make_list(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def test_empty_list():
    assert is_palindrome(None) is True


def test_single_node():
    assert is_palindrome(ListNode(1)) is True


def test_two_same():
    head = ListNode(1, ListNode(1))
    assert is_palindrome(head) is True


def test_two_different():
    head = ListNode(1, ListNode(2))
    assert is_palindrome(head) is False


def test_palindrome_odd():
    head = make_list([1, 2, 3, 2, 1])
    assert is_palindrome(head) is True


def test_palindrome_even():
    head = make_list([1, 2, 2, 1])
    assert is_palindrome(head) is True


def test_non_palindrome():
    head = make_list([1, 2, 3, 4, 5])
    assert is_palindrome(head) is False

```

## How to reproduce the detail

The bench ran this code sandboxed: it was saved as solution.py next to the test file (copied as test_solution.py) in a fresh temp dir, then `python -m pytest test_solution.py -v --tb=short` with a 10 s timeout and Python-level network blocked. To see the per-test detail the row does not carry, save the executed code above as solution.py, copy the test file next to it as test_solution.py, and run the same pytest command. If the failure was sandbox_timeout, run with a timeout: without the sandbox, a hanging solution hangs instead of timing out.

Diagnostic only: this file changes no score, no row, and no database entry.
