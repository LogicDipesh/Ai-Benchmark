import tempfile, os, shutil
from aibenchmark.sandbox import _write_sitecustomize, _run_pytest

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

with tempfile.TemporaryDirectory() as tmpdir:
    with open(os.path.join(tmpdir, "solution.py"), "w") as f:
        f.write(code)
    shutil.copy("problems/coding/test_coding_001.py", os.path.join(tmpdir, "test_solution.py"))
    _write_sitecustomize(tmpdir)
    try:
        rc, output, passed, failed, errors = _run_pytest(tmpdir, "test_solution.py", tmpdir)
        print("returncode:", rc)
        print("passed/failed/errors:", passed, failed, errors)
        print("---- pytest output ----")
        print(output)
    except Exception as e:
        print("EXCEPTION:", type(e).__name__, e)
