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
