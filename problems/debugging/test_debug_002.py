import pytest
from solution import add_item


def test_add_to_new_list():
    result = add_item(1)
    assert result == [1]


def test_add_to_new_list_again():
    result = add_item(2)
    assert result == [2]


def test_add_to_existing():
    result = add_item(1, [2, 3])
    assert result == [2, 3, 1]


def test_add_to_empty():
    result = add_item(1, [])
    assert result == [1]


def test_independent_calls():
    assert add_item(1) == [1]
    assert add_item(2) == [2]
    assert add_item(3) == [3]
