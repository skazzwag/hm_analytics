#!/usr/bin/env python3
"""List bundled OpenCode skill IDs by primary tool; no external runtime/dependencies."""
import argparse
import json
from pathlib import Path
import re
import sys


def inventory(root):
    base = root / '.opencode' / 'skills'
    if not base.is_dir(): raise FileNotFoundError(base)
    found=[]
    for folder in sorted(base.iterdir()):
        entry=folder/'SKILL.md'
        if not folder.is_dir() or not entry.is_file(): continue
        match=re.search(r'^name:\s*[\"\']?([^\"\'\n]+)',entry.read_text(), re.M)
        name=match.group(1).strip() if match else None
        prefix=folder.name.split('-',1)[0]
        found.append({'tool':prefix,'id':folder.name,'name':name,'matches':name==folder.name})
    return found


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd(),help='Repository root')
    parser.add_argument('--json',action='store_true',help='Machine-readable inventory')
    args=parser.parse_args(argv)
    try: rows=inventory(args.root.resolve())
    except FileNotFoundError as err:
        print(f'Missing: {err}',file=sys.stderr); return 2
    if args.json:
        print(json.dumps(rows,indent=2))
    else:
        print('| Tool | Skill ID | Entry matches directory? |')
        print('|---|---|---|')
        for item in rows:
            print(f'| {item["tool"]} | `{item["id"]}` | {"yes" if item["matches"] else "NO"} |')
    return 0 if all(x['matches'] for x in rows) else 2

if __name__=='__main__': sys.exit(main())
