from itertools import takewhile

from hypothesis import given, strategies as st
import parsy
import pytest

from megaparsy.control.applicative.combinators import between

from tests.helpers import prs_


def test_between_basic():
    p = between(parsy.string('('), parsy.string(')'), parsy.regex(r'[^)]*'))
    result = p.parse("(whatever)")
    assert result == 'whatever'


@given(
    pre=st.text(),
    c=st.characters(),
    n=st.integers(min_value=0, max_value=10),
    post=st.text(),
)
def test_between(pre, c, n, post):
    r"""
      describe "between" $
        it "works" . property $ \pre c n' post -> do
          let p = between (string pre) (string post) (many (char c))
              n = getNonNegative n'
              b = length (takeWhile (== c) post)
              z = replicate n c
              s = pre ++ z ++ post
          if b > 0
            then prs_ p s `shouldFailWith` err (length pre + n + b)
              ( etoks post <> etok c <>
                if length post == b
                  then ueof
                  else utoks (drop b post) )
            else prs_ p s `shouldParse` z
      --                ^> args to `parse` method

      -- etoks utoks see Text.Megaparsec.Error.Builder
    """
    p = between(parsy.string(pre), parsy.string(post), parsy.string(c).many())
    b = len(list(takewhile(lambda c_: c_ == c, post)))
    token = c * n
    val = f"{pre}{token}{post}"
    if b > 0:
        with pytest.raises(parsy.ParseError):
            prs_(p)(val)
    else:
        result = prs_(p)(val)
        assert result == [c_ for c_ in token]
