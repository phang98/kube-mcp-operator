import os
import subprocess
import sys

version = sys.argv[1]
msg = subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode().strip()

entry = f"## {version}\n\n{msg}\n\n"

if os.path.exists('CHANGELOG.md'):
    with open('CHANGELOG.md', 'r') as f:
        existing = f.read()
else:
    existing = ''

with open('CHANGELOG.md', 'w') as f:
    f.write(entry + existing)
