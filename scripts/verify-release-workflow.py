#!/usr/bin/env python3
"""Guard the independently reviewed write-token workflow against unreviewed drift."""
import hashlib
from pathlib import Path
import sys

EXPECTED = "a0240f8b22c5a6ef925f1bfffdb7f7f5c0276f94ca5d831117a1ed6061a2f6db"

def validate(source):
    if hashlib.sha256(source).hexdigest() != EXPECTED:
        raise ValueError('publication workflow differs from reviewed contract')

if __name__ == '__main__':
    root=Path(__file__).resolve().parent.parent
    try:
        validate((root/'.github/workflows/release.yml').read_bytes())
        print('PASS publication workflow matches reviewed trigger, SHA and permissions')
    except (ValueError,OSError):sys.exit('FAIL publication workflow contract')
