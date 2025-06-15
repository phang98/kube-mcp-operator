import argparse
import toml

parser = argparse.ArgumentParser(description='Bump project version')
parser.add_argument('level', choices=['major', 'minor', 'patch'], nargs='?', default='patch')
parser.add_argument('--file', default='pyproject.toml')
args = parser.parse_args()

with open(args.file, 'r') as f:
    data = toml.load(f)

version = data['project']['version']
major, minor, patch = map(int, version.split('.'))
if args.level == 'major':
    major += 1
    minor = 0
    patch = 0
elif args.level == 'minor':
    minor += 1
    patch = 0
else:
    patch += 1
new_version = f"{major}.{minor}.{patch}"

data['project']['version'] = new_version
with open(args.file, 'w') as f:
    toml.dump(data, f)

print(new_version)
