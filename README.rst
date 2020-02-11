=========
megaparsy
=========

|Build Status| |PyPi Version|

|Python3.6| |Python3.7| |Python3.8|

.. |Build Status| image:: https://travis-ci.org/anentropic/megaparsy.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/anentropic/megaparsy
.. |PyPi Version| image:: https://badge.fury.io/py/megaparsy.svg
    :alt: Latest PyPI version
    :target: https://pypi.python.org/pypi/megaparsy/
.. |Python3.6| image:: https://img.shields.io/badge/Python%203.6--brightgreen.svg
    :alt: Python 3.6
.. |Python3.7| image:: https://img.shields.io/badge/Python%203.7--brightgreen.svg
    :alt: Python 3.7
.. |Python3.8| image:: https://img.shields.io/badge/Python%203.8--brightgreen.svg
    :alt: Python 3.8


Work In Progress - ignore for now ;)

Initial motivation for this project was to build an indentation-sensitive parser. This is problematic for any parser library which is limited to expressing context-free grammars (which is most of them), unless you use a separate pre-processing step (like e.g. the parser for the Python language does).

Googling around this topic I came upon `<https://markkarpov.com/tutorial/megaparsec.html#indentationsensitive-parsing>`_

So in Haskell-land we can find 'Monadic Parser Combinators', which do not have this restriciton to CFGs. And the `Megaparsec <https://hackage.haskell.org/package/megaparsec>`_ library defines many useful combinators, including some which designed specifically to help with building indentation-sensitive parsers.

But... it was difficult for me to learn to make a parser for the first time *and* learn Haskell simultaneously. So I looked around for a Python option and found the  brilliant `Parsy <https://parsy.readthedocs.io/en/latest/>`_ library. It provides an implementation of 'Monadic Parser Combinators' in Python.

Nicely and simply explained here:

.. figure:: http://img.youtube.com/vi/dDtZLm7HIJs/0.jpg
   :alt: Functional or Combinator Parsing explained by Professor Graham Hutton.
   :target: http://www.youtube.com/watch?v=dDtZLm7HIJs

   *Functional or Combinator Parsing explained by Professor Graham Hutton.*

So in *Megaparsy* I have ported a bunch of the Megaparsec combinators over to Parsy. It is surprising how smoothly it went and how similar they come out - this is testament to the genius of Parsy, which is where all the clever part is.

(I haven't done all of them yet, but the indentation-sensitive ones are here)

I've also roughly translated across the property-based tests from their Haskell QuickCheck originals into Python `Hypothesis <https://hypothesis.readthedocs.io/en/latest/>`_ ones.
