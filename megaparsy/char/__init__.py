import parsy


newline = parsy.string('\n')

crlf = parsy.string('\r\n')

eol = (newline | crlf).desc('end of line')

tab = parsy.string('\t')

space = parsy.whitespace.optional().result('')

space1 = parsy.whitespace.result('')
