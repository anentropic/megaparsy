import parsy
import pytest

from megaparsy.lexer import space, lexeme, symbol
from megaparsy.char.lexer import skip_line_comment


@pytest.mark.parametrize('s', [
    '',
    ' ',
    '  ',
    '   \n',
    '\t  ',
])
def test_space(s):
    # whitespace is consumed
    scn = space()
    val = scn.parse(s)
    assert val == ''


@pytest.mark.parametrize('s0,s1', [
    ('', 'x y'),
    (' ', 'x y'),
    ('  ', 'x y'),
    ('   \n', 'x y'),
    ('\t  ', 'x y'),
])
def test_space2(s0, s1):
    # following non-whitespace is not consumed
    p = space() + parsy.regex(r'.*')
    val = p.parse(s0 + s1)
    assert val == s1


@pytest.mark.parametrize('s0,s1', [
    ('', '// comment'),
    (' ', '// comment'),
    ('  ', '// comment'),
    ('   \n', '// comment'),
    ('\t  ', '// comment'),
])
def test_space3(s0, s1):
    # we allow comment parser to do its thing
    # (in this case: skips comment)
    p = space(p_line_comment=skip_line_comment('//'))
    val = p.parse(s0 + s1)
    assert val == ''


def test_lexeme():
    p = lexeme(parsy.regex(r'\w+')).many()
    s = "one two three\nfour five six "
    val = p.parse(s)
    assert val == [
        'one',
        'two',
        'three',
        'four',
        'five',
        'six',
    ]


def test_symbol():
    p = symbol('foo').many()
    s = "foo foo\nfoo "
    val = p.parse(s)
    assert val == ['foo', 'foo', 'foo']
