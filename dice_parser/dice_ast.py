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
import pathlib
from typing import TYPE_CHECKING, Any

from lark.lark import Lark
from lark.lexer import Token
from lark.visitors import Transformer


if TYPE_CHECKING:
    from typing_extensions import Self


class RollTransformer(Transformer):
    _comma = object()

    def expr(self, num) -> Expression:
        return Expression(*num)

    def commented_expr(self, numcomment) -> Expression:
        return Expression(*numcomment)

    def comparison(self, binop) -> BinOp:
        return BinOp(*binop)

    def a_num(self, binop) -> BinOp:
        return BinOp(*binop)

    def m_num(self, binop) -> BinOp:
        return BinOp(*binop)

    def u_num(self, unop) -> UnOp:
        return UnOp(*unop)

    def numexpr(self, num_anno) -> AnnotatedNumber:
        return AnnotatedNumber(*num_anno)

    def literal(self, num) -> LiteralNode:
        return LiteralNode(*num)

    def set(self, opset) -> OperatedSet:
        return OperatedSet(*opset)

    def set_op(self, opsel) -> NodeSetOperator:
        return NodeSetOperator.new(*opsel)

    def setexpr(self, the_set) -> Parenthetical | NumberSet:
        if len(the_set) == 1 and the_set[-1] is not self._comma:
            return Parenthetical(the_set[0])
        elif len(the_set) and the_set[-1] is self._comma:
            the_set = the_set[:-1]
        return NumberSet(the_set)

    def dice(self, opice) -> OperatedDice:
        return OperatedDice(*opice)

    def dice_op(self, opsel) -> NodeSetOperator:
        return NodeSetOperator.new(*opsel)

    def diceexpr(self, dice) -> DiceNode:
        if len(dice) == 1:
            return DiceNode(1, *dice)
        return DiceNode(*dice)

    def selector(self, sel) -> NodeSetSelector:
        return NodeSetSelector(*sel)

    def comma(self, _) -> Any:
        return self._comma


class ChildMixin:
    """A mixin that tree nodes must implement to support tree traveral utilities."""

    @property
    def children(self) -> list[Self]:
        """A list of this node's children."""
        raise NotImplementedError

    @property
    def left(self) -> Self | None:
        """The node's leftmost child, if any."""
        return self.children[0] if self.children else None

    @left.setter
    def left(self, value: Self) -> None:
        self.set_child(0, value)

    @property
    def right(self) -> Self | None:
        """The node's rightmost child, if any."""
        return self.children[-1] if self.children else None

    @right.setter
    def right(self, value: Self) -> None:
        self.set_child(-1, value)

    def _child_set_check(self, index: int) -> None:
        if index > (len(self.children) - 1) or index < -len(self.children):
            raise IndexError

    def set_child(self, index: int, value: Self) -> None:
        """Sets the child at a specific index of the object.

        Parameters
        ----------
        index: :class:`int`
            The index of the value to set
        value: :class:`ChildMixin`
            The new value to set it to
        """
        self._child_set_check(index)
        raise NotImplementedError


class Node(abc.ABC, ChildMixin):
    """The base class for all AST nodes.

    A node has no specific attributes, but supports all methods in :class:`~dice_parser.ast.ChildMixin` for traversal.
    """

    def set_child(self, index: int, value: Node) -> None:
        """Sets the a child at a specific index of this Node.

        Parameters
        ----------
        index: :class:`int`
            Which child to set
        value: :class:`Node`
            The Node to set it to
        """
        super().set_child(index, value)

    @property
    def children(self) -> list[Node]:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class Expression(Node):
    """Expressions are usually the root of all ASTs.

    Attributes
    ----------
    roll: :class:`Node`
        The subtree representing the expression's roll.
    comment: Optional[:class:`str`]
        The comment of this expression.
    """

    __slots__ = ('roll', 'comment')

    def __init__(self, roll: Node, comment: str | None = None) -> None:
        self.roll = roll
        self.comment = str(comment) if comment is not None else None

    @property
    def children(self) -> list[Node]:
        return [self.roll]

    def set_child(self, index: int, value: Node) -> None:
        self._child_set_check(index)
        self.roll = value

    def __str__(self) -> str:
        if self.comment:
            return f'{self.roll} {self.comment}'
        return f'{self.roll}'


