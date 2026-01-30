from __future__ import annotations
__all__ = ['ContainerStructure']
from collections import deque
from typing import Callable, Generator, Generic, TypeVar
from minfx.neptune_v2.exceptions import MetadataInconsistency
from minfx.neptune_v2.internal.utils.paths import path_to_str
T = TypeVar('T')
Node = TypeVar('Node')

def _default_node_factory(path):
    return {}

class ContainerStructure(Generic[T, Node]):

    def __init__(self, node_factory=None):
        if node_factory is None:
            node_factory = _default_node_factory
        self._structure = node_factory(path=[])
        self._node_factory = node_factory
        self._node_type = type(self._structure)

    def get_structure(self):
        return self._structure

    def _iterate_node(self, node, path_prefix):
        nodes_queue = deque([(node, path_prefix)])
        while nodes_queue:
            node, prefix = nodes_queue.popleft()
            for key, value in node.items():
                if not isinstance(value, self._node_type):
                    yield [*prefix, key]
                else:
                    nodes_queue.append((value, [*prefix, key]))

    def iterate_subpaths(self, path_prefix):
        root = self.get(path_prefix)
        for path in self._iterate_node(root or {}, path_prefix):
            yield path_to_str(path)

    def get(self, path):
        ref = self._structure
        for index, part in enumerate(path):
            if not isinstance(ref, self._node_type):
                raise MetadataInconsistency(f"Cannot access path '{path_to_str(path)}': '{path_to_str(path[:index])}' is already defined as an attribute, not a namespace")
            if part not in ref:
                return None
            ref = ref[part]
        return ref

    def set(self, path, attr):
        ref = self._structure
        location, attribute_name = (path[:-1], path[-1])
        for idx, part in enumerate(location):
            if part not in ref:
                ref[part] = self._node_factory(location[:idx + 1])
            ref = ref[part]
            if not isinstance(ref, self._node_type):
                raise MetadataInconsistency(f"Cannot access path '{path_to_str(path)}': '{part}' is already defined as an attribute, not a namespace")
        if attribute_name in ref and isinstance(ref[attribute_name], self._node_type):
            if isinstance(attr, self._node_type):
                return
            raise MetadataInconsistency(f"Cannot set attribute '{path_to_str(path)}'. It's a namespace")
        ref[attribute_name] = attr

    def pop(self, path):
        self._pop_impl(self._structure, path, path)

    def _pop_impl(self, ref, sub_path, attr_path):
        if not sub_path:
            return
        head, tail = (sub_path[0], sub_path[1:])
        if head not in ref:
            raise MetadataInconsistency(f'Cannot delete {path_to_str(attr_path)}. Attribute not found.')
        if not tail:
            if isinstance(ref[head], self._node_type):
                raise MetadataInconsistency(f"Cannot delete {path_to_str(attr_path)}. It's a namespace, not an attribute.")
            del ref[head]
        else:
            self._pop_impl(ref[head], tail, attr_path)
            if not ref[head]:
                del ref[head]

    def clear(self):
        self._structure.clear()