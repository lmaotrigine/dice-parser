dice-parser
===========

A fast, powerful, and extensible dice engine for D&D, d20 systems, and
any other system that needs dice!

Key features
------------

-  Quick to start - just use ``dice_parser.roll()``!
-  Optimised for speed and memory efficiency
-  Highly extensible API for custom behaviour and dice stringification
-  Built-in execution limits against malicious dice expressions
-  Tree-based dice representation for easy traversal

Installing
----------

**Requires Python 3.10+**.

.. code:: bash

   python3 -m pip install git+https://github.com/lmaotrigine/dice-parser@main

Quickstart
----------

.. code:: python

   >>> import dice_parser as dice
   >>> result = dice.roll('1d20+5')
   >>> str(result)
   '1d20 (10) + 5 = `15`'
   >>> result.total
   15
   >>> result.crit
   <CritType.NORMAL: 0>
   >>> str(result.ast)
   '1d20 + 5'

Dice Syntax
-----------

This is the grammar supported by the dice parser, roughly ordered by how
rightly the grammar binds.

Numbers
~~~~~~~

These are the atoms used at the base of the syntax tree.

+---------+------------------------------------+-----------------------+--------------------------------------+
| Name    | Syntax                             | Description           | Examples                             |
+=========+====================================+=======================+======================================+
| literal | ``INT``, ``DECIMAL``               | A literal             | ``1``, ``0.5``,                      |
+---------+------------------------------------+-----------------------+--------------------------------------+
| dice    | ``INT? "d" (INT \| "%")``          | A set of die.         | ``d20``, ``3d6``                     |
+---------+------------------------------------+-----------------------+--------------------------------------+
| set     | ``"(" (num ("," num)* ","?)? ")"`` | A set of expressions. | ``()``, ``(2,)``, ``(1, 3+3, 1d20)`` |
+---------+------------------------------------+-----------------------+--------------------------------------+

Note that ``(3d6)`` is equivalent to ``3d6``, but ``(3d6,)`` is the set
containing a single element ``3d6``.

Set operations
~~~~~~~~~~~~~~

These operations can be performed on dice and sets.

Grammar
^^^^^^^

+-------+-----------------+-----------------------------+-------------+
| Name  | Syntax          | Description                 | Examples    |
+=======+=================+=============================+=============+
| s     | ``opera         | An operation on a set (see  | ``kh3``,    |
| et_op | tion selector`` | below).                     | ``ro<3``    |
+-------+-----------------+-----------------------------+-------------+
| sel   | ``seltype INT`` | A selection on a set (see   | ``3``,      |
| ector |                 | below).                     | ``h1``,     |
|       |                 |                             | ``>2``      |
+-------+-----------------+-----------------------------+-------------+

Operators
^^^^^^^^^

Operators are always followed by a selector, and operate on the items in
the set that match the selector.

+--------+----------+------------------------------------------------------+
| Syntax | Name     | Description                                          |
+========+==========+======================================================+
| k      | keep     | Keeps all matched values.                            |
+--------+----------+------------------------------------------------------+
| p      | drop     | Drops all matched values.                            |
+--------+----------+------------------------------------------------------+
| rr     | reroll   | Rerolls all matched values until none match. (Dice   |
|        |          | only)                                                |
+--------+----------+------------------------------------------------------+
| ro     | reroll   | Rerolls all matched values once. (Dice only)         |
|        | once     |                                                      |
+--------+----------+------------------------------------------------------+
| ra     | reroll   | Rerolls up to one matched value once, keeping the    |
|        | and add  | original roll. (Dice only)                           |
+--------+----------+------------------------------------------------------+
| e      | explode  | Rolls another die for each matched value. (Dice      |
|        | on       | only)                                                |
+--------+----------+------------------------------------------------------+
| mi     | minimum  | Sets the minimum value of each die. (Dice only)      |
+--------+----------+------------------------------------------------------+
| ma     | maximum  | Sets the maximum value of each die. (Dice only)      |
+--------+----------+------------------------------------------------------+

Selectors
^^^^^^^^^

Selectors select from the remaining kept values in a set.

+----------+-------------+-------------------------------------------------+
| Syntax   | Name        | Description                                     |
+==========+=============+=================================================+
| X        | literal     | All values in this set that are literally this  |
|          |             | value.                                          |
+----------+-------------+-------------------------------------------------+
| hX       | highest X   | The highest X values in the set.                |
+----------+-------------+-------------------------------------------------+
| lX       | lowest X    | The lowest X values in the set.                 |
+----------+-------------+-------------------------------------------------+
| >X       | greater     | All values in this set greater than X.          |
|          | than X      |                                                 |
+----------+-------------+-------------------------------------------------+
| <X       | less than X | All values in this set less than X.             |
+----------+-------------+-------------------------------------------------+

Unary Operations
~~~~~~~~~~~~~~~~

====== ======== ========================
Syntax Name     Description
====== ======== ========================
+X     positive Does nothing.
-X     negative The negative value of X.
====== ======== ========================

Binary Operations
~~~~~~~~~~~~~~~~~

