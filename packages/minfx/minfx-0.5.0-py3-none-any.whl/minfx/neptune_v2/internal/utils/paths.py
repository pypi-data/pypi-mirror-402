from __future__ import annotations
__all__ = ['join_paths', 'parse_path', 'path_to_str']

def _remove_empty_paths(paths):
    return list(filter(bool, paths))

def parse_path(path):
    return _remove_empty_paths(str(path).split('/'))

def path_to_str(path):
    return '/'.join(_remove_empty_paths(path))

def join_paths(*paths):
    return '/'.join(_remove_empty_paths([str(path) for path in paths]))