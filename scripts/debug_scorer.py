from aibenchmark.sandbox import run_tests_sandboxed

code = """
def reverse_words(s):
    if not s:
        return \"\"
    words = s.split()
    return \" \".join(reversed(words))
"""

score, status, error = run_tests_sandboxed('problems/coding', code, 'problems/coding/test_coding_001.py')
print(f'Score: {score}, Status: {status}, Error: {error}')