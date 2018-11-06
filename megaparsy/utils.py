import parsy


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
