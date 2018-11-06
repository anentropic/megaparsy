import parsy

from megaparsy.utils import try_


def test_try():
    p = try_(parsy.string('let')) + parsy.string('lexical')
    s = "lexical"
    val = p.parse(s)
    assert val == 'lexical'
