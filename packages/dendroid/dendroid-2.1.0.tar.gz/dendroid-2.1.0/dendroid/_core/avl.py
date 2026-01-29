from __future__ import annotations

import copy
from collections.abc import Iterable
from reprlib import recursive_repr
from typing import Generic, cast, overload

from reprit.base import generate_repr
from typing_extensions import Self, override

from . import abcs
from .hints import Item, KeyT, ValueT
from .nil import NIL, Nil
from .utils import (
    dereference_maybe,
    maybe_weakref,
    to_unique_sorted_items,
    to_unique_sorted_values,
)


class Node(abcs.HasCustomRepr, Generic[KeyT, ValueT]):
    @property
    def balance_factor(self, /) -> int:
        return _to_height(self.left) - _to_height(self.right)

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
    def left(self, node: Self | Nil) -> None:
        self._left = node
        _set_parent(node, self)

    @property
    def parent(self, /) -> Self | Nil:
        return dereference_maybe(self._parent)

    @parent.setter
    def parent(self, value: Self | Nil, /) -> None:
        self._parent = maybe_weakref(value)

    @property
    def right(self, /) -> Self | Nil:
        return self._right

    @right.setter
    def right(self, node: Self | Nil) -> None:
        self._right = node
        _set_parent(node, self)

    @property
    def value(self, /) -> ValueT:
        return self._value

    @value.setter
    def value(self, value: ValueT) -> None:
        self._value = value

    __slots__ = (
        '__weakref__',
        '_key',
        '_left',
        '_parent',
        '_right',
        '_value',
        'height',
    )

    def __init__(
        self,
        key: KeyT,
        value: ValueT,
        /,
        *,
        left: Self | Nil = NIL,
        right: Self | Nil = NIL,
        parent: Self | Nil = NIL,
    ) -> None:
        self._key, self._value = key, value
        self.left, self.right, self.parent = left, right, parent
        self.height = max(_to_height(self.left), _to_height(self.right)) + 1

    __repr__ = recursive_repr()(generate_repr(__init__))

    def __getstate__(
        self, /
    ) -> tuple[KeyT, ValueT, int, Self | Nil, Self | Nil, Self | Nil]:
        return (
            self._key,
            self._value,
            self.height,
            self.parent,
            self.left,
            self.right,
        )

    def __setstate__(
        self,
        state: tuple[KeyT, ValueT, int, Self | Nil, Self | Nil, Self | Nil],
        /,
    ) -> None:
        (
            self._key,
            self._value,
            self.height,
            self.parent,
            self._left,
            self._right,
        ) = state


def _to_height(node: Node[KeyT, ValueT] | Nil, /) -> int:
    return -1 if node is NIL else node.height


def _update_height(node: Node[KeyT, ValueT], /) -> None:
    node.height = max(_to_height(node.left), _to_height(node.right)) + 1


def _set_parent(
    node: Node[KeyT, ValueT] | Nil, parent: Node[KeyT, ValueT] | Nil, /
) -> None:
    if node is not NIL:
        node.parent = parent


class Tree(abcs.Tree[KeyT, ValueT]):
    @property
    def root(self, /) -> Node[KeyT, ValueT] | Nil:
        return self._root

    @override
    def predecessor(
        self, node: abcs.Node[KeyT, ValueT], /
    ) -> Node[KeyT, ValueT] | Nil:
        assert isinstance(node, Node), node
        if node.left is NIL:
            result = node.parent
            while result is not NIL and node is result.left:
                node, result = result, result.parent
        else:
            result = node.left
            while result.right is not NIL:
                result = result.right
        return result

    @override
    def successor(
        self, node: abcs.Node[KeyT, ValueT], /
    ) -> Node[KeyT, ValueT] | Nil:
        assert isinstance(node, Node), node
        if node.right is NIL:
            result = node.parent
            while result is not NIL and node is result.right:
                node, result = result, result.parent
        else:
            result = node.right
            while result.left is not NIL:
                result = result.left
        return result

    @overload
    @classmethod
    def from_components(
        cls, keys: Iterable[KeyT], values: None = ..., /
    ) -> Tree[KeyT, KeyT]: ...

    @overload
    @classmethod
    def from_components(
        cls, keys: Iterable[KeyT], values: Iterable[ValueT], /
    ) -> Tree[KeyT, ValueT]: ...

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
        items = to_unique_sorted_items(keys, list(values))

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

    @override
    def clear(self, /) -> None:
        self._root = NIL

    @override
    def insert(self, key: KeyT, value: ValueT, /) -> Node[KeyT, ValueT]:
        parent = self.root
        if parent is NIL:
            node = self._root = Node(key, value)
            return node
        while True:
            if key < parent.key:
                if parent.left is NIL:
                    node = Node(key, value)
                    parent.left = node
                    break
                parent = parent.left
            elif parent.key < key:
                if parent.right is NIL:
                    node = Node(key, value)
                    parent.right = node
                    break
                parent = parent.right
            else:
                return parent
        self._rebalance(node.parent)
        return node

    @override
    def remove(self, node: abcs.Node[KeyT, ValueT], /) -> None:
        assert isinstance(node, Node), node
        if node.left is NIL:
            imbalanced_node = node.parent
            self._transplant(node, node.right)
        elif node.right is NIL:
            imbalanced_node = node.parent
            self._transplant(node, node.left)
        else:
            successor = node.right
            while successor.left is not NIL:
                successor = successor.left
            if successor.parent is node:
                imbalanced_node = successor
            else:
                imbalanced_node = successor.parent
                self._transplant(successor, successor.right)
                successor.right = node.right
            self._transplant(node, successor)
            successor.left, successor.left.parent = node.left, successor
        self._rebalance(imbalanced_node)

    def _rebalance(self, node: Node[KeyT, ValueT] | Nil) -> None:
        while node is not NIL:
            _update_height(node)
            if node.balance_factor > 1:
                assert node.left is not NIL
                if node.left.balance_factor < 0:
                    self._rotate_left(node.left)
                self._rotate_right(node)
            elif node.balance_factor < -1:
                assert node.right is not NIL
                if node.right.balance_factor > 0:
                    self._rotate_right(node.right)
                self._rotate_left(node)
            node = node.parent

    def _rotate_left(self, node: Node[KeyT, ValueT], /) -> None:
        replacement = node.right
        assert replacement is not NIL
        self._transplant(node, replacement)
        node.right, replacement.left = replacement.left, node
        _update_height(node)
        _update_height(replacement)

    def _rotate_right(self, node: Node[KeyT, ValueT], /) -> None:
        replacement = node.left
        assert replacement is not NIL
        self._transplant(node, replacement)
        node.left, replacement.right = replacement.right, node
        _update_height(node)
        _update_height(replacement)

    def _transplant(
        self,
        origin: Node[KeyT, ValueT],
        replacement: Node[KeyT, ValueT] | Nil,
        /,
    ) -> None:
        parent = origin.parent
        if parent is NIL:
            self._root = replacement
            _set_parent(replacement, NIL)
        elif origin is parent.left:
            parent.left = replacement
        else:
            parent.right = replacement

    _root: Node[KeyT, ValueT] | Nil

    __slots__ = ('_root',)

    @override
    def __copy__(self, /) -> Self:
        return type(self)(copy.deepcopy(self._root))

    def __init__(self, root: Node[KeyT, ValueT] | Nil, /) -> None:
        self._root = root
