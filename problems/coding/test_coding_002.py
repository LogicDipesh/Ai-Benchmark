import pytest
from solution import LRUCache


def test_get_empty():
    cache = LRUCache(2)
    assert cache.get(1) == -1


def test_put_and_get():
    cache = LRUCache(2)
    cache.put(1, 10)
    assert cache.get(1) == 10


def test_eviction():
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.get(1)
    cache.put(3, 3)
    assert cache.get(2) == -1
    assert cache.get(1) == 1
    assert cache.get(3) == 3


def test_update_existing():
    # FIXED (was wrong): updating an existing key must NOT evict another
    # key. The old test asserted get(2) == -1 here, which capped every
    # correct LRU implementation at 3/4 = 0.75.
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.put(1, 100)
    assert cache.get(1) == 100
    assert cache.get(2) == 2


def test_update_marks_recent():
    # Updating a key makes it most-recently-used, so the NEXT insertion
    # evicts the other key, not the updated one. This is the behaviour the
    # old test was trying to check, without conflating update and eviction.
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.put(1, 100)
    cache.put(3, 3)
    assert cache.get(2) == -1
    assert cache.get(1) == 100
    assert cache.get(3) == 3
