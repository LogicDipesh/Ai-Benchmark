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