class AnnotatedNumber(Node):
    """Represents a value with an annotation.

    Attributes
    ----------
    value: :class:`Node`
        The subtree representing the annotated value
    annotations: List[:class:`str`]
        The annotation on the value
    """

    __slots__ = ('value', 'annotations')

    def __init__(self, value: Node, *annotations: Token | str) -> None:
        super().__init__()
        self.value = value
        self.annotations = [str(a).strip() for a in annotations]

    @property
    def children(self) -> list[Node]:
        return [self.value]

    def set_child(self, index: int, value: Node) -> None:
        self._child_set_check(index)
        self.value = value

    def __str__(self) -> str:
        return f'{self.value} {"".join(self.annotations)}'


class LiteralNode(Node):
    """
    Attributes
    ----------
    value: Union[:class:`int`, :class:`float`]
        The literal number represented.
    """

    __slots__ = ('value',)

    def __init__(self, value: Token | int | float) -> None:
        super().__init__()
        if isinstance(value, Token):
            self.value = int(value) if value.type == 'INTEGER' else float(value)
        else:
            self.value = value

    @property
    def children(self) -> list[Node]:
        return []

    def __str__(self) -> str:
        return str(self.value)


class Parenthetical(Node):
    """
    Attributes
    ----------
    value: :class:`Node`
        The subtree inside the parentheses
    """

    __slots__ = ('value',)

    def __init__(self, value: Node) -> None:
        super().__init__()
        self.value = value

    @property
    def children(self) -> list[Node]:
        return [self.value]

    def set_child(self, index: int, value: Node) -> None:
        self._child_set_check(index)
        self.value = value

    def __str__(self) -> str:
        return f'({self.value})'


class UnOp(Node):
    """
    Attributes
    ----------
    op: :class:`str`
        The unary operation
    value: :class:`Node`
        The subtree that the operation operates on
    """

    __slots__ = ('op', 'value')

    def __init__(self, op: Token | str, value: Node) -> None:
        super().__init__()
        self.op = str(op)
        self.value = value

    @property
    def children(self) -> list[Node]:
        return [self.value]

    def set_child(self, index: int, value: Node) -> None:
        self._child_set_check(index)
        self.value = value

    def __str__(self) -> str:
        return f'{self.op}{self.value}'


class BinOp(Node):
    """
    Attributes
    ----------
    op: :class:`str`
        The binary operation
    left: :class:`Node`
        The left subtree that the operation operates on
    right: :class:`Node`
        The right subtree that the operation operates on
    """

    __slots__ = ('op', 'left', 'right')

    if TYPE_CHECKING:
        left: Node
        right: Node

    def __init__(self, left: Node, op: Token | str, right: Node) -> None:
        super().__init__()
        self.op = str(op)
        self.left = left
        self.right = right

    @property
    def children(self) -> list[Node]:
        return [self.left, self.right]

    def set_child(self, index: int, value: Node) -> None:
        self._child_set_check(index)
        if self.children[index] is self.left:
            self.left = value
        else:
            self.right = value

    def __str__(self) -> str:
        return f'{self.left} {self.op} {self.right}'


class NodeSetOperator:
    """
    Attributes
    ----------
    op: :class:`str`
        The operation to run on the selected elements of the set
    sels: List[:class:`NodeSetSelector`]
        The selectors that describe how to select operands
    """

    __slots__ = ('op', 'sels')

    IMMEDIATE = {'mi', 'ma'}

    def __init__(self, op: Token | str, sels: list[NodeSetSelector]) -> None:
        self.op = str(op)
        self.sels = sels

    @classmethod
    def new(cls, op: Token | str, sel: NodeSetSelector) -> NodeSetOperator:
        return cls(op, [sel])

    def add_sels(self, sels: list[NodeSetSelector]) -> None:
        self.sels.extend(sels)

    def __str__(self) -> str:
        return ''.join([f'{self.op}{sel}' for sel in self.sels])


