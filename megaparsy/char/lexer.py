import operator
from collections import namedtuple

import parsy

from megaparsy import char
from megaparsy.utils import try_, from_maybe


OPERATOR_MAP = {
    operator.eq: '==',
    operator.gt: '>',
    operator.lt: '<',
}


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
        p_block_comment: is used to parse block (multi-line) comments. You can
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
    This is a wrapper for "lexemes". Typical usage is to supply the `p_space`
    argument (parser that consumes white space, e.g. `megaparsy.space()`)
    and use the resulting function to wrap parsers for every lexeme.
    (basically: consumes trailing whitespace after a token)

    Args:
        p_lexeme: parser that matches a single lexemes
        p_space: space parser, i.e. delimiting end of lexeme
    """
    return p_lexeme << p_space


def symbol(symbol, p_space=char.space):
    return lexeme(parsy.string(symbol), p_space=p_space)


def skip_line_comment(prefix):
    """
    Given comment prefix this function returns a parser that skips line
    comments. Note that it stops just before the newline character but
    doesn't consume the newline. Newline is either supposed to be consumed by
    'space' parser or picked up manually.
    """
    return (
        parsy.string(prefix).result('') << parsy.regex(r'[^\n]*')
    ).desc('line-comment')


# TODO: skip_block_comment


def indent_guard(p_space_consumer, operator, reference_level):
    """
    `indent_guard` first consumes all white space (indentation) with
    `p_space_consumer` parser, then it checks the column position.
    Ordering between current indentation level and the reference indentation
    level `ref` should be `ord`, otherwise the parser fails. On success the
    current column position is returned.

    When you want to parse a block of indentation, first run this parser with
    arguments like `indentGuard(space, operator.gt, 4)` this will make
    sure you have indentation > 4. Use returned value to check indentation
    on every subsequent line according to syntax of your language.

    Args:
        p_space_consumer: e.g. `megaparsy.space()`
        operator: e.g. `operator.lt|gt|eq` from python stdlib
        reference_level: column value (int index) of reference indent level
            to compare to
    """
    @parsy.generate
    def parser():
        """
        Returns:
            int: current indent level
        """
        yield p_space_consumer
        _, actual = yield parsy.line_info
        if operator(actual, reference_level):
            return actual
        else:
            return parsy.fail(
                'indent_guard: {actual} {op} {ref}'.format(
                    actual=actual,
                    op=OPERATOR_MAP.get(operator, operator.__name__),
                    ref=reference_level,
                )
            )

    return parser


def non_indented(p_space_consumer, p_content):
    """
    -- | Parse a non-indented construction. This ensures that there is no
    -- indentation before actual data. Useful, for example, as a wrapper for
    -- top-level function definitions.

    nonIndented :: MonadParsec e s m
      => m ()              -- ^ How to consume indentation (white space)
      -> m a               -- ^ How to parse actual data
      -> m a
    nonIndented sc p = indentGuard sc EQ pos1 *> p
    """
    return indent_guard(p_space_consumer, operator.eq, 0) >> p_content


def _indented_items(reference_level, next_level, p_space_consumer, p_indented_tokens):
    """
    Grab indented items. This is a helper for `indent_block`, it's not a
    part of the public API.

    Args:
        reference_level: column index to compare indent against
        next_level: column index of anticipated next indent level
        p_space_consumer: e.g. `megaparsy.space()`
        p_indented_tokens: parser to consume the indented items
    """
    def closure():
        """
        Allows us to recursively use `parser`
        """
        @parsy.generate
        def parser():
            """
            Returns:
                List[str]
            """
            yield p_space_consumer
            _, pos = yield parsy.line_info
            done = yield (parsy.eof.result(True)).optional()
            if done:
                return []
            else:
                if pos <= reference_level:
                    return []
                elif pos == next_level:
                    current_val = yield p_indented_tokens
                    more_vals = yield closure()
                    return [current_val] + more_vals
                else:
                    return parsy.fail(
                        '_indented_items: {lvl} == {pos}'.format(
                            lvl=next_level,
                            pos=pos
                        )
                    )

        return parser

    return closure()


IndentNone = namedtuple('IndentNone', ('val',))
IndentMany = namedtuple('IndentMany', ('indent', 'f', 'p'))
IndentSome = namedtuple('IndentSome', ('indent', 'f', 'p'))
# where `f` is Callable[[List[str]], str] returning str result


def indent_block(p_space_consumer, p_reference):
    """
    Parse a “reference” token and a number of other tokens that have
    greater (but the same) level of indentation than that of “reference”
    token. Reference token can influence parsing, see 'IndentOpt' for more
    information.

    Tokens *must not* consume newlines after them. On the other hand, the
    first argument of this function *must* consume newlines among other white
    space characters.

    Args:
        p_space_consumer: e.g. `megaparsy.space()`
        p_reference: parser which should return an instance of one of
            IndentNone | IndentMany | IndentSome
            (return instance e.g. by using `p.result()` when `p` matches)

    data IndentOpt m a b
      = IndentNone a
        -- ^ Parse no indented tokens, just return the value
      | IndentMany (Maybe Pos) ([b] -> m a) (m b)
        -- ^ Parse many indented tokens (possibly zero), use given indentation
        -- level (if 'Nothing', use level of the first indented token); the
        -- second argument tells how to get the final result, and the third
        -- argument describes how to parse an indented token
      | IndentSome (Maybe Pos) ([b] -> m a) (m b)
        -- ^ Just like 'IndentMany', but requires at least one indented token to
        -- be present

    indentBlock sc r = do
      sc
      ref <- indentLevel
      a   <- r
      case a of
        IndentNone x -> sc *> return x
        IndentMany indent f p -> do
          mlvl <- (optional . try) (C.eol *> indentGuard sc GT ref)
          done <- isJust <$> optional eof
          case (mlvl, done) of
            (Just lvl, False) ->
              indentedItems ref (fromMaybe lvl indent) sc p >>= f
            _ -> sc *> f []
        IndentSome indent f p -> do
          pos <- C.eol *> indentGuard sc GT ref
          let lvl = fromMaybe pos indent
          x <- if | pos <= ref -> incorrectIndent GT ref pos
                  | pos == lvl -> p
                  | otherwise  -> incorrectIndent EQ lvl pos
          xs  <- indentedItems ref lvl sc p
          f (x:xs)
    """
    @parsy.generate
    def parser():
        """
        Returns:
            List[str]

        Raises:
            TypeError: if `p_reference` does not return one of
                IndentNone | IndentMany | IndentSome
        """
        yield p_space_consumer
        _, ref_level = yield parsy.line_info
        indent_opt = yield p_reference

        if isinstance(indent_opt, IndentNone):
            # Parse no indented tokens, just return the value
            return p_space_consumer.result(indent_opt.val)

        elif isinstance(indent_opt, IndentMany):
            # Parse none-or-many indented tokens, use given indentation
            # level (if `None`, use level of the first indented token)
            maybe_indent, f, p = indent_opt
            p_indent_guard = indent_guard(p_space_consumer, operator.gt, ref_level)
            maybe_lvl = yield try_(char.eol >> p_indent_guard).optional()
            done = yield (parsy.eof.result(True)).optional()
            if not done and maybe_lvl is not None:
                next_level = from_maybe(maybe_lvl, maybe_indent)
                vals = yield _indented_items(
                    ref_level, next_level, p_space_consumer, p
                )
                return f(vals)
            else:
                return p_space_consumer.result(f([]))

        elif isinstance(indent_opt, IndentSome):
            # Just like `IndentMany`, but requires at least one indented token
            # to be present
            maybe_indent, f, p = indent_opt
            p_indent_guard = indent_guard(p_space_consumer, operator.gt, ref_level)
            pos = yield char.eol >> p_indent_guard
            lvl = from_maybe(pos, maybe_indent)
            if pos <= ref_level:
                parsy.fail(
                    'indent_block: {pos} > {ref}'.format(
                        ref=ref_level,
                        pos=pos,
                    )
                )
            elif pos == lvl:
                current_val = yield p
                more_vals = yield _indented_items(ref_level, lvl, p_space_consumer, p)
                return f([current_val] + more_vals)
            else:
                parsy.fail(
                    'indent_block: {lvl} == {pos}'.format(
                        lvl=lvl,
                        pos=pos,
                    )
                )

        else:
            raise TypeError('Must be one of IndentNone|IndentMany|IndentSome')

    return parser


def line_fold(p_space_consumer, callback):
    r"""
    Create a parser that supports line-folding. The first argument is used
    to consume white space between components of line fold, thus it *must*
    consume newlines in order to work properly. The second argument is a
    `callback` that receives a custom space-consuming parser as argument.

    The callback should return a parser which can consume items in the fold.

    Args:
        p_space_consumer: e.g. `megaparsy.space()`
        callback: see example

    Example:

        def mycallback(sc_):
            @parsy.generate
            def parser():
                return (yield lexeme(parsy.regex(r'\w+'), sc_).many())

            return parser

        my_fold = line_fold(space(), mycallback)
    """
    @parsy.generate
    def parser():
        yield p_space_consumer
        _, current = yield parsy.line_info
        sc_ = try_(
            indent_guard(p_space_consumer, operator.gt, current).result('')
        )
        return callback(sc_) << p_space_consumer

    return parser
