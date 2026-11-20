"""Scan the project for possible hard-coded secrets.

Changed from the original root version in one way only: it NEVER prints
a matched value, only the file name, the pattern type, and how many
matches were found. The original printed the matches themselves, which
would leak a key into terminal output / logs if one was ever found.

Run from the project root (this script uses the project root as its
starting point; edit ROOT_PATH if your project lives elsewhere).
"""
import os
import re

# Project root is two levels up from scripts/: scripts/check_secrets.py
# -> project root. Run this script from anywhere; it does not depend on
# the current working directory.
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATTERNS = {
    "sk-... token": re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    "api_key assignment": re.compile(
        r"api[_-]?key\s*[:=]\s*['\"][^'\"]{10,}['\"]", re.IGNORECASE
    ),
}

for root, dirs, files in os.walk(ROOT_PATH):
    # Skip generated / ignored folders.
    dirs[:] = [
        d
        for d in dirs
        if d not in ("__pycache__", ".pytest_cache", ".venv", "venv")
        and not d.endswith(".egg-info")
    ]
    for name in files:
        if not name.endswith((".py", ".yaml", ".md", ".txt", ".toml")):
            continue
        path = os.path.join(root, name)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
        except OSError:
            continue
        for label, pattern in PATTERNS.items():
            count = len(pattern.findall(content))
            if count:
                print(f"Potential key ({label}) in {path}: {count} match(es) "
                      f"[value hidden -- inspect the file yourself]")
