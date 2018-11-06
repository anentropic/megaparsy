import parsy

from megaparsy import char


def space(
        p_space=char.space,
        p_line_comment=parsy.fail('line-comment'),
        p_block_comment=parsy.fail('block-comment')
        ):
    """
    Produces a parser that consumes white space in general. It's expected
    that you create such a parser once and pass it to other functions in this
    package as needed (when you see `p_space_consumer` in documentation,
    usually it means that something like `space()` is expected there).

    Args:
        p_space_chars: is used to parse blocks of space characters.
            You can use 'char.space' for this purpose, or your own parser
            (if you don't want to automatically consume newlines, for example).
            Make sure the parser does not succeed on empty input though.
        p_line_comment: is used to parse line comments. You can use
            'megaparsy.skip_line_comment` if you don't need anything special.
        blockComment: is used to parse block (multi-line) comments. You can
            use `megaparsy.skip_block_comment` or `skip_block_comment_nested`
            if you don't need anything special.

    If you don't want to match a kind of comment, simply pass `parsy.fail()`
    and `space` will just move on or finish depending on whether there is more
    white space for it to consume.
    """
    return parsy.success('')\
        .skip(p_space.optional())\
        .skip(p_line_comment.optional())\
        .skip(p_block_comment.optional())


def lexeme(p_lexeme, p_space=char.space):
    """
    This is a wrapper for "lexemes". Typical usage is to supply the first
    argument (parser that consumes white space, e.g. `megaparsy.space()`)
    and use the resulting function to wrap parsers for every lexeme.

    Args:
        p_lexeme: parser that matches a single lexemes
        p_space: space parser, i.e. delimiting end of lexeme
    """
    return p_lexeme << p_space


def symbol(symbol, p_space=char.space):
    return lexeme(parsy.string(symbol), p_space=p_space)