====== ==============
Syntax Name
====== ==============
X \* Y multiplication
X / Y  division
X // Y int division
X % Y  modulo
X + Y  addition
X - Y  subtraction
X == Y equality
X >= Y greater/equal
X <= Y less/equal
X > Y  greater than
X < Y  less than
X != Y inequality
====== ==============

Examples
~~~~~~~~

.. code:: python

   >>> from dice_parser import roll
   >>> r = roll('4d6kh3')  # highest 3 of four 6-sided dice
   >>> r.total
   14
   >>> str(r)
   '4d6kh3 (4, 4, **6**, ~~3~~) = `14`'

   >>> r = roll('2d6ro<3')  # roll 2d6, then reroll any 1s or 2s once
   >>> r.total
   9
   >>> str(r)
   '2d6ro<3 (**~~1~~**, 3, **6**) = `9`'

   >>> r = roll('8d6mi2')  # roll 8d6, with each die having a minimum roll of 2
   >>> r.total
   33
   >>> str(r)
   '8d6mi2 (1 -> 2, **6**, 4, 2, **6**, 2, 5, **6**) = `33`'

   >>> r = roll('(1d4 + 1, 3, 2d6kl1)kh1')  # the highest of 1d4+1, 3, and the lower of 2d6
   >>> r.total
   3
   >>> str(r)
   '(1d4 (2) + 1, ~~3~~, ~~2d6kl1 (2, 5)~~)kh1 = `3`'

Custom Stringifier
------------------

The default stringifier formats the result of each roll in Markdown,
which may not be useful in your application. To change this behaviour,
you can create a subclass of :class:`dice_parser.Stringifier` [`View Source <https://github.com/lmaotrigine/dice-parser/blob/main/dice_parser/stringifiers.py>`__] (or
``dice_parser.SimpleStringifier`` as a starting point), and implement
the ``str_*`` methods to customize how your dice tree is stringified

Then, simply pass an instance of your stringifier into the ``roll()``
function!

.. code:: python

   >>> import dice_parser
   >>> class MyStringifier(dice_parser.SimpleStringifier):
   ...     def stringify_node(self, node):
   ...         if not node.kept:
   ...             return 'X'
   ...         return super().stringify_node(node)
   ...
   ...     def str_expression(self, node):
   ...         return f'The result of the roll {self.stringify_node(node.roll)} was {int(node.total)}'
   ...
   >>> result = dice_parser.roll('4d6e6kh3', stringifier=MyStringifier())
   >>> str(result)
   'The result of the roll 4d6e6kh3 (X, 5, 6!, 6!, X, X) was 17'

Annotations and Comments
------------------------

Each dice node supports value annotations - i.e., a method to “tag”
parts of a roll with some indicator. For example,

.. code:: python

   >>> from dice_parser import roll
   >>> str(roll('3d6 [fire] + 1d4 [piercing]'))
   '3d6 (3, 2, 2) [fire] + 1d4 (3) [piercing] = `10`'

   >>> str(roll('-(1d8 + 3) [healing]'))
   '-(1d8 (7) + 3) [healing] = `-10`'

   >>> str(roll('(1 [one], 2 [two] 3 [three])'))
   '(1 [one], 2 [two], 3 [three]) = `6`'

are all examples of valid annotations. Annotations are purely visual and
do not affect the evaluation of the roll by default.

Additionally, when ``allow_comments=True`` is passed to ``roll()``, the
result of the roll may have a comment:

.. code:: python

   >>> from dice_parser import roll
   >>> result = roll('1d20 I rolled a d20', allow_comments=True)
   >>> str(result)
   '1d20 (13) = `13`'
   >>> result.comment
   'I rolled a d20'

Note that while ``allow_comments`` is enabled, AST caching is disabled,
which may lead to slightly worse performance.

Performance
-----------

By default, the parser caches the 256 most frequently used dice
expressions in an LFU cache, allowing for a significant speedup when
rolling many of the same kinds of rolls. This caching is disabled when
``allow_comments`` is True.

With caching:

.. code:: bash

   $ python -m timeit -s "from dice_parser import roll" "roll('1d20')"
   10000 loops, best of 5: 21.6 usec per loop
   $ python -m timeit -s "from dice_parser import roll" "roll('100d20')"
   500 loops, best of 5: 572 usec per loop
   $ python3 -m timeit -s "from dice_parser import roll; expr='1d20+'*50+'1d20'" "roll(expr)"
   500 loops, best of 5: 732 usec per loop
   $ python3 -m timeit -s "from dice_parser import roll" "roll('10d20rr<20')"
   1000 loops, best of 5: 1.13 msec per loop

Without caching:

.. code:: bash

   $ python3 -m timeit -s "from dice_parser import roll" "roll('1d20')"
   5000 loops, best of 5: 61.6 usec per loop
   $ python3 -m timeit -s "from dice_parser import roll" "roll('100d20')"
   500 loops, best of 5: 620 usec per loop
   $ python3 -m timeit -s "from dice_parser import roll; expr='1d20+'*50+'1d20'" "roll(expr)"
   500 loops, best of 5: 2.1 msec per loop
   $ python3 -m timeit -s "from dice_parser import roll" "roll('10d20rr<20')"
   1000 loops, best of 5: 1.26 msec per loop
