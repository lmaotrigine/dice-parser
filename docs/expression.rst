Expression Tree
===============

This page documents the structure of the Expression object as returned by :meth:`dice_parser.RollResult.expr`. If you're looking
for the Expression object returned by :meth:`dice_parser.Roller.parse`, check out :doc:`Abstract Syntax Tree <ast>`.

.. autoclass:: dice_parser.Number

  :members: number, total, set, keptset, drop, children
  :show-inheritance:
  
  .. property:: left

    The leftmost child of this Number
    
    :type: List[Number]
  
  .. automethod:: set_child

.. autoclass:: dice_parser.Expression
  :show-inheritance:


.. autoclass:: dice_parser.Literal
  :show-inheritance:
  :members: explode, update

.. autoclass:: dice_parser.UnOp
  :show-inheritance:

.. autoclass:: dice_parser.BinOp
  :show-inheritance:


.. autoclass:: dice_parser.Parenthetical
  :show-inheritance:

.. autoclass:: dice_parser.Set
  :show-inheritance:

.. autoclass:: dice_parser.Dice
  :show-inheritance:
  :members: roll_another

.. autoclass:: dice_parser.Die
  :show-inheritance:

.. autoclass:: dice_parser.SetOperator
  :members: select, operate

.. autoclass:: dice_parser.SetSelector
  :show-inheritance:
  :members: select
