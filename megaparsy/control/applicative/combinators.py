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


def nested(p_open, p_close, p_token, p_sep_by):

    @parsy.generate
    def group():
        return (
            yield between(
                p_open,
                p_close,
                expr.sep_by(p_sep_by),
            )
        )

    expr = p_token | group
    return expr
