from aibenchmark.sandbox import run_tests_sandboxed

# Correct implementation for the palindrome linked list problem
code = """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def is_palindrome(head):
    if not head:
        return True
    vals = []
    while head:
        vals.append(head.val)
        head = head.next
    return vals == vals[::-1]
"""

score, status, error = run_tests_sandboxed('problems/coding', code, 'problems/coding/test_coding_001.py')
print(f'Score: {score}, Status: {status}, Error: {error}')

# Test with wrong code
wrong_code = """
def is_palindrome(head):
    return False
"""

score, status, error = run_tests_sandboxed('problems/coding', wrong_code, 'problems/coding/test_coding_001.py')
print(f'Wrong code - Score: {score}, Status: {status}, Error: {error}')

# Empty code
empty_code = ""
score, status, error = run_tests_sandboxed('problems/coding', empty_code, 'problems/coding/test_coding_001.py')
print(f'Empty - Score: {score}, Status: {status}, Error: {error}')

# With markdown
md_code = '''
Here is the solution:
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def is_palindrome(head):
    if not head:
        return True
    vals = []
    while head:
        vals.append(head.val)
        head = head.next
    return vals == vals[::-1]
```
'''
from aibenchmark.sandbox import extract_code
extracted = extract_code(md_code)
score, status, error = run_tests_sandboxed('problems/coding', extracted, 'problems/coding/test_coding_001.py')
print(f'Markdown - Score: {score}, Status: {status}, Error: {error}')