#!/usr/bin/env python3
"""Safely preview/rename legacy local skill directories before applying the updated overlay.

Does not alter skill content or resolve concurrent edits. No dependencies beyond Python stdlib.
"""
import argparse
import json
from pathlib import Path
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True, help='Existing repository root')
    parser.add_argument('--apply', action='store_true', help='Actually rename directories; default dry-run')
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()
    folder = repo / '.opencode' / 'skills'
    mapping_file = Path(__file__).with_name('skill-rename-map.json')
    mapping = json.loads(mapping_file.read_text())['previous_to_current']
    if folder.is_symlink() or not folder.is_dir():
        print(f'ERROR: no .opencode/skills directory at {repo}', file=sys.stderr)
        return 2
    moves=[]
    conflicts=[]
    for old,new in sorted(mapping.items()):
        src=folder/old; dest=folder/new
        if not src.exists() and not src.is_symlink():
            continue
        if src.is_symlink() or not src.is_dir():
            conflicts.append(f'Unexpected file or symlink: {src}')
        elif dest.exists() or dest.is_symlink():
            conflicts.append(f'Destination already exists: {dest} (source: {src})')
        else:
            moves.append((src,dest))
    if conflicts:
        for msg in conflicts: print('CONFLICT:',msg,file=sys.stderr)
        print('No changes made. Reconcile conflicts manually before migration.',file=sys.stderr)
        return 2
    for src,dest in moves:
        print(('RENAME' if args.apply else 'WOULD RENAME')+f': {src.name} -> {dest.name}')
    if args.apply:
        for src,dest in moves: src.rename(dest)
        print(f'Renamed {len(moves)} directories. Merge the updated overlay NOW to refresh references/frontmatter.')
    else:
        print(f'{len(moves)} proposed moves. Pass --apply only after checking and backing up local changes.')
    return 0

if __name__=='__main__': sys.exit(main())
