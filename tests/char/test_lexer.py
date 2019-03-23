import operator
import re

from hypothesis import given, strategies as st
import parsy
import pytest

from megaparsy import char
from megaparsy.char.lexer import (
    indent_block,
    indent_guard,
    IndentMany,
    IndentNone,
    IndentSome,
    line_fold,
    non_indented,
    skip_line_comment,
)
from megaparsy.lexer import space, lexeme, symbol


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


def test_indent_guard():
    p = indent_guard(space(), operator.gt, 4)

    # too short
    with pytest.raises(parsy.ParseError):
        p.parse(' ' * 2)

    # only equal, we requested >
    with pytest.raises(parsy.ParseError):
        p.parse(' ' * 4)

    # indent is > 4, returns current indent
    val = p.parse(' ' * 6)
    assert val == 6


def test_non_indented():
    """
    Returns the result of content-consuming parser if the start pos is indented
    else raises ParseError
    """
    p = non_indented(space(), symbol('one'))

    s = """
one
"""
    val = p.parse(s)
    assert val == 'one'

    s = """
    one
"""
    with pytest.raises(parsy.ParseError):
        p.parse(s)


@pytest.mark.parametrize('s', [
    """one
    two
    three
        four
five""",
    """    one
        two
        three
            four
    five""",
])
def test_line_fold(s):
    """
    `line_fold` collects all items matching the parser returned from your
    callback which are at a greater indent than the start position.
    """

    def callback(sc_):
        @parsy.generate
        def parser():
            return (yield lexeme(parsy.regex(r'\w+'), sc_).many())

        return parser

    p = line_fold(space(), callback) << parsy.regex(r'\w+')  # discard the 'five'
    val = p.parse(s)
    assert val == [
        'one',
        'two',
        'three',
        'four',
    ]


@pytest.fixture(params=[" ", "\t"])
def whitespace_char(request):
    return request.param


@pytest.fixture(params=range(2, 9))
def indent_level(request):
    return request.param


symbol_a = 'aaa'
symbol_b = 'bbb'
symbol_c = 'ccc'


def get_col(str_):
    """
    Find position of first non-whitespace char in `str_`
    """
    # type: (str) -> int
    return re.search(r'[^\s]', str_).start()


sc = space(parsy.regex(r'( |\t)+').result(''))

scn = space(char.space1)


@st.composite
def make_indent_(draw, val, size):
    """
    Indent `val` by `size` using either space or tab, with random trailing
    space or tab chars appended.
    Will sometimes randomly ignore `size` param.
    """
    whitespace_char = st.text(' \t', min_size=1, max_size=1)
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
    space or tab chars appended. Followed by one or more line breaks.
    Will sometimes randomly ignore `size` param.
    """
    eol = draw(st.one_of(
        st.text('\n', min_size=1, max_size=1),
        st.text('\n', min_size=1),
    ))
    indented_val = draw(make_indent_(val, size))
    return ''.join([indented_val, eol])


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
    indent_level = draw(st.integers(min_value=1, max_value=10))
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

    cols = [get_col(l) for l in lines]

    lvlc = indent_block(
        p_space_consumer=scn,
        p_reference=symbol(symbol_c, sc).result(IndentNone(symbol_c))
    )
    lvlb = indent_block(
        p_space_consumer=scn,
        p_reference=symbol(symbol_b, sc).result(IndentSome(None, lambda l: (symbol_b, l), lvlc))
    )
    lvla = indent_block(
        p_space_consumer=scn,
        p_reference=symbol(symbol_a, sc).result(IndentMany(indent_level, lambda l: (symbol_a, l), lvlb))
    )

    s = ''.join(lines)
    p = lvla << parsy.eof

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
