from __future__ import annotations
__all__ = ['sha1']
import hashlib
from pathlib import Path
import typing

def sha1(fname, block_size=2 ** 16):
    sha1sum = hashlib.sha1()
    with Path(fname).open('rb') as source:
        block = source.read(block_size)
        while len(block) != 0:
            sha1sum.update(block)
            block = source.read(block_size)
    return str(sha1sum.hexdigest())