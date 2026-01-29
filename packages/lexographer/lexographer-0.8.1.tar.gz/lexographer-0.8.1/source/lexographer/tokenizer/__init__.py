from __future__ import annotations

from lexographer.logging import logger
from lexographer.enumerations import Context, Type
from lexographer.exceptions import TokenizerError
from lexographer.lexer import Lexer
from lexographer.tokenizer.token import Token
from lexographer.tokenizer.tokens import Tokens

from abc import abstractmethod

import os

logger = logger.getChild(__name__)


class Tokenizer(object):
    """The Tokenizer class supports converting the provided text string into raw tokens
    via a use-case specific subclass implementation which uses the base functionality
    provided by the Tokenizer class and adds the necessary customization for the type of
    structured text being tokenized, such as a document in a format such as XML, a query
    string in a language like SQL, or code written in a language such as Python."""

    _lexer: Lexer = None
    _tokens: list[Token] = None
    _context: Context = None
    _index: int = None
    _line: int = None
    _column: int = None
    _length: int = None
    _level: int = None

    def __init__(self, text: str = None, file: str = None):
        """Supports initializing the Tokenizer class with the provided text string or file contents."""

        if text is None and file is None:
            raise TokenizerError(
                "The Tokenizer must be instantiated with either a text string or a valid file path!"
            )

        if text is None:
            pass
        elif not isinstance(text, str):
            raise TypeError("The 'text' argument must have a string value!")

        if file is None:
            pass
        elif not isinstance(file, str):
            raise TypeError("The 'file' argument must have a string value!")
        elif not os.path.exists(file):
            raise TokenizerError(
                f"The 'file' argument, {file}, must reference a valid file path!"
            )
        elif not os.path.isfile(file):
            raise TokenizerError(
                f"The 'file' argument, {file}, must reference a valid file!"
            )

        self._lexer = Lexer(text=text, file=file)
        self._tokens: list[Token] = []
        self._context: Context = Context.Unknown
        self._index: int = 0
        self._line: int = 1
        self._column: int = 1
        self._length: int = 0
        self._level: int = 0

        self.parse()

    def __len__(self) -> int:
        logger.debug("%s.__len__()", self.__class__.__name__)

        return self._length

    def __iter__(self) -> Tokenizer:
        logger.debug("%s.__iter__()", self.__class__.__name__)

        self._index = 0

        return self

    def __next__(self, offset: int = 0) -> Token:
        logger.debug("%s.__next__() index => %d", self.__class__.__name__, self._index)

        if not isinstance(offset, int):
            raise TypeError("The 'offset' argument must have an integer value!")

        token: Token = None

        if 0 <= (self._index + offset) < self._length:
            token = self._tokens[(self._index + offset)]

            self._index += 1
        else:
            raise StopIteration

        return token

    def __getitem__(self, index: int) -> Token:
        if index < self._length:
            return self._tokens[index]
        else:
            raise KeyError(
                "The 'index' argument is out of range for this Tokenizer instance!"
            )

    @property
    def lexer(self) -> Lexer:
        return self._lexer

    @property
    def text(self) -> str:
        return self.lexer.text

    @property
    def file(self) -> str | None:
        return self.lexer.file

    @property
    def tokens(self) -> list[Token]:
        return self._tokens

    @property
    def context(self) -> Context:
        return self._context

    @context.setter
    def context(self, context: Context):
        if not isinstance(context, Context):
            raise TypeError(
                "The 'context' argument must reference a Context enumeration class option!"
            )

        self._context = context

    @property
    def index(self) -> int:
        return self._index

    @property
    def length(self) -> int:
        return self._length

    @property
    def level(self) -> int:
        return self._level

    @level.setter
    def level(self, level: int):
        if not (isinstance(level, int) and level >= 0):
            raise TypeError("The 'level' argument must have a positive integer value!")

        self._level = level

    @property
    def token(self):
        raise NotImplementedError

    @token.setter
    def token(self, token: Token):
        if not isinstance(token, Token):
            raise TypeError(
                "The 'token' argument must reference a Token class instance!"
            )

        self._tokens.append(token)

        self._length += 1

    def next(self, offset: int = 0) -> Token | None:
        if not isinstance(offset, int):
            raise TypeError("The 'offset' argument must have an integer value!")

        try:
            return self.__next__(offset=offset)
        except StopIteration:
            return None

    def seek(self, index: int = 0) -> Tokenizer:
        logger.debug("%s.seek(index: %d)", self.__class__.__name__, index)

        if not isinstance(index, int):
            raise TypeError("The 'index' argument must have an integer value!")
        elif index < 0:
            self._index = self._index + index
        elif index >= 0:
            self._index = index

        return self

    def peek(self, offset: int = 1) -> Token | None:
        logger.debug("%s.peek(offset: %d)", self.__class__.__name__, offset)

        if not (isinstance(offset, int) and offset >= 0):
            raise TypeError("The 'offset' argument must have a positive integer value!")

        token: Token = None

        if (self._index + offset) <= self._length:
            token = self._tokens[self._index + offset]

        return token

    def previous(self, offset: int = 0) -> Token | None:
        logger.debug("%s.previous(offset: %d)", self.__class__.__name__, offset)

        if not isinstance(offset, int):
            raise TypeError("The 'offset' argument must have an integer value!")

        if offset < 0:
            offset = 0 - offset

        token: Token = None

        if len(self._tokens) > 0:
            token = self._tokens[self._index - (1 + offset)]

        return token

    @abstractmethod
    def parse(self):
        """Parse over the individual characters of the provided contents string via the
        Lexer, generating a list of Tokens that represent each part of the successfully
        parsed text. Should raise a TokenizerError if unexpected input is encountered.
        """

        raise NotImplementedError(
            "The 'parse' method must be implemented in a subclass!"
        )
