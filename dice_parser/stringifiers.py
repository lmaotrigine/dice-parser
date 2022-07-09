from __future__ import annotations

import abc
from collections.abc import Callable, Iterable
from typing import TypeVar

from .expression import *

__all__ = ('Stringifier', 'SimpleStringifier', 'MarkdownStringifier')

E = TypeVar('E', bound=Number)

class Stringifier(abc.ABC):
    def _get_stringifer(self, _type: type[E]) -> Callable[[E], str]:
        _nodes = {
            Expression: self._str_expression,
            Literal: self._str_literal,
            UnOp:self._str_unop,
            BinOp: self._str_binop,
            Parenthetical: self._str_parenthetical,
            Set: self._str_set,
            Dice:self._str_dice,
            Die: self._str_die,
        }
        return _nodes[_type]  # type: ignore
    
    def stringify(self, the_roll: Expression) -> str:
        return self._stringify(the_roll)
    
    def _stringify(self, node: Number) -> str:
        handler = self._get_stringifer(type(node))
        inside = handler(node)
        if node.annotation:
            return f'{inside} {node.annotation}'
        return inside
    
    def _str_expression(self, node: Expression) -> str:
        raise NotImplementedError
    
    def _str_literal(self, node: Literal) -> str:
        raise NotImplementedError
    
    def _str_unop(self, node: UnOp) -> str:
        raise NotImplementedError
    
    def _str_binop(self, node: BinOp) -> str:
        raise NotImplementedError
    
    def _str_parenthetical(self, node: Parenthetical) -> str:
        raise NotImplementedError
    
    def _str_set(self, node: Set) -> str:
        raise NotImplementedError
    
    def _str_dice(self, node: Dice) -> str:
        raise NotImplementedError
    
    def _str_die(self, node: Die) -> str:
        raise NotImplementedError
    
    @staticmethod
    def _str_ops(operations: Iterable[SetOperator]) -> str:
        return ''.join([str(op) for op in operations])


class SimpleStringifier(Stringifier):
    def _str_expression(self, node: Expression) -> str:
        return f'{self._stringify(node.roll)} ={int(node.total)}'
    
    def _str_literal(self, node: Literal) -> str:
        history = ' -> '.join(map(str, node.values))
        if node.exploded:
            return f'{history}!'
        return history
    
    def _str_unop(self, node: UnOp) -> str:
        return f'{node.op}{self._stringify(node.value)}'
    
    def _str_binop(self, node: BinOp) -> str:
        return f'{self._stringify(node.left)} {node.op} {self._stringify(node.right)}'
    
    def _str_parenthetical(self, node: Parenthetical) -> str:
        return f'({self._stringify(node.value)}){self._str_ops(node.operations)}'
    
    def _str_set(self, node: Set) -> str:
        out = ', '.join([self._stringify(v) for v in node.values])
        if len(node.values) == 1:
            return f'({out},){self._str_ops(node.operations)}'
        return f'({out}){self._str_ops(node.operations)}'
    
    def _str_dice(self, node: Dice) -> str:
        the_dice = [self._stringify(die) for die in node.values]
        return f'{node.num}d{node.size}{self._str_ops(node.operations)} ({", ".join(the_dice)})'
    
    def _str_die(self, node: Die) -> str:
        the_rolls = [self._stringify(val) for val in node.values]
        return ', '.join(the_rolls)


class MarkdownStringifier(SimpleStringifier):
    class _MDContext:
        def __init__(self) -> None:
            self.in_dropped = False
        
        def reset(self) -> None:
            self.in_dropped = False
    
    def __init__(self) -> None:
        super().__init__()
        self._context = self._MDContext()
    
    def stringify(self, the_roll: Expression) -> str:
        self._context.reset()
        return super().stringify(the_roll)
    
    def _stringify(self, node: Number) -> str:
        if not node.kept and not self._context.in_dropped:
            self._context.in_dropped = True
            inside = super()._stringify(node)
            self._context.in_dropped = False
            return f'~~{inside}~~'
        return super()._stringify(node)
    
    def _str_expression(self, node: Expression) -> str:
        return f'{self._stringify(node.roll)} = `{int(node.total)}`'
    
    def _str_die(self, node: Die) -> str:
        the_rolls = []
        for val in node.values:
            inside = self._stringify(val)
            if val.number == 1 or val.number == node.size:
                inside = f'**{inside}**'
            the_rolls.append(inside)
        return ', '.join(the_rolls)
