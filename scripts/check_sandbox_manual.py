from aibenchmark.sandbox import run_tests_sandboxed

code = '''
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def is_palindrome(head):
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    return vals == vals[::-1]
'''

score, status, error = run_tests_sandboxed(
    "problems/coding", code, "problems/coding/test_coding_001.py"
)
print(score, status, error)
