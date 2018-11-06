#!/usr/bin/env python
import os
import sys
from functools import partial

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import parsy
from megaparsy.lexer import space, lexeme as megaparsy_lexeme
from megaparsy import char
from megaparsy.char.lexer import (
    indent_block,
    IndentMany,
    IndentSome,
    line_fold,
    non_indented,
    skip_line_comment,
)


# parser that matches comments beginning with `#`
line_comment = skip_line_comment("#")

# parser which matches whitespace, including newline
scn = space(char.space1, line_comment)

# parser which only matches ' ' and '\t', but *not* newlines
_space1_no_nl = parsy.regex(r'( |\t)+').result('')
sc = space(_space1_no_nl, line_comment)

# factory for parser returning tokens separated by no-newline whitespace
lexeme = partial(megaparsy_lexeme, p_space=sc)

# parser matching lexemes matching [a-zA-Z0-9\-]+
_token = parsy.regex(r'[a-zA-Z0-9\-]+')
p_item_factory = partial(lexeme, _token)
p_item = p_item_factory().desc('list')


# sub-lists
def _line_fold_callback(sc_):
    @parsy.generate
    def parser():
        items = yield p_item_factory(sc_).many()
        return ' '.join(items)


p_line_fold = line_fold(scn, _line_fold_callback)


@parsy.generate
def _complex_item_block():
    header = yield p_item
    return IndentMany(indent=None, f=lambda: header, p=p_line_fold)


# parser matching list item and its indented children
p_complex_item = indent_block(scn, _complex_item_block)


@parsy.generate
def _item_list_block():
    header = yield p_item
    return IndentSome(indent=None, f=lambda: header, p=p_complex_item)


# parser matching a collection of list items, begins non-indented, ends non-indented
# i.e. a whole list
p_item_list = non_indented(scn, indent_block(scn, _item_list_block))


# document is a collection of lists
parser = p_item_list << parsy.eof


if __name__ == "__main__":
    input_ = sys.argv[1]
    print(input_)
    val = parser.parse(input_)
    print(val)