class NodeSetSelector:
    """
    Attributes
    ----------
    cat: Optional[:class:`str`]
        The type of selection (lowest, highest, literal, etc)
    num: :class:`int`
        The number to select (highest/lowest etc N or literal N)
    """

    __slots__ = ('cat', 'num')

    def __init__(self, cat: Token | str | None, num: int) -> None:
        self.cat = str(cat) if cat is not None else None
        self.num = int(num)

    def __str__(self) -> str:
        if self.cat:
            return f'{self.cat}{self.num}'
        return str(self.num)


class OperatedSet(Node):
    """
    Attributes
    ----------
    value: :class:`NumberSet`
        The set to be operated on
    operations: Sequence[:class:`NodeSetOperator`]
        The operations to run on the set
    """

    __slots__ = ('value', 'operations')

    def __init__(self, the_set: NumberSet | DiceNode, *operations: NodeSetOperator) -> None:
        super().__init__()
        self.value = the_set
        self.operations = list(operations)
        self._simplify_operations()

    @property
    def children(self) -> list[Node]:
        return [self.value]

    def set_child(self, index: int, value: Node) -> None:
        self._child_set_check(index)
        self.value = value

    def _simplify_operations(self) -> None:
        new_operations = []
        for operation in self.operations:
            if operation.op in NodeSetOperator.IMMEDIATE or not new_operations:
                new_operations.append(operation)
            else:
                last_op = new_operations[-1]
                if operation.op == last_op.op:
                    last_op.add_sels(operation.sels)
                else:
                    new_operations.append(operation)
        self.operations = new_operations

    def __str__(self) -> str:
        return f'{self.value}{"".join([str(op) for op in self.operations])}'


class NumberSet(Node):
    """
    Attributes
    ----------
    values: List[:class:`Node`]
        The elements of the set
    """

    __slots__ = ('values',)

    def __init__(self, values: list[Node]) -> None:
        super().__init__()
        self.values = list(values)

    @property
    def children(self) -> list[Node]:
        return self.values

    def set_child(self, index: int, value: Node) -> None:
        self._child_set_check(index)
        self.values[index] = value

    def __str__(self) -> str:
        out = ', '.join([str(v) for v in self.values])
        if len(self.values) == 1:
            return f'({out},)'
        return f'({out})'

    def __copy__(self) -> NumberSet:
        return NumberSet(values=self.values.copy())


class OperatedDice(OperatedSet):
    __slots__ = ()

    def __init__(self, the_dice: DiceNode, *operations: NodeSetOperator) -> None:
        super().__init__(the_dice, *operations)


class DiceNode(Node):
    """
    Attributes
    ---------
    num: :class:`int`
        The number of dice to roll
    size: :class:`int`
        The number of sides in each die to roll
    """

    __slots__ = ('num', 'size')

    def __init__(self, num: Token | int, size: Token | int | str) -> None:
        super().__init__()
        self.num = int(num)
        if str(size) == '%':
            self.size = str(size)
        else:
            self.size = int(size)

    @property
    def children(self) -> list[Node]:
        return []

    def __str__(self) -> str:
        return f'{self.num}d{self.size}'


GRAMMAR = pathlib.Path(__file__).parent / 'grammar.lark'

with GRAMMAR.open() as fp:
    grammar = fp.read()

parser = Lark(
    grammar,
    start=['expr', 'commented_expr'],
    parser='lalr',
    transformer=RollTransformer(),
    maybe_placeholders=True,
)


if __name__ == '__main__':
    while True:
        parser = Lark(
            grammar, start=['expr', 'commented_expr'], parser='lalr', maybe_placeholders=True
        )
        result = parser.parse(input(), start='expr')
        print(result.pretty())
        print(result)
        expr = RollTransformer().transform(result)
        print(str(expr))
