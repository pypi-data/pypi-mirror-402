'Delete paths except those provided as args.'
from argparse import ArgumentParser
from pathlib import Path
from shutil import rmtree
import os, sys

def _log(p):
    print('Delete:', p, file = sys.stderr)

def _rmexcept(leaves):
    def filterdirnames():
        for name in dirnames:
            p = Path(dirpath, name)
            if p in ancestors:
                yield name
            elif p not in leaves:
                _log(p)
                rmtree(p)
    if not leaves:
        _log(os.curdir)
        rmtree(Path.cwd())
        return
    ancestors = set()
    for p in leaves:
        while True:
            p = p.parent
            if not p.parts:
                break
            ancestors.add(p)
    leaves = set(leaves)
    for dirpath, dirnames, filenames in os.walk(os.curdir):
        dirnames[:] = filterdirnames()
        for name in filenames:
            p = Path(dirpath, name)
            if p not in leaves:
                _log(p)
                p.unlink()

def main():
    parser = ArgumentParser()
    parser.add_argument('--open-molly-guard', action = 'store_true')
    parser.add_argument('leaf', type = Path, nargs = '*')
    args = parser.parse_args()
    assert args.open_molly_guard
    _rmexcept(args.leaf)

if '__main__' == __name__:
    main()
