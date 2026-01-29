from __future__ import annotations

import copy
from collections.abc import Iterable, Iterator
from typing import cast, overload

from typing_extensions import Self, override

from . import abcs, binary
from .hints import KeyT, ValueT
from .nil import NIL, Nil
from .utils import to_unique_sorted_items, to_unique_sorted_values

Node = binary.Node


class Tree(abcs.Tree[KeyT, ValueT]):
    @overload
    @classmethod
    def from_components(
        cls: type[Tree[KeyT, KeyT]],
        keys: Iterable[KeyT],
        values: None = ...,
        /,
    ) -> Tree[KeyT, KeyT]: ...

    @overload
    @classmethod
    def from_components(
        cls, keys: Iterable[KeyT], values: Iterable[ValueT], /
    ) -> Self: ...

    @classmethod
    def from_components(
        cls: type[Tree[KeyT, KeyT]] | type[Tree[KeyT, ValueT]],
        keys: Iterable[KeyT],
        values: Iterable[ValueT] | None = None,
        /,
    ) -> Tree[KeyT, KeyT] | Tree[KeyT, ValueT]:
        keys = list(keys)
        if not keys:
            return cls(NIL)
        if values is None:
            keys = to_unique_sorted_values(keys)

            def to_simple_node(
                start_index: int, end_index: int
            ) -> Node[KeyT, KeyT]:
                middle_index = (start_index + end_index) // 2
                key = keys[middle_index]
                return Node(
                    key,
                    key,
                    left=(
                        to_simple_node(start_index, middle_index)
                        if middle_index > start_index
                        else NIL
                    ),
                    right=(
                        to_simple_node(middle_index + 1, end_index)
                        if middle_index < end_index - 1
                        else NIL
                    ),
                )

            return cast(type[Tree[KeyT, KeyT]], cls)(
                to_simple_node(0, len(keys))
            )
        items = to_unique_sorted_items(keys, tuple(values))

        def to_complex_node(
            start_index: int, end_index: int, /
        ) -> Node[KeyT, ValueT]:
            middle_index = (start_index + end_index) // 2
            key, value = items[middle_index]
            return Node(
                key,
                value,
                left=(
                    to_complex_node(start_index, middle_index)
                    if middle_index > start_index
                    else NIL
                ),
                right=(
                    to_complex_node(middle_index + 1, end_index)
                    if middle_index < end_index - 1
                    else NIL
                ),
            )

        return cast(type[Tree[KeyT, ValueT]], cls)(
            to_complex_node(0, len(items))
        )

    @property
    @override
    def root(self, /) -> Node[KeyT, ValueT] | Nil:
        return self._root

    @override
    def clear(self, /) -> None:
        self._root = NIL

    @override
    def find(self, key: KeyT, /) -> Node[KeyT, ValueT] | Nil:
        if self._root is NIL:
            return NIL
        self._splay(key)
        root = self._root
        return NIL if key < root.key or root.key < key else root

    @override
    def insert(self, key: KeyT, value: ValueT, /) -> Node[KeyT, ValueT]:
        if self._root is NIL:
            node = self._root = Node(key, value)
            return node
        self._splay(key)
        if key < self._root.key:
            self._root.left, self._root = (
                NIL,
                Node(key, value, left=self._root.left, right=self._root),
            )
        elif self._root.key < key:
            self._root.right, self._root = (
                NIL,
                Node(key, value, left=self._root, right=self._root.right),
            )
        return self._root

    @override
    def max(self, /) -> Node[KeyT, ValueT] | Nil:
        node = self._root
        if node is not NIL:
            while node.right is not NIL:
                node = node.right
            self._splay(node.key)
        return node

    @override
    def min(self, /) -> Node[KeyT, ValueT] | Nil:
        node = self._root
        if node is not NIL:
            while node.left is not NIL:
                node = node.left
            self._splay(node.key)
        return node

    @override
    def popmax(self, /) -> Node[KeyT, ValueT] | Nil:
        if self._root is NIL:
            return self._root
        result = self.max()
        self._remove_root()
        return result

    @override
    def popmin(self, /) -> Node[KeyT, ValueT] | Nil:
        if self._root is NIL:
            return self._root
        result = self.min()
        self._remove_root()
        return result

    @override
    def predecessor(
        self, node: abcs.Node[KeyT, ValueT], /
    ) -> Node[KeyT, ValueT] | Nil:
        result: Node[KeyT, ValueT] | Nil
        assert isinstance(node, Node), node
        if node.left is not NIL:
            result = node.left
            while result.right is not NIL:
                result = result.right
        else:
            result, cursor, key = NIL, self._root, node.key
            while cursor is not node:
                assert cursor is not NIL
                if cursor.key < key:
                    result, cursor = cursor, cursor.right
                else:
                    cursor = cursor.left
        if result is not NIL:
            self._splay(result.key)
        return result

    @override
    def remove(self, node: abcs.Node[KeyT, ValueT], /) -> None:
        assert isinstance(node, Node), node
        self._splay(node.key)
        self._remove_root()

    @override
    def successor(
        self, node: abcs.Node[KeyT, ValueT], /
    ) -> Node[KeyT, ValueT] | Nil:
        assert isinstance(node, Node), node
        result: Node[KeyT, ValueT] | Nil
        if node.right is not NIL:
            result = node.right
            while result.left is not NIL:
                result = result.left
        else:
            result, cursor, key = NIL, self._root, node.key
            while cursor is not node:
                assert cursor is not NIL
                if key < cursor.key:
                    result, cursor = cursor, cursor.left
                else:
                    cursor = cursor.right
        if result is not NIL:
            self._splay(result.key)
        return result

    @staticmethod
    def _rotate_left(node: Node[KeyT, ValueT], /) -> Node[KeyT, ValueT]:
        replacement = node.right
        assert replacement is not NIL
        node.right, replacement.left = replacement.left, node
        return replacement

    @staticmethod
    def _rotate_right(node: Node[KeyT, ValueT], /) -> Node[KeyT, ValueT]:
        replacement = node.left
        assert replacement is not NIL
        node.left, replacement.right = replacement.right, node
        return replacement

    def _remove_root(self, /) -> None:
        root = self._root
        assert root is not NIL
        if root.left is NIL:
            self._root = root.right
        else:
            right_root_child = root.right
            self._root = root.left
            self._splay(root.key)
            self._root.right = right_root_child

    def _splay(self, key: KeyT, /) -> None:
        next_root = self._root
        next_root_left_child = next_root_right_child = self._header
        while True:
            assert next_root is not NIL
            if key < next_root.key:
                if next_root.left is NIL:
                    break
                if key < next_root.left.key:
                    next_root = self._rotate_right(next_root)
                    if next_root.left is NIL:
                        break
                next_root_right_child.left = next_root
                next_root_right_child, next_root = next_root, next_root.left
            elif next_root.key < key:
                if next_root.right is NIL:
                    break
                if next_root.right.key < key:
                    next_root = self._rotate_left(next_root)
                    if next_root.right is NIL:
                        break
                next_root_left_child.right = next_root
                next_root_left_child, next_root = next_root, next_root.right
            else:
                break
        next_root_left_child.right, next_root_right_child.left = (
            next_root.left,
            next_root.right,
        )
        next_root.left, next_root.right = self._header.right, self._header.left
        self._root = next_root

    _header: Node[KeyT, ValueT]
    _root: Node[KeyT, ValueT] | Nil

    __slots__ = '_header', '_root'

    @override
    def __copy__(self, /) -> Self:
        return type(self)(copy.deepcopy(self._root))

    def __init__(self, root: Node[KeyT, ValueT] | Nil, /) -> None:
        self._root = root
        self._header = Node(NotImplemented, NotImplemented)

    def __iter__(self, /) -> Iterator[Node[KeyT, ValueT]]:
        # we are collecting all values at once
        # because tree can be implicitly changed during iteration
        # (e.g. by simple lookup)
        # and cause infinite loops
        return cast(
            Iterator[Node[KeyT, ValueT]], iter(list(super().__iter__()))
        )

    def __reversed__(self, /) -> Iterator[Node[KeyT, ValueT]]:
        # we are collecting all values at once
        # because tree can be implicitly changed during iteration
        # (e.g. by simple lookup)
        # and cause infinite loops
        return cast(
            Iterator[Node[KeyT, ValueT]], iter(list(super().__reversed__()))
        )
