from __future__ import annotations

from lark.lexer import Token

__all__ = ('RollError', 'RollSyntaxError', 'RollValueError', 'TooManyRolls')


class RollError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class RollSyntaxError(RollError):
    def __init__(self, line: int, col: int, got: Token | str, expected: set[str]) -> None:
        self.line = line
        self.col = col
        self.got = got
        self.expected = expected
        msg = f'Unexpected input on line {line}, col {col}: expected {", ".join([str(ex) for ex in expected])}, got {got}'
        super().__init__(msg)


class RollValueError(RollError):
    pass


class TooManyRolls(RollError):
    pass
