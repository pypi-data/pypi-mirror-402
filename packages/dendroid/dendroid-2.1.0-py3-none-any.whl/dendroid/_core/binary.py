from __future__ import annotations

import copy
from collections.abc import Iterable
from typing import Generic, cast, overload

from reprit.base import generate_repr
from typing_extensions import Self, override

from . import abcs
from .hints import Item, KeyT, ValueT
from .nil import NIL, Nil
from .utils import (
    are_keys_equal,
    to_unique_sorted_items,
    to_unique_sorted_values,
)


class Node(abcs.HasCustomRepr, Generic[KeyT, ValueT]):
    @property
    def item(self, /) -> Item[KeyT, ValueT]:
        return self.key, self.value

    @property
    def key(self, /) -> KeyT:
        return self._key

    @property
    def left(self, /) -> Self | Nil:
        return self._left

    @left.setter
    def left(self, value: Self | Nil, /) -> None:
        self._left = value

    @property
    def right(self, /) -> Self | Nil:
        return self._right

    @right.setter
    def right(self, value: Self | Nil) -> None:
        self._right = value

    @property
    def value(self, /) -> ValueT:
        return self._value

    @value.setter
    def value(self, value: ValueT) -> None:
        self._value = value

    _left: Self | Nil
    _right: Self | Nil

    __slots__ = '_key', '_left', '_right', '_value'

    def __init__(
        self,
        key: KeyT,
        value: ValueT,
        /,
        *,
        left: Self | Nil = NIL,
        right: Self | Nil = NIL,
    ) -> None:
        self._key, self._value, self._left, self._right = (
            key,
            value,
            left,
            right,
        )

    __repr__ = generate_repr(__init__)


class Tree(abcs.Tree[KeyT, ValueT]):
    @overload
    @classmethod
    def from_components(
        cls, keys: Iterable[KeyT], values: None = ..., /
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
                start_index: int, end_index: int, /
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
    def root(self, /) -> Node[KeyT, ValueT] | Nil:
        return self._root

    @override
    def clear(self, /) -> None:
        self._root = NIL

    @override
    def insert(self, key: KeyT, value: ValueT, /) -> Node[KeyT, ValueT]:
        parent = self._root
        if parent is NIL:
            node = self._root = Node(key, value)
            return node
        while True:
            if key < parent.key:
                if parent.left is NIL:
                    node = parent.left = Node(key, value)
                    return node
                parent = parent.left
            elif parent.key < key:
                if parent.right is NIL:
                    node = parent.right = Node(key, value)
                    return node
                parent = parent.right
            else:
                return parent

    @override
    def popmax(self, /) -> Node[KeyT, ValueT] | Nil:
        node = self._root
        if node is NIL:
            return node
        if node.right is NIL:
            self._root = node.left
            return node
        while node.right.right is not NIL:
            node = node.right
            assert node.right is not NIL
        assert node.right is not NIL
        result, node.right = node.right, node.right.left
        return result

    @override
    def popmin(self, /) -> Node[KeyT, ValueT] | Nil:
        node = self._root
        if node is NIL:
            return node
        if node.left is NIL:
            self._root = node.right
            return node
        while node.left.left is not NIL:
            node = node.left
            assert node.left is not NIL
        assert node.left is not NIL
        result, node.left = node.left, node.left.right
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
        return result

    @override
    def remove(self, _node: abcs.Node[KeyT, ValueT], /) -> None:
        assert isinstance(_node, Node), _node
        node: Node[KeyT, ValueT] = _node
        assert self._root is not NIL
        parent, key = self._root, node.key
        if are_keys_equal(key, parent.key):
            if parent.left is NIL:
                self._root = parent.right
            else:
                node = parent.left
                if node.right is NIL:
                    self._root, node.right = node, self._root.right
                else:
                    while node.right.right is not NIL:
                        node = node.right
                        assert node.right is not NIL
                    assert node.right is not NIL
                    (
                        self._root,
                        node.right.left,
                        node.right.right,
                        node.right,
                    ) = (
                        node.right,
                        self._root.left,
                        self._root.right,
                        node.right.left,
                    )
            return
        while True:
            if key < parent.key:
                # search in left subtree
                assert parent.left is not NIL
                if are_keys_equal(key, parent.left.key):
                    # remove `parent.left`
                    cursor = parent.left.left
                    if cursor is NIL:
                        parent.left = parent.left.right
                        return
                    if cursor.right is NIL:
                        parent.left, cursor.right = cursor, parent.left.right
                    else:
                        while cursor.right.right is not NIL:
                            cursor = cursor.right
                            assert cursor.right is not NIL
                        assert cursor.right is not NIL
                        (
                            parent.left,
                            cursor.right.left,
                            cursor.right.right,
                            cursor.right,
                        ) = (
                            cursor.right,
                            parent.left.left,
                            parent.left.right,
                            cursor.right.left,
                        )
                    return
                parent = parent.left
            # search in right subtree
            else:
                assert parent.right is not NIL
                if are_keys_equal(key, parent.right.key):
                    # remove `parent.right`
                    cursor = parent.right.left
                    if cursor is NIL:
                        parent.right = parent.right.right
                        return
                    if cursor.right is NIL:
                        parent.right, cursor.right = cursor, parent.right.right
                    else:
                        while cursor.right.right is not NIL:
                            cursor = cursor.right
                            assert cursor.right is not NIL
                        assert cursor.right is not NIL
                        (
                            parent.right,
                            cursor.right.left,
                            cursor.right.right,
                            cursor.right,
                        ) = (
                            cursor.right,
                            parent.right.left,
                            parent.right.right,
                            cursor.right.left,
                        )
                    return
                parent = parent.right

    @override
    def successor(
        self, node: abcs.Node[KeyT, ValueT], /
    ) -> Node[KeyT, ValueT] | Nil:
        result: Node[KeyT, ValueT] | Nil
        assert isinstance(node, Node), node
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
        return result

    _root: Node[KeyT, ValueT] | Nil

    __slots__ = ('_root',)

    @override
    def __copy__(self, /) -> Self:
        return type(self)(copy.deepcopy(self._root))

    def __init__(self, root: Node[KeyT, ValueT] | Nil, /) -> None:
        self._root = root
