"""Fetch only pinned public text files; verify bytes before extracting cases."""
import hashlib
import argparse
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--round2',action='store_true',help='Fetch the separate untouched second corpus')
    args=parser.parse_args()
    records = json.loads((ROOT / ('validation/round2-sources.json' if args.round2 else 'validation/sources.json')).read_text())
    destination = ROOT / ('reports/real-world-validation-round2/sources' if args.round2 else 'reports/real-world-validation/sources')
    destination.mkdir(parents=True, exist_ok=True)
    for record in records:
        assert record['url'].startswith('https://raw.githubusercontent.com/')
        content = urlopen(record['url'], timeout=30).read()
        assert hashlib.sha256(content).hexdigest() == record['sha256'], 'Upstream bytes changed'
        name = record['repository'].split('/')[1]
        path = destination / Path(record['path']).name if args.round2 else destination / name / record['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        (destination / (name + '-tree.json')).write_text(json.dumps({'sha': record['revision']}))
    (destination / 'downloads.json').write_text(json.dumps(records, indent=2)+'\n')
    print('Verified', len(records), 'public source/license files. No upstream code executed.')


if __name__ == '__main__':
    main()
