# Failure artifact: coding_001_palindrome_linked_list (coding)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: error
- Error: execution_error
- Latency (ms): 40485
- Written (UTC): 20261101-191836
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
def is_palindrome(head):
    if not head or not head.next:
        return True

    # Find the middle of the linked list
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next

    # Reverse the second half
    prev = None
    curr = slow
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt

    # Compare first half and reversed second half
    left = head
    right = prev
    result = True
    while right:
        if left.val != right.val:
            result = False
            break
        left = left.next
        right = right.next

    # Restore the list (optional)
    curr = prev
    prev = None
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt

    return result
```
```

## Executed code

```python
def is_palindrome(head):
    if not head or not head.next:
        return True

    # Find the middle of the linked list
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next

    # Reverse the second half
    prev = None
    curr = slow
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt

    # Compare first half and reversed second half
    left = head
    right = prev
    result = True
    while right:
        if left.val != right.val:
            result = False
            break
        left = left.next
        right = right.next

    # Restore the list (optional)
    curr = prev
    prev = None
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt

    return result
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
