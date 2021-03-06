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

from collections.abc import Callable
from enum import IntEnum
from typing import TypeVar

import lark.exceptions as lark

from . import dice_ast as ast
from . import utils
from .cache import LFUCache
from .errors import *
from .expression import *
from .stringifiers import MarkdownStringifier, Stringifier


__all__ = ('CritType', 'AdvType', 'RollContext', 'RollResult', 'Roller')

POSSIBLE_COMMENT_AMBIGUITIES = {
    '*',
}

T = TypeVar('T', bound=ast.ChildMixin)
N = TypeVar('N', bound=ast.Node)
E = TypeVar('E', bound=Number)


class CritType(IntEnum):
    """An enum representing the crit type of a roll."""

    NONE = 0
    CRIT = 1
    FAIL = 2


class AdvType(IntEnum):
    """An enum representing the advantage a roll should be made at."""

    NONE = 0
    ADV = 1
    DIS = -1


class RollContext:
    """Used to track information about rolls to ensure all rolls halt eventually.

    Attributes
    ----------
    max_rolls: :class:`int`
        The maximum number of rolls allowed per context invocation
    """

    def __init__(self, max_rolls: int = 1000) -> None:
        self.max_rolls = max_rolls
        self.rolls = 0
        self.reset()

    def reset(self) -> None:
        """Called at the start of each new roll."""
        self.rolls = 0

    def count_roll(self, n: int = 1) -> None:
        """Called each time a die is about to be rolled.

        Parameters
        ----------
        n: :class:`int`
            The number of rolls about to be made

        Raises
        ------
        TooManyRolls
            The number of rolls exceed the maximum rolls allowed in this context
        """
        self.rolls += n
        if self.rolls > self.max_rolls:
            raise TooManyRolls('Too many dice rolled.')


class RollResult:
    """Holds information about the result of a roll.

    Instances should generally not be constructed manually.

    .. container:: operations

        .. describe:: int(x)

            Return the integer result of the roll (rounded towards 0).

        .. describe:: str(x)

            Return the string result of the roll.

        .. describe:: float(x)

            Return the result of the roll without rounding.

    Attributes
    ----------
    ast: :class:`ast.Node`
        The abstract syntax tree of the dice expression that was rolled
    expr: :class:`Expression`
        The Expression representation of the result of the roll.
    comment: Optional[:class:`str`]
        If `allow_comments` was True and a comment was found, the comment. Otherwise, None.
    """

    def __init__(self, the_ast: ast.Node, the_roll: Expression, stringifier: Stringifier) -> None:
        self.ast = the_ast
        self.expr = the_roll
        self.stringifier = stringifier
        self.comment = the_roll.comment

    @property
    def total(self) -> int:
        """The integer result of the roll (rounded towards 0)."""
        return int(self.expr.total)

    @property
    def result(self) -> str:
        """The string result of the roll. Equivalent to ``stringifier.stringify(self.expr)``."""
        return self.stringifier.stringify(self.expr)

    @property
    def crit(self) -> CritType:
        """If the leftmost node was Xd20kh1, returns :class:`CritType.CRIT` if the roll was a 20 and
        :class:`CritType.FAIL` if the roll was a 1.
        Returns :class:`CritType.NONE` otherwise.
        """
        left = self.expr
        while left.children:
            left = left.children[0]
        if not isinstance(left, Dice):
            return CritType.NONE

        if not (len(left.keptset) == 1 and left.size == 20):
            return CritType.NONE

        if left.total == 1:
            return CritType.FAIL
        elif left.total == 20:
            return CritType.CRIT
        return CritType.NONE

    def __str__(self) -> str:
        return self.result

    def __int__(self) -> int:
        return self.total

    def __float__(self) -> float:
        return self.expr.total

    def __repr__(self) -> str:
        return f'<RollResult total={self.total}>'


