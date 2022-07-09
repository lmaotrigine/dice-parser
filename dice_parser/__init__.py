from . import dice_ast as ast  # type: ignore
from . import utils as utils
from .dice import *
from .errors import *
from .expression import *
from .stringifiers import *

_roller = Roller()
roll = _roller.roll
parse = _roller.parse
