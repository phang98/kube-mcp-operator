#!/usr/bin/env python3
import re
import sys

ALLOWED_TAGS = ["feat", "fix", "chore", "docs", "refactor", "style", "test"]

PATTERN = re.compile(rf'^({'|'.join(ALLOWED_TAGS)}(\([^\n\r\)]+\))?: .+)')


def main():
    if len(sys.argv) < 2:
        sys.exit(0)
    path = sys.argv[1]
    with open(path, 'r') as f:
        first_line = f.readline().strip()
    if not PATTERN.match(first_line):
        print(
            f"Commit message must start with one of {ALLOWED_TAGS} and follow"
            " the Conventional Commits style.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
