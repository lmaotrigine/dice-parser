Abstract Syntax Tree
====================

This page documents the structure of the Expression object as returned by :meth:`dice_parser.Roller.parse`. If you're looking
for the Expression object returned by :meth:`dice_parser.Roller.roll`, check out :doc:`Expression Tree </expression>`.

.. autoclass:: dice_parser.ast.ChildMixin
  :members:

.. autoclass:: dice_parser.ast.Node
  :show-inheritance:
  :members:

.. autoclass:: dice_parser.ast.Expression
  :show-inheritance:

.. autoclass:: dice_parser.ast.AnnotatedNumber
  :show-inheritance:

.. autoclass:: dice_parser.ast.LiteralNode
  :show-inheritance:

.. autoclass:: dice_parser.ast.Parenthetical
  :show-inheritance:

.. autoclass:: dice_parser.ast.UnOp
  :show-inheritance:

.. autoclass:: dice_parser.ast.BinOp
  :show-inheritance:

.. autoclass:: dice_parser.ast.OperatedSet
  :show-inheritance:

.. autoclass:: dice_parser.ast.NumberSet
  :show-inheritance:

.. autoclass:: dice_parser.ast.OperatedDice
  :show-inheritance:

.. autoclass:: dice_parser.ast.DiceNode
  :show-inheritance:

.. autoclass:: dice_parser.ast.NodeSetOperator
  :members:

.. autoclass:: dice_parser.ast.NodeSetSelector
  :members:
