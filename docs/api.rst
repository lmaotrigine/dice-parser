Class Reference
===============

Looking for information on :class:`dice_parser.Expression` or :class:`dice_parser.ast.Node`? Check out
:doc:`Expression Tree </expression>` for information on the Expression returned by a roll, or
:doc:`Abstract Syntax Tree </ast>` for the AST returned by a parse.

Dice
----
.. autoclass:: dice_parser.Roller
  :members:

.. autoclass:: dice_parser.RollResult
  :members:

.. autoclass:: dice_parser.RollContext
  :members:

Enumerations
------------

.. autoclass:: dice_parser.AdvType
  :members:

  .. attribute:: NONE
      :type: int

      Equivalent to ``0``. Represents no advantage.
  
  .. attribute:: ADV
      :type: int

      Equivalent to ``1``. Represents advantage.
  
  .. attribute:: DIS
      :type: int

      Equivalent to ``-1``. Represents disadvantage.

.. autoclass:: dice_parser.CritType
  :members:

  .. attribute:: NONE
      :type: int

      Equivalent to ``0``. Represents no crit.
  
  .. attribute:: CRIT
      :type: int

      Equivalent to ``1``. Represents a critical hit (a natural 20 on a d20).
  
  .. attribute:: FAIL
      :type: int

      Equivalent to ``-1``. Represents a critical fail (a natural 1 on a d20).

Stringifiers
------------
.. autoclass:: dice_parser.Stringifier
  :members:

  .. automethod:: str_expression
  
  .. automethod:: str_literal
  
  .. automethod:: str_unop
  
  .. automethod:: str_binop
  
  .. automethod:: str_parenthetical

  .. automethod:: str_set
  
  .. automethod:: str_dice
  
  .. automethod:: str_die

.. autoclass:: dice_parser.SimpleStringifier

.. autoclass:: dice_parser.MarkdownStringifier


Exceptions
----------
.. autoclass:: dice_parser.RollError
  :members:

.. autoclass:: dice_parser.RollSyntaxError
  :members:

.. autoclass:: dice_parser.RollValueError
  :members:

.. autoclass:: dice_parser.TooManyRolls
  :members:
