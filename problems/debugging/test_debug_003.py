import pytest
import threading
from solution import Counter


def test_single_increment():
    c = Counter()
    assert c.increment() == 1


def test_multiple_increments():
    c = Counter()
    assert c.increment() == 1
    assert c.increment() == 2
    assert c.increment() == 3


def test_concurrent():
    c = Counter()
    threads = [threading.Thread(target=lambda: [c.increment() for _ in range(100)]) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert c._value == 1000


def test_returns_incremented():
    c = Counter()
    assert c.increment() == 1
    assert c.increment() == 2
