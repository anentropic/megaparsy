import operator
import re
from functools import partial

from hypothesis import given, strategies as st
import parsy
import pytest

from megaparsy import char
from megaparsy.char.lexer import (
    space,
    symbol,
    indent_block,
    indent_guard,
    IndentMany,
    IndentNone,
    IndentSome,
    line_fold,
    non_indented,
    skip_line_comment,
)


SMALL_INT_MAX = 10

symbol_a = 'aaa'
symbol_b = 'bbb'
symbol_c = 'ccc'

sc = space(parsy.regex(r'( |\t)+').result(''))

scn = space(char.space1)

whitespace_char = st.text(' \t', min_size=1, max_size=1)


def get_col(str_):
    """
    Find position of first non-whitespace char in `str_`
    """
    # type: (str) -> int
    return re.search(r'[^\s]', str_).start()


def get_indent(str_):
    """
    Find length of initial whitespace chars in `str_`
    """
    # type: (str) -> int
    match = re.search(r'[^\s]|$', str_)
    if match:
        return match.start()
    else:
        return 0


@st.composite
def make_indent_(draw, val, size):
    """
    Indent `val` by `size` using either space or tab, with random trailing
    space or tab chars appended.
    Will sometimes randomly ignore `size` param.
    """
    trailing = draw(st.text(draw(whitespace_char)))
    indent = draw(st.one_of(
        st.text(draw(whitespace_char), min_size=size, max_size=size),
        st.text(draw(whitespace_char)),
    ))
    return ''.join([indent, val, trailing])


@st.composite
def make_indent(draw, val, size):
    """
    Indent `val` by `size` using either space or tab, with random trailing
    space or tab chars appended.
    Followed by one or more line breaks.
    Will sometimes randomly ignore `size` param.
    """
    eol = draw(st.one_of(
        st.text('\n', min_size=1, max_size=1),
        st.text('\n', min_size=1),
    ))
    indented_val = draw(make_indent_(val, size))
    return ''.join([indented_val, eol])


@st.composite
def make_interspace(draw, val, size):
    """
    Returns `val` either indented or with trailing whitespace (?)

    mkInterspace :: String -> Int -> Gen String
    mkInterspace val size = oneof [si, mkIndent val size]
      where
        si = (++ val) <$> listOf (elements " \t")
    """
    si = st.text(draw(whitespace_char)).flatmap(
        lambda _interspace: st.just(val + _interspace)
    )
    return draw(st.one_of(
        si, make_indent(val, size)
    ))


def test_skip_line_comment():
    # does not need newline to be present
    p = skip_line_comment('//')
    s = "// this line comment doesn't have a newline at the end "
    val = p.parse(s)
    assert val == ""

    # trailing newline is not consumed
    p = skip_line_comment('//') + parsy.string("\n")
    s = "// here we go\n"
    val = p.parse(s)
    assert val == "\n"


@given(make_indent(symbol_a, 0))
def test_non_indented(s):
    """
    Returns the result of content-consuming parser if the start pos is indented
    else raises ParseError
    """
    p = non_indented(scn, symbol(symbol_a, scn))

    i = get_indent(s)

    if i == 0:
        val = p.parse(s)
        assert val == symbol_a
    else:
        with pytest.raises(parsy.ParseError):
            p.parse(s)


@st.composite
def _make_fold(draw):
    """
    Helper strategy for `test_line_fold` case.

    The shape of the content will be the same every time:
      a
      b
      c

    But the chars and size of indent, plus trailing whitespace on each line
    and number of line breaks will all be fuzzed.
    """
    return (
        draw(make_interspace(symbol_a, 0)),
        draw(make_interspace(symbol_b, 1)),
        draw(make_interspace(symbol_c, 1)),
    )


@given(_make_fold())
def test_line_fold(lines):
    """
    `line_fold` collects all items matching the parser returned from your
    callback, and which are at a greater indent than the start position.
    """

    def callback(sc_):
        @parsy.generate
        def parser():
            a = yield symbol(symbol_a, sc_)
            b = yield symbol(symbol_b, sc_)
            c = yield symbol(symbol_c, scn)
            return a, b, c

        return parser

    p = line_fold(scn, callback)

    s = ''.join(lines)

    cols = [get_col(l) for l in lines]
    ends = [l.endswith('\n') for l in lines]

    if ends[0] and cols[1] <= cols[0]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif ends[1] and cols[2] <= cols[0]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    else:
        val = p.parse(s)
        assert val == (
            symbol_a,
            symbol_b,
            symbol_c,
        )


@st.composite
def _make_indented(draw):
    """
    Helper strategy for `test_indent_guard` case.

    The shape of the content will be the same every time:
      a
      a
      a

    But the chars and size of indent, plus trailing whitespace on each line
    and number of line breaks will all be fuzzed.
    """
    indent_level = draw(st.integers(min_value=0, max_value=SMALL_INT_MAX))
    return (
        draw(make_indent(symbol_a, indent_level)),
        draw(make_indent(symbol_a, indent_level)),
        draw(make_indent(symbol_a, indent_level)),
    )


@given(_make_indented())
def test_indent_guard(lines):
    sp = (symbol(symbol_a, sc) << char.eol).result('')
    ip = partial(indent_guard, scn)

    @parsy.generate
    def p():
        x = yield ip(operator.gt, 1)
        return (
            sp
            >> ip(operator.eq, x)
            >> sp
            >> ip(operator.gt, x)
            >> sp
            >> scn
        )

    s = ''.join(lines)

    cols = [get_col(l) for l in lines]

    if cols[0] <= 1:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[1] != cols[0]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[2] <= cols[0]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    else:
        val = p.parse(s)
        assert val == ''


@st.composite
def _make_block(draw):
    """
    Helper strategy for `test_indent_block` case.

    The shape of the content will be the same every time:
    a
        b
          c
        b
          c

    But the chars and size of indent, plus trailing whitespace on each line
    and number of line breaks will all be fuzzed.
    """
    indent_level = draw(st.integers(min_value=1, max_value=SMALL_INT_MAX))
    lines = (
        draw(make_indent(symbol_a, 0)),
        draw(make_indent(symbol_b, indent_level)),
        draw(make_indent(symbol_c, indent_level + 2)),
        draw(make_indent(symbol_b, indent_level)),
        draw(make_indent_(symbol_c, indent_level + 2)),
    )
    return lines, indent_level


@given(_make_block())
def test_indent_block(block):
    lines, indent_level = block

    lvlc = indent_block(
        p_space_consumer=scn,
        p_reference=symbol(symbol_c, sc).result(
            IndentNone(symbol_c)
        )
    )
    lvlb = indent_block(
        p_space_consumer=scn,
        p_reference=symbol(symbol_b, sc).result(
            IndentSome(None, lambda l: (symbol_b, l), lvlc)
        )
    )
    lvla = indent_block(
        p_space_consumer=scn,
        p_reference=symbol(symbol_a, sc).result(
            IndentMany(indent_level, lambda l: (symbol_a, l), lvlb)
        )
    )

    s = ''.join(lines)
    p = lvla << parsy.eof

    cols = [get_col(l) for l in lines]

    if cols[1] <= cols[0]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif indent_level is not None and cols[1] != indent_level:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[2] <= cols[1]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[3] == cols[2]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[3] <= cols[0]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[3] < cols[1]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[3] > cols[1]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    elif cols[4] <= cols[3]:
        with pytest.raises(parsy.ParseError):
            p.parse(s)
    else:
        val = p.parse(s)
        assert val == (
            symbol_a,
            [
                (symbol_b, [symbol_c]),
                (symbol_b, [symbol_c]),
            ]
        )
