# Failure artifact: debug_003_race_condition (debugging)

- Provider: openrouter
- Model: cohere/north-mini-code:free
- Score: 0.0
- Status: error
- Error: execution_error; truncated_at_cap
- Latency (ms): 74399
- Written (UTC): 20261031-144145
- Run id: not recorded (evaluators do not receive one); match by timestamp + problem + provider.
- Test file on disk: problems/debugging/test_debug_003.py

## Prompt sent

```
Fix the race condition in the following thread-safe counter.
The counter is not thread-safe despite the lock; identify and fix
the issue so concurrent increments produce correct results.


Broken code:
import threading

class Counter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self):
        self._lock.acquire()
        current = self._value
        self._value = current + 1
        return self._value


Return ONLY one Python code block and nothing else. No explanation, no preamble, no tests, no text outside the block.
```

## Raw model response

```

```

## Executed code

```python

```

## Test file content

```python
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

```

## How to reproduce the detail

The bench ran this code sandboxed: it was saved as solution.py next to the test file (copied as test_solution.py) in a fresh temp dir, then `python -m pytest test_solution.py -v --tb=short` with a 10 s timeout and Python-level network blocked. To see the per-test detail the row does not carry, save the executed code above as solution.py, copy the test file next to it as test_solution.py, and run the same pytest command. If the failure was sandbox_timeout, run with a timeout: without the sandbox, a hanging solution hangs instead of timing out.

Diagnostic only: this file changes no score, no row, and no database entry.
