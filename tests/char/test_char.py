import parsy
import pytest

from megaparsy import char


def test_newline():
    p = char.newline
    s = "\n"
    val = p.parse(s)
    assert val == s


def test_crlf():
    p = char.crlf
    s = "\r\n"
    val = p.parse(s)
    assert val == s


@pytest.mark.parametrize('s,expected', [
    ("\n", "\n"),
    ("\r\n", "\r\n"),
])
def test_eol(s, expected):
    # returns the eol sequence
    p = char.eol
    val = p.parse(s)
    assert val == expected


@pytest.mark.parametrize('s', [
    "\r ",
    "\r",
    "x",
    "",
])
def test_eol_errors(s):
    p = char.eol
    with pytest.raises(parsy.ParseError):
        p.parse(s)


def test_tab():
    p = char.tab
    s = "\t"
    val = p.parse(s)
    assert val == s


def test_space():
    # consumes space up to first non-space character
    p = char.space + parsy.regex(r'.*')
    s = " \n   \t  \r\n  xyz"
    val = p.parse(s)
    assert val == "xyz"


def test_space1():
    # consumes space up to first non-space character
    p = char.space1 + parsy.regex(r'.*')
    s = " \n   \t  \r\n  xyz"
    val = p.parse(s)
    assert val == "xyz"


@pytest.mark.parametrize('s', [
    "xyz",
    "",
])
def test_space1_error(s):
    # consumes space up to first non-space character
    p = char.space1 + parsy.regex(r'.*')
    with pytest.raises(parsy.ParseError):
        p.parse(s)
