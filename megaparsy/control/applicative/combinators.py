import parsy


def between(p_open, p_close, p):
    """
    -- | @'between' open close p@ parses @open@, followed by @p@ and @close@.
    -- Returns the value returned by @p@.
    --
    -- > braces = between (symbol "{") (symbol "}")

    between_brackets = partial(between, symbol("["), symbol("]"))
    """
    return p_open >> p << p_close


@parsy.generate
def nested(p_open, p_close, p_token):

    @parsy.generate
    def _nested_(p_open, p_close):
        return (yield between(p_open, p_close, nested))

    return (yield p_token | _nested_(p_open, p_close))
