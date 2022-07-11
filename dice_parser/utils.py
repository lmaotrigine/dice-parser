# Copyright (c) 2022-present, Varun J., All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from . import dice_ast, expression


if TYPE_CHECKING:
    from .dice import AdvType


T = TypeVar('T', bound=dice_ast.ChildMixin)
N = TypeVar('N', bound=dice_ast.Node)
E = TypeVar('E', bound=expression.Number)


def ast_adv_copy(ast: N, adv_type: AdvType) -> N:
    """Returns a minimally shallow copy of a dice AST with respect to advantage.

    Parameters
    ----------
    node: :class:`dice_parser.ast.Node`
        The parsed AST
    adv_type: :class:`AdvType`
        The advantage type to roll at.

    Returns
    -------
    :class:`dice_parser.ast.Node`
        The copied AST
    """
    root = copy.copy(ast)
    if not adv_type:
        return root
    parent = child = root
    while child.children:  # type: ignore
        parent = child
        parent.left = child = copy.copy(parent.left)  # type: ignore

    if not isinstance(child, dice_ast.DiceNode):
        return root

    if not (child.num == 1 and child.size == 20):
        return root

    if not isinstance(parent, dice_ast.OperatedDice):
        new_parent = dice_ast.OperatedDice(child)
        parent.left = new_parent  # type: ignore
        parent = new_parent
    else:
        parent.operations = parent.operations.copy()

    child.num = 2

    if adv_type == 1:
        high_or_low = dice_ast.NodeSetSelector('h', 1)
    else:
        high_or_low = dice_ast.NodeSetSelector('l', 1)
    kh1 = dice_ast.NodeSetOperator('k', [high_or_low])
    parent.operations.insert(0, kh1)
    return root


def simplify_expr_annotations(
    expr: expression.Number, ambig_inherit: Literal['left', 'right', None] = None
) -> None:
    """Transforms an expression in place by simplifying the annotations using a bubble-up method.

    Parameters
    ----------
    expr: :class:`~dice_parser.Number`
        The expression to transform
    ambig_inherit: typing.Literal['left', 'right', None]
        Inheritance behaviour when encountering a child node with no annotation and a parent with ambiguous types.
        Can be ``None`` for no inherit, ``'left'`` for leftmost, or ``'right'`` for rightmost.
    """
    if ambig_inherit not in ('left', 'right', None):
        raise ValueError('ambig_inherit must be "left", "right", or None.')

    def do_simplify(node: expression.Number) -> tuple[str, ...]:
        possible_types = []
        child_possibilities = {}
        for child in node.children:
            child_possibilities[child] = do_simplify(child)
            possible_types.extend(t for t in child_possibilities[child] if t not in possible_types)
        if node.annotation is not None:
            possible_types.append(node.annotation)
        if len(possible_types) == 1:
            node.annotation = possible_types[0]
            for child in node.children:
                child.annotation = None
        elif len(possible_types) and ambig_inherit is not None:
            for i, child in enumerate(node.children):
                if child_possibilities[child]:
                    continue
                elif isinstance(node, expression.BinOp) and node.op in {'*', '/', '//', '%'} and i:
                    continue
                elif ambig_inherit == 'left':
                    child.annotation = possible_types[0]
                elif ambig_inherit == 'right':
                    child.annotation = possible_types[-1]
        return tuple(possible_types)

    do_simplify(expr)


def simplify_expr(expr: expression.Expression, **kwargs: Any) -> None:
    """Transforms an expression in place by simplifying it (removing all dice and evaluating branches with respect to
    annotations).

    Parameters
    ----------
    expr: :class:`~dice_parser.Expression`
        The expression to transform
    kwargs: Any
        Arguments that are passed to :func:`simplify_expr_annotations`.
    """
    simplify_expr_annotations(expr.roll, **kwargs)

    def do_simplify(node: expression.Number, first: bool = False) -> tuple[expression.Number, bool]:
        if node.annotation:
            return expression.Literal(node.total, annotation=node.annotation), True
        had_replacement = set()
        for i, child in enumerate(node.children):
            replacement, branch_had = do_simplify(child)
            if branch_had:
                had_replacement.add(i)
            if replacement is not child:
                node.set_child(i, replacement)
        for i, child in enumerate(node.children):
            if (i not in had_replacement) and (had_replacement or first):
                replacement = expression.Literal(child.total)
                node.set_child(i, replacement)
        return node, bool(had_replacement)

    do_simplify(expr, True)


def tree_map(func: Callable[[T], T], node: T) -> T:
    """Returns a copy of the tree, with each node replaced with ``func(node)``.

    Parameters
    ----------
    func: Callable[[:class:`dice_parser.ast.ChildMixin`], :class:`dice_parser.ast.ChildMixin`]
        A transformer function
    node: :class:`dice_parser.ast.ChildMixin`
        The root of the tree to transform.
    """
    copied = copy.copy(node)
    for i, child in enumerate(copied.children):
        copied.set_child(i, tree_map(func, child))
    return func(copied)


def leftmost(root: dice_ast.ChildMixin) -> dice_ast.ChildMixin:
    """Returns the leftmost leaf in this tree.

    Parameters
    ----------
    root: :class:`dice_parser.ast.ChildMixin`
        The root node of the tree
    """
    left = root
    while left.children:
        left = left.children[0]
    return left


def rightmost(root: dice_ast.ChildMixin) -> dice_ast.ChildMixin:
    """Returns the rightmost left in this tree.

    Parameters
    ----------
    root: :class:`dice_parser.ast.ChildMixin`
        The root node of this tree
    """
    right = root
    while right.children:
        right = right.children[-1]
    return right


def dfs(node: T, predicate: Callable[[T], bool]) -> dice_ast.ChildMixin | None:
    """Returns the first node in the tree such that ``predicate(node)`` is True, searching depth-first left-to-right.

    Parameters
    ----------
    node: :class:`dice_parser.ast.ChildMixin`
        The root node of the tree
    predicate: Callable[[:class:`dice_parser.ast.ChildMixin`], :class:`bool`]
        A preficate function
    """
    if predicate(node):
        return node
    for child in node.children:
        result = dfs(child, predicate)
        if result is not None:
            return result
    return None
