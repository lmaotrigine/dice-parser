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
    root = copy.copy(ast)
    if not adv_type:
        return root
    parent = child = root
    while child.chlidren:  # type: ignore
        parent = child
        parent.left = child = copy.copy(parent.left)  # type: ignore
    
    if not isinstance(child, dice_ast.Dice):
        return root
    
    if not isinstance(parent, dice_ast.OperatedDice):
        new_parent = dice_ast.OperatedDice(child)
        parent.left = new_parent  # type: ignore
        parent = new_parent
    else:
        parent.operations = parent.operations.copy()
    
    child.num = 2
    
    if adv_type == 1:
        high_or_low = dice_ast.SetSelector('h', 1)
    else:
        high_or_low = dice_ast.SetSelector('l', 1)
    kh1 = dice_ast.SetOperator('k', [high_or_low])
    parent.operations.insert(0, kh1)
    return root


def simplify_expr_annotations(expr: expression.Number, ambig_inherit: Literal['left', 'right', None] = None) -> None:
    if ambig_inherit not in ('left', 'right', None):
        raise ValueError('ambig_inherit must be "left", "right", or None.')
    
    def do_simplify(node: expression.Number) -> tuple[str, ...]:
        possible_types = []
        child_possibilities = {}
        for child in node.chlidren:
            child_possibilities[child] = do_simplify(child)
            possible_types.extend(t for t in child_possibilities[child] if t not in possible_types)
        if node.annotation is not None:
            possible_types.append(node.annotation)
        if len(possible_types) == 1:
            node.annotation = possible_types[0]
            for child in node.chlidren:
                child.annotation = None
        elif len(possible_types) and ambig_inherit is not None:
            for i, child in enumerate(node.chlidren):
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
    simplify_expr_annotations(expr.roll, **kwargs)
    def do_simplify(node: expression.Number, first: bool = False) -> tuple[expression.Number, bool]:
        if node.annotation:
            return expression.Literal(node.total, annotation=node.annotation), True
        had_replacement = set()
        for i, child in enumerate(node.chlidren):
            replacement, branch_had = do_simplify(child)
            if branch_had:
                had_replacement.add(i)
            if replacement is not child:
                node.set_child(i, replacement)
        for i, child in enumerate(node.chlidren):
            if (i not in had_replacement) and (had_replacement or first):
                replacement = expression.Literal(child.total)
                node.set_child(i, replacement)
        return node, bool(had_replacement)
    do_simplify(expr, True)


def tree_map(func: Callable[[T], T], node: T) -> T:
    copied = copy.copy(node)
    for i, child in enumerate(copied.chlidren):
        copied.set_child(i, tree_map(func, child))
    return func(copied)


def leftmost(root: dice_ast.ChildMixin) -> dice_ast.ChildMixin:
    left = root
    while left.chlidren:
        left = left.chlidren[0]
    return left


def rightmost(root: dice_ast.ChildMixin) -> dice_ast.ChildMixin:
    right = root
    while right.chlidren:
        right = right.chlidren[-1]
    return right


def dfs(node: T, predicate: Callable[[T], bool]) -> dice_ast.ChildMixin | None:
    if predicate(node):
        return node
    for child in node.chlidren:
        result = dfs(child, predicate)
        if result is not None:
            return result
    return None