class Roller:
    """The main class responsible for parsing dice into an AST and evaluating that AST.

    Attributes
    ----------
    context: :class:`RollContext`
        The roll context associated with this roller.
    """

    def __init__(self, context: RollContext | None = None) -> None:
        if context is None:
            context = RollContext()
        self._parse_cache = LFUCache(256)
        self.context: RollContext = context

    def _get_evaluator(self, _type: type[N]) -> Callable[[N], Number]:
        _nodes = {
            ast.Expression: self._eval_expression,
            ast.AnnotatedNumber: self._eval_annotatednumber,
            ast.LiteralNode: self._eval_literal,
            ast.Parenthetical: self._eval_parenthetical,
            ast.UnOp: self._eval_unop,
            ast.BinOp: self._eval_binop,
            ast.OperatedSet: self._eval_operatedset,
            ast.NumberSet: self._eval_numberset,
            ast.OperatedDice: self._eval_operateddice,
            ast.DiceNode: self._eval_dice,
        }
        return _nodes[_type]  # type: ignore

    def roll(
        self,
        expr: str | ast.Node,
        stringifier: Stringifier | None = None,
        allow_comments: bool = False,
        advantage: AdvType = AdvType.NONE,
    ) -> RollResult:
        """Rolls the dice.

        Parameters
        ----------
        expr: Union[:class:`str`, :class:`ast.Node`]
            The dice expression
        stringifier: :class:`Stringifier`
            The stringifier to stringify the result. Defaults to :class:`MarkdownStringifier`
        allow_comments: :class:`bool`
            Whether to parse for comments after the main roll expression
            (disables cache, can lead to possible performance issues)
        advantage: :class:`AdvType`
            If the roll should be made at (dis)advantage. Only applies if the leftmost node s 1d20

        Returns
        -------
        :class:`RollResult`
            The result of the roll
        """
        if stringifier is None:
            stringifier = MarkdownStringifier()
        self.context.reset()

        if isinstance(expr, str):
            dice_tree = self.parse(expr, allow_comments)
        else:
            dice_tree = expr

        if advantage is not AdvType.NONE:
            dice_tree = utils.ast_adv_copy(dice_tree, advantage)
        dice_expr: Expression = self._eval(dice_tree)  # type: ignore
        return RollResult(dice_tree, dice_expr, stringifier)

    def parse(self, expr: str, allow_comments: bool = False) -> ast.Expression:
        """Parses a dice expression into an AST.

        Parameters
        ----------
        expr: :class:`str`
            The dice to roll
        allow_comments: :class:`bool`
            Whether to parse for comments after the main roll expression
            (disables cache, can lead to possible performance issues)

        Returns
        -------
        :class:`ast.Expression`
            An AST representing the dice expression.
        """
        try:
            if not allow_comments:
                return self._parse_no_comment(expr)
            else:
                return self._parse_with_comments(expr)
        except lark.UnexpectedToken as ut:
            raise RollSyntaxError(ut.line, ut.column, ut.token, ut.expected)
        except lark.UnexpectedCharacters as uc:
            raise RollSyntaxError(uc.line, uc.column, expr[uc.pos_in_stream], uc.allowed)

    def _parse_no_comment(self, expr: str) -> ast.Expression:
        clean_expr = expr.replace(' ', '')
        if clean_expr in self._parse_cache:
            return self._parse_cache[clean_expr]  # type: ignore
        dice_tree = ast.parser.parse(expr, start='expr')
        self._parse_cache[clean_expr] = dice_tree
        return dice_tree  # type: ignore

    def _parse_with_comments(self, expr: str) -> ast.Expression:
        try:
            return ast.parser.parse(expr, start='commented_expr')  # type: ignore
        except lark.UnexpectedInput as ui:
            successful_fragment = expr[: ui.pos_in_stream]
            for op in POSSIBLE_COMMENT_AMBIGUITIES:
                if successful_fragment.endswith(op):
                    successful_fragment = successful_fragment[: -len(op)]
                    force_comment = expr[len(successful_fragment) :]
                    break
            else:
                raise
            result = ast.parser.parse(successful_fragment, start='commented_expr')
            result.comment = force_comment  # type: ignore
            return result  # type: ignore

    def _eval(self, node: ast.Node) -> Number:
        handler = self._get_evaluator(type(node))
        return handler(node)

    def _eval_expression(self, node: ast.Expression) -> Expression:
        return Expression(self._eval(node.roll), node.comment)

    def _eval_annotatednumber(self, node: ast.AnnotatedNumber) -> Number:
        target = self._eval(node.value)
        target.annotation = ''.join(node.annotations)
        return target

    def _eval_literal(self, node: ast.LiteralNode) -> Literal:
        return Literal(node.value)

    def _eval_parenthetical(self, node: ast.Parenthetical) -> Parenthetical:
        return Parenthetical(self._eval(node.value))

    def _eval_unop(self, node: ast.UnOp) -> UnOp:
        return UnOp(node.op, self._eval(node.value))

    def _eval_binop(self, node: ast.BinOp) -> BinOp:
        return BinOp(self._eval(node.left), node.op, self._eval(node.right))

    def _eval_operatedset(self, node: ast.OperatedSet) -> Set:
        target: Set = self._eval(node.value)  # type: ignore
        for op in node.operations:
            the_op = SetOperator.from_ast(op)
            the_op.operate(target)
            target.operations.append(the_op)
        return target

    def _eval_numberset(self, node: ast.NumberSet) -> Set:
        return Set([self._eval(n) for n in node.values])

    def _eval_operateddice(self, node: ast.OperatedDice) -> Set[Die]:
        return self._eval_operatedset(node)

    def _eval_dice(self, node: ast.DiceNode) -> Dice:
        return Dice.new(node.num, node.size, context=self.context)
