import operator
import re

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
    return re.search(r'[^\s]', str_).start()


sc = space(parsy.regex(r'( |\t)+').result(''))

scn = space(char.space1)


def test_indent_block():
    whitespace_char = ' '
    indent_level = 4

    def make_indent_(val, size):
        indent_str = whitespace_char * size
        return ''.join([indent_str, val, whitespace_char])

    def make_indent(val, size):
        return make_indent_(val, size) + '\n'

    lines = [
        make_indent(symbol_a, 0),
        make_indent(symbol_b, indent_level),
        make_indent(symbol_c, indent_level + 2),
        make_indent(symbol_b, indent_level),
        make_indent_(symbol_c, indent_level + 2)
    ]
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

r"""
mkIndent :: String -> Int -> Gen String
mkIndent x n = (++) <$> mkIndent' x n <*> eol
  where
    eol = frequency [(5, return "\n"), (1, (scaleDown . listOf1 . return) '\n')]

mkIndent' :: String -> Int -> Gen String
mkIndent' x n = concat <$> sequence [spc, sym, tra]
  where
    spc = frequency [(5, vectorOf n itm), (1, scaleDown (listOf itm))]
    tra = scaleDown (listOf itm)
    itm = elements " \t"
    sym = return x

scaleDown :: Gen a -> Gen a
scaleDown = scale (`div` 4)

scale :: (Int -> Int) -> Gen a -> Gen a Source#
-- "Adjust the size parameter, by transforming it with the given function."

getCol :: String -> Pos
getCol x = sourceColumn .
  strSourcePos defaultTabWidth (initialPos "") $ takeWhile isSpace x

describe "indentBlock" $ do
    it "works as indented" $
      property $ \mn'' -> do
        let mkBlock = do
              l0 <- mkIndent sbla 0
              l1 <- mkIndent sblb ib
              l2 <- mkIndent sblc (ib + 2)
              l3 <- mkIndent sblb ib
              l4 <- mkIndent' sblc (ib + 2)
              return (l0,l1,l2,l3,l4)
            ib  = fromMaybe 2 mn'
            mn' = getSmall . getPositive <$> mn''
            mn  = mkPos . fromIntegral <$> mn'

        forAll mkBlock $ \(l0,l1,l2,l3,l4) -> do
          let (col0, col1, col2, col3, col4) =
                (getCol l0, getCol l1, getCol l2, getCol l3, getCol l4)
              fragments = [l0,l1,l2,l3,l4]
              g x = sum (length <$> take x fragments)
              s = concat fragments
              p = lvla <* eof
              lvla = indentBlock scn $ IndentMany mn      (l sbla) lvlb <$ b sbla
              lvlb = indentBlock scn $ IndentSome Nothing (l sblb) lvlc <$ b sblb
              lvlc = indentBlock scn $ IndentNone                  sblc <$ b sblc
              b    = symbol sc
              l x  = return . (x,)
              ib'  = mkPos (fromIntegral ib)
          if | col1 <= col0 -> prs p s `shouldFailWith`
               err (getIndent l1 + g 1) (utok (head sblb) <> eeof)
             | isJust mn && col1 /= ib' -> prs p s `shouldFailWith`
               errFancy (getIndent l1 + g 1) (ii EQ ib' col1)
             | col2 <= col1 -> prs p s `shouldFailWith`
               errFancy (getIndent l2 + g 2) (ii GT col1 col2)
             | col3 == col2 -> prs p s `shouldFailWith`
               err (getIndent l3 + g 3) (utoks sblb <> etoks sblc <> eeof)
             | col3 <= col0 -> prs p s `shouldFailWith`
               err (getIndent l3 + g 3) (utok (head sblb) <> eeof)
             | col3 < col1 -> prs p s `shouldFailWith`
               errFancy (getIndent l3 + g 3) (ii EQ col1 col3)
             | col3 > col1 -> prs p s `shouldFailWith`
               errFancy (getIndent l3 + g 3) (ii EQ col2 col3)
             | col4 <= col3 -> prs p s `shouldFailWith`
               errFancy (getIndent l4 + g 4) (ii GT col3 col4)
             | otherwise -> prs p s `shouldParse`
               (sbla, [(sblb, [sblc]), (sblb, [sblc])])
    it "IndentMany works as intended (newline at the end)" $
      property $ forAll ((<>) <$> mkIndent sbla 0 <*> mkWhiteSpaceNl) $ \s -> do
        let p    = lvla
            lvla = indentBlock scn $ IndentMany Nothing (l sbla) lvlb <$ b sbla
            lvlb = b sblb
            b    = symbol sc
            l x  = return . (x,)
        prs  p s `shouldParse` (sbla, [])
        prs' p s `succeedsLeaving` ""
    it "IndentMany works as intended (eof)" $
      property $ forAll ((<>) <$> mkIndent sbla 0 <*> mkWhiteSpace) $ \s -> do
        let p    = lvla
            lvla = indentBlock scn $ IndentMany Nothing (l sbla) lvlb <$ b sbla
            lvlb = b sblb
            b    = symbol sc
            l x  = return . (x,)
        prs  p s `shouldParse` (sbla, [])
        prs' p s `succeedsLeaving` ""
    it "IndentMany works as intended (whitespace aligned precisely to the ref level)" $ do
      let p    = lvla
          lvla = indentBlock scn $ IndentMany Nothing (l sbla) lvlb <$ b sbla
          lvlb = b sblb
          b    = symbol sc
          l x  = return . (x,)
          s    = "aaa\n bbb\n "
      prs  p s `shouldParse` (sbla, [sblb])
      prs' p s `succeedsLeaving` ""
    it "works with many and both IndentMany and IndentNone" $
      property $ forAll ((<>) <$> mkIndent sbla 0 <*> mkWhiteSpaceNl) $ \s -> do
        let p1   = indentBlock scn $ IndentMany Nothing (l sbla) lvlb <$ b sbla
            p2   = indentBlock scn $ IndentNone sbla <$ b sbla
            lvlb = b sblb
            b    = symbol sc
            l x  = return . (x,)
        prs  (many p1) s `shouldParse` [(sbla, [])]
        prs  (many p2) s `shouldParse` [sbla]
        prs' (many p1) s `succeedsLeaving` ""
        prs' (many p2) s `succeedsLeaving` ""
    it "IndentSome expects the specified indentation level for first item" $ do
      let s   = "aaa\n  bbb\n"
          p   = indentBlock scn $
            IndentSome (Just (mkPos 5)) (l sbla) lvlb <$ symbol sc sbla
          lvlb = symbol sc sblb
          l x = return . (x,)
      prs p s `shouldFailWith` errFancy 6
        (fancy $ ErrorIndentation EQ (mkPos 5) (mkPos 3))
"""
