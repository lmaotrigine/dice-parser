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

import abc
from collections.abc import Callable, Iterable
from typing import TypeVar

from .expression import *


__all__ = ('Stringifier', 'SimpleStringifier', 'MarkdownStringifier')

E = TypeVar('E', bound=Number)


class Stringifier(abc.ABC):
    """An ABC for a string builder from a dice result.

    Subclasses should implement all ``str_*`` methods to transform an :class:`Expression` into a :class:`str`.
    """

    def _get_stringifer(self, _type: type[E]) -> Callable[[E], str]:
        _nodes = {
            Expression: self.str_expression,
            Literal: self.str_literal,
            UnOp: self.str_unop,
            BinOp: self.str_binop,
            Parenthetical: self.str_parenthetical,
            Set: self.str_set,
            Dice: self.str_dice,
            Die: self.str_die,
        }
        return _nodes[_type]  # type: ignore

    def stringify(self, the_roll: Expression) -> str:
        """Transforms a rolled expression into a string recursively, bottom-up."""
        return self.stringify_node(the_roll)

    def stringify_node(self, node: Number) -> str:
        """Called on each node that needs to be stringified."""
        handler = self._get_stringifer(type(node))
        inside = handler(node)
        if node.annotation:
            return f'{inside} {node.annotation}'
        return inside

    def str_expression(self, node: Expression) -> str:
        raise NotImplementedError

    def str_literal(self, node: Literal) -> str:
        raise NotImplementedError

    def str_unop(self, node: UnOp) -> str:
        raise NotImplementedError

    def str_binop(self, node: BinOp) -> str:
        raise NotImplementedError

    def str_parenthetical(self, node: Parenthetical) -> str:
        raise NotImplementedError

    def str_set(self, node: Set) -> str:
        raise NotImplementedError

    def str_dice(self, node: Dice) -> str:
        raise NotImplementedError

    def str_die(self, node: Die) -> str:
        raise NotImplementedError

    @staticmethod
    def _str_ops(operations: Iterable[SetOperator]) -> str:
        return ''.join([str(op) for op in operations])


class SimpleStringifier(Stringifier):
    def str_expression(self, node: Expression) -> str:
        return f'{self.stringify_node(node.roll)} = {int(node.total)}'

    def str_literal(self, node: Literal) -> str:
        history = ' -> '.join(map(str, node.values))
        if node.exploded:
            return f'{history}!'
        return history

    def str_unop(self, node: UnOp) -> str:
        return f'{node.op}{self.stringify_node(node.value)}'

    def str_binop(self, node: BinOp) -> str:
        return f'{self.stringify_node(node.left)} {node.op} {self.stringify_node(node.right)}'

    def str_parenthetical(self, node: Parenthetical) -> str:
        return f'({self.stringify_node(node.value)}){self._str_ops(node.operations)}'

    def str_set(self, node: Set) -> str:
        out = ', '.join([self.stringify_node(v) for v in node.values])
        if len(node.values) == 1:
            return f'({out},){self._str_ops(node.operations)}'
        return f'({out}){self._str_ops(node.operations)}'

    def str_dice(self, node: Dice) -> str:
        the_dice = [self.stringify_node(die) for die in node.values]
        return f'{node.num}d{node.size}{self._str_ops(node.operations)} ({", ".join(the_dice)})'

    def str_die(self, node: Die) -> str:
        the_rolls = [self.stringify_node(val) for val in node.values]
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

    def stringify_node(self, node: Number) -> str:
        if not node.kept and not self._context.in_dropped:
            self._context.in_dropped = True
            inside = super().stringify_node(node)
            self._context.in_dropped = False
            return f'~~{inside}~~'
        return super().stringify_node(node)

    def str_expression(self, node: Expression) -> str:
        return f'{self.stringify_node(node.roll)} = `{int(node.total)}`'

    def str_die(self, node: Die) -> str:
        the_rolls = []
        for val in node.values:
            inside = self.stringify_node(val)
            if val.number == 1 or val.number == node.size:
                inside = f'**{inside}**'
            the_rolls.append(inside)
        return ', '.join(the_rolls)
