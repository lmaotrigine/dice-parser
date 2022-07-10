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
import random
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from . import dice_ast as ast
from . import errors


if TYPE_CHECKING:
    from typing_extensions import Self

    from .dice import RollContext

E = TypeVar('E', bound='Number')


__all__ = (
    'Number',
    'Expression',
    'Literal',
    'UnOp',
    'BinOp',
    'Parenthetical',
    'Set',
    'Dice',
    'Die',
    'SetOperator',
    'SetSelector',
)


class Number(abc.ABC, ast.ChildMixin):
    __slots__ = ('kept', 'annotation')

    def __init__(self, kept: bool = True, annotation: str | None = None) -> None:
        self.kept = kept
        self.annotation = annotation

    @property
    def number(self) -> int | float:
        return sum(n.number for n in self.keptset)

    @property
    def total(self) -> int | float:
        return self.number if self.kept else 0

    @property
    def set(self) -> list[Self]:
        raise NotImplementedError

    @property
    def keptset(self) -> list[Self]:
        return [n for n in self.set if n.kept]

    def drop(self) -> None:
        self.kept = False

    def __int__(self) -> int:
        return int(self.total)

    def __float__(self) -> float:
        return float(self.total)

    def __repr__(self) -> str:
        return f'<Number total={self.total} kept={self.kept}>'

    def set_child(self, index: int, value: Self) -> None:
        return super().set_child(index, value)

    @property
    def children(self) -> list[Self]:
        raise NotImplementedError


