import logging
from functools import wraps

import parsy


logger = logging.getLogger(__name__)


def try_(p):
    """
    When arbitrary look ahead returning a parser is needed.
    (if you don't want `.optional()` which returns a result)

    You can do this in parsy with p0 | p1 | ...
    but you may not have a p1
    """
    return p | parsy.success('')


def from_maybe(default, maybe):
    """
    Helper for translating code using Haskell's:

        fromMaybe default maybe

    (typically, the argument order feels back-to-front for python code
    but it's easier to translate code if we keep it the same)
    """
    return maybe if maybe is not None else default


CARET = "\u2038"


def debug(p, label="", context=12):

    @parsy.Parser
    @wraps(p)
    def wrapped(stream, index):
        left = stream[max(0, index - context): index]
        right = stream[index: index + context]
        result = parsy.line_info(stream, index)
        line, col = result.value
        logger.debug(f"{label}({line}:{col})|{left}{CARET}{right}")

        return p(stream, index)

    return wrapped
