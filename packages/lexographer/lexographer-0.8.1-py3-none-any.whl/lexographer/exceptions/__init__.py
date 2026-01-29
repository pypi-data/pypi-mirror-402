class LexographerError(Exception):
    """LexographerError is the root exception type for library exception handling."""

    pass


class LexerError(LexographerError):
    """LexerError is the exception type for errors raised by the Lexer class."""

    pass


class TokenizerError(LexographerError):
    """TokenizerError is the exception type for errors raised by the Tokenizer class."""

    pass


class ParserError(LexographerError):
    """ParserError is the exception type for errors raised by the Parser class."""

    pass