class Expression(Number):
    __slots__ = ('roll', 'comment')

    def __init__(self, roll: Number, comment: str | None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.roll = roll
        self.comment = comment

    @property
    def number(self) -> int | float:
        return self.roll.number

    @property
    def set(self) -> list[Number]:
        return self.roll.set

    @property
    def children(self) -> list[Number]:
        return [self.roll]

    def set_child(self, index: int, value: Number) -> None:
        self._child_set_check(index)
        self.roll = value

    def __repr__(self) -> str:
        return f'<Expression roll={self.roll} comment={self.comment}>'


class Literal(Number):
    __slots__ = ('values', 'exploded')

    def __init__(self, value: int | float, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.values = [value]
        self.exploded = False

    @property
    def number(self) -> int | float:
        return self.values[-1]

    @property
    def set(self) -> list[Number]:
        return [self]

    @property
    def children(self) -> list[Number]:
        return []

    def explode(self) -> None:
        self.exploded = True

    def update(self, value: int | float) -> None:
        self.values.append(value)

    def __repr__(self) -> str:
        return f'<Literal {self.number}>'


class UnOp(Number):
    __slots__ = ('op', 'value')

    UNARY_OPS = {
        '-': lambda v: -v,
        '+': lambda v: +v,
    }

    def __init__(self, op: str, value: Number, **kwargs) -> None:
        super().__init__(**kwargs)
        self.op = op
        self.value = value

    @property
    def number(self) -> int | float:
        return self.UNARY_OPS[self.op](self.value.total)

    @property
    def set(self) -> list[Number]:
        return [self]

    @property
    def children(self) -> list[Number]:
        return [self.value]

    def set_child(self, index: int, value: Number) -> None:
        self._child_set_check(index)
        self.value = value

    def __repr__(self) -> str:
        return f'<UnOp op={self.op} value={self.value}>'


class BinOp(Number):
    __slots__ = ('op', 'left', 'right')

    BINARY_OPS = {
        '+': lambda l, r: l + r,
        '-': lambda l, r: l - r,
        '*': lambda l, r: l * r,
        '/': lambda l, r: l / r,
        '//': lambda l, r: l // r,
        '%': lambda l, r: l % r,
        '<': lambda l, r: int(l < r),
        '>': lambda l, r: int(l > r),
        '==': lambda l, r: int(l == r),
        '>=': lambda l, r: int(l >= r),
        '<=': lambda l, r: int(l <= r),
        '!=': lambda l, r: int(l != r),
    }

    if TYPE_CHECKING:
        left: Number
        right: Number

    def __init__(self, left: Number, op: str, right: Number, **kwargs) -> None:
        super().__init__(**kwargs)
        self.op = op
        self.left = left
        self.right = right

    @property
    def number(self) -> int | float:
        try:
            return self.BINARY_OPS[self.op](self.left.total, self.right.total)
        except ZeroDivisionError:
            raise errors.RollValueError('Cannot divide by zero.')

    @property
    def set(self) -> list[Number]:
        return [self]

    @property
    def children(self) -> list[Number]:
        return [self.left, self.right]

    def set_child(self, index: int, value: Number) -> None:
        self._child_set_check(index)
        if self.children[index] is self.left:
            self.left = value
        else:
            self.right = value

    def __repr__(self) -> str:
        return f'<BinOp left={self.left} op={self.op} right={self.right}>'


class Parenthetical(Number):
    __slots__ = ('value', 'operations')

    def __init__(
        self, value: Number, operations: list[SetOperator] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        if operations is None:
            operations = []
        self.value = value
        self.operations = operations

    @property
    def total(self) -> int | float:
        return self.value.total if self.kept else 0

    @property
    def set(self) -> list[Number]:
        return self.value.set

    @property
    def children(self) -> list[Number]:
        return [self.value]

    def set_child(self, index: int, value: Number) -> None:
        self._child_set_check(index)
        self.value = value

    def __repr__(self) -> str:
        return f'<Parenthetical value={self.value} operations={self.operations}>'


class Set(Number, Generic[E]):
    __slots__ = ('values', 'operations')

    def __init__(
        self, values: list[E], operations: list[SetOperator] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        if operations is None:
            operations = []
        self.values = values
        self.operations = operations

    @property
    def set(self) -> list[E]:
        return self.values

    @property
    def keptset(self) -> list[E]:
        return [n for n in self.set if n.kept]

    @property
    def children(self) -> list[E]:
        return self.values

    def set_child(self, index: int, value: E) -> None:
        self._child_set_check(index)
        self.values[index] = value

    def __repr__(self) -> str:
        return f'<Set values={self.values} operations={self.operations}>'

    def __copy__(self) -> Set:
        return Set(values=self.values.copy(), operations=self.operations.copy())


class Dice(Set['Die']):
    __slots__ = ('num', 'size', '_context')
    if TYPE_CHECKING:
        values: list[Die]

    def __init__(
        self,
        num: int,
        size: int | str,
        values: list[Die],
        operations: list[SetOperator] | None = None,
        context: RollContext | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(values, operations, **kwargs)
        self.num = num
        self.size = size
        self._context = context

    @classmethod
    def new(cls, num: int, size: int | str, context: RollContext | None = None) -> Dice:
        return cls(num, size, [Die.new(size, context=context) for _ in range(num)], context=context)

    def roll_another(self) -> None:
        self.values.append(Die.new(self.size, context=self._context))

    @property
    def children(self) -> list[Number]:
        return []

    def __repr__(self) -> str:
        return f'<Dice num={self.num} size={self.size} values={self.values} operations={self.operations}>'

    def __copy__(self) -> Dice:
        return Dice(
            num=self.num,
            size=self.size,
            context=self._context,
            values=self.values.copy(),
            operations=self.operations.copy(),
        )


class Die(Number):
    __slots__ = ('size', 'values', '_context')

    def __init__(
        self, size: int | str, values: list[Literal], context: RollContext | None = None
    ) -> None:
        super().__init__()
        self.size = size
        self.values = values
        self._context = context

    @classmethod
    def new(cls, size: int | str, context: RollContext | None = None) -> Die:
        inst = cls(size, [], context=context)
        inst._add_roll()
        return inst

    @property
    def number(self) -> int | float:
        return self.values[-1].total

    @property
    def set(self) -> list[Number]:
        return [self.values[-1]]

    @property
    def children(self) -> list[Number]:
        return []

    def _add_roll(self) -> None:
        if self.size != '%' and self.size < 1:  # type: ignore
            raise errors.RollValueError('Cannot roll a 0-sided die.')
        if self._context:
            self._context.count_roll()
        if self.size == '%':
            n = Literal(random.randrange(10) * 10)
        else:
            n = Literal(random.randrange(self.size) + 1)  # type: ignore
        self.values.append(n)

    def reroll(self) -> None:
        if self.values:
            self.values[-1].drop()
        self._add_roll()

    def explode(self) -> None:
        if self.values:
            self.values[-1].explode()
        # another Die is added by the explode operator

    def force_value(self, new_value: int | float) -> None:
        if self.values:
            self.values[-1].update(new_value)

    def __repr__(self) -> str:
        return f'<Die size={self.size} values={self.values}>'


class SetOperator:
    __slots__ = ('op', 'sels')

    def __init__(self, op: str, sels: list[SetSelector]) -> None:
        self.op = op
        self.sels = sels

    @classmethod
    def from_ast(cls, node: ast.SetOperator) -> SetOperator:
        return cls(node.op, [SetSelector.from_ast(n) for n in node.sels])

    def select(self, target: Set[E], max_targets: int | None = None) -> set[E]:
        out = set()
        for selector in self.sels:
            batch_max = None
            if max_targets is not None:
                batch_max = max_targets - len(out)
                if batch_max == 0:
                    break
            out.update(selector.select(target, max_targets=batch_max))
        return out

    def operate(self, target: Set) -> None:
        operations = {
            'k': self.keep,
            'p': self.drop,
            # dice only
            'rr': self.reroll,
            'ro': self.reroll_once,
            'ra': self.explode_once,
            'e': self.explode,
            'mi': self.minimum,
            'ma': self.maximum,
        }
        operations[self.op](target)  # type: ignore

    def keep(self, target: Set) -> None:
        for value in target.keptset:
            if value not in self.select(target):
                value.drop()

    def drop(self, target: Set) -> None:
        for value in self.select(target):
            value.drop()

    def reroll(self, target: Dice) -> None:
        to_reroll = self.select(target)
        while to_reroll:
            for die in to_reroll:
                die.reroll()
            to_reroll = self.select(target)

    def reroll_once(self, target: Dice) -> None:
        for die in self.select(target):
            die.reroll()

    def explode(self, target: Dice) -> None:
        to_explode = self.select(target)
        already_exploded = set()
        while to_explode:
            for die in to_explode:
                die.explode()
                target.roll_another()
            already_exploded.update(to_explode)
            to_explode = self.select(target).difference(already_exploded)

    def explode_once(self, target: Dice) -> None:
        for die in self.select(target, max_targets=1):
            die.explode()
            target.roll_another()

    def minimum(self, target: Dice) -> None:
        selector = self.sels[-1]
        if selector.cat is not None:
            raise errors.RollValueError(f'{selector} is not a valid selector for minimums.')
        the_min = selector.num
        for die in target.keptset:
            if die.number < the_min:
                die.force_value(the_min)

    def maximum(self, target: Dice) -> None:
        selector = self.sels[-1]
        if selector.cat is not None:
            raise errors.RollValueError(f'{selector} is not a valid selector for maximums.')
        the_max = selector.num
        for die in target.keptset:
            if die.number > the_max:
                die.force_value(the_max)

    def __str__(self) -> str:
        return ''.join([f'{self.op}{sel}' for sel in self.sels])

    def __repr__(self) -> str:
        return f'<SetOperator op={self.op} sels={self.sels}>'


class SetSelector:
    __slots__ = ('cat', 'num')

    def __init__(self, cat: str | None, num: int) -> None:
        self.cat = cat
        self.num = num

    @classmethod
    def from_ast(cls, node: ast.SetSelector) -> Self:
        return cls(node.cat, node.num)

    def select(self, target: Set[E], max_targets: int | None = None) -> set[E]:
        selectors = {
            'l': self.lowestn,
            'h': self.highestn,
            '<': self.lessthan,
            '>': self.morethan,
            None: self.literal,
        }
        selected = selectors[self.cat](target)
        if max_targets is not None:
            selected = selected[:max_targets]
        return set(selected)

    def lowestn(self, target: Set[E]) -> list[E]:
        return sorted(target.keptset, key=lambda n: n.total)[: self.num]

    def highestn(self, target: Set[E]) -> list[E]:
        return sorted(target.keptset, key=lambda n: n.total, reverse=True)[: self.num]

    def lessthan(self, target: Set[E]) -> list[E]:
        return [n for n in target.keptset if n.total < self.num]

    def morethan(self, target: Set[E]) -> list[E]:
        return [n for n in target.keptset if n.total > self.num]

    def literal(self, target: Set[E]) -> list[E]:
        return [n for n in target.keptset if n.total == self.num]

    def __str__(self) -> str:
        if self.cat:
            return f'{self.cat}{self.num}'
        return str(self.num)

    def __repr__(self) -> str:
        return f'<SetSelector cat={self.cat} num={self.num}>'
