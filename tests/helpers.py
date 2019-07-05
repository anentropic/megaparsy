import parsy


def prs_(p):
    """
    -- | Just like 'prs', but forces the parser to consume all input by adding
    -- 'eof':
    --
    -- > prs_ p = parse (p <* eof) ""
                                    ^ arg to `parse` func
                                    representing name of source file
    prs_
      :: Parser a
         -- ^ Parser to run
      -> String
         -- ^ Input for the parser
      -> Either (ParseErrorBundle String Void) a
         -- ^ Result of parsing
    """
    return (p << parsy.eof).parse
