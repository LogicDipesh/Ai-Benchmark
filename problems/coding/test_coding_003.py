import pytest
from solution import merge


def test_merge_overlapping():
    result = merge([[1, 3], [2, 6], [8, 10], [15, 18]])
    assert result == [[1, 6], [8, 10], [15, 18]]


def test_merge_adjacent():
    result = merge([[1, 4], [4, 5]])
    assert result == [[1, 5]]


def test_merge_empty():
    assert merge([]) == []


def test_merge_single():
    assert merge([[1, 5]]) == [[1, 5]]


def test_merge_nested():
    result = merge([[1, 5], [2, 3]])
    assert result == [[1, 5]]


def test_merge_unsorted():
    result = merge([[8, 10], [1, 3], [2, 6], [15, 18]])
    assert result == [[1, 6], [8, 10], [15, 18]]
