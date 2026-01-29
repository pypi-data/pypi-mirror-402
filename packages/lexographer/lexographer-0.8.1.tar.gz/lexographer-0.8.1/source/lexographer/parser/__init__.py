from __future__ import annotations

from lexographer.logging import logger
from lexographer.enumerations import Context, Type
from lexographer.tokenizer import Tokenizer, Tokens, Token
from lexographer.exceptions import ParserError

from abc import abstractmethod

import os

logger = logger.getChild(__name__)


class Parser(object):
    _tokenizer_subclass: Tokenizer = None
    _encoding: str = None
    _tokenizer: Tokenizer = None
    _context: Context = None

    @classmethod
    def register_tokenizer(cls, tokenizer: Tokenizer):
        """Supports registering the default Tokenizer for this Parser subclass to use."""

        if not isinstance(tokenizer, type):
            raise TypeError(
                "The 'tokenizer' argument must reference a Tokenizer subclass!"
            )
        elif not issubclass(tokenizer, Tokenizer):
            raise TypeError(
                "The 'tokenizer' argument must reference a Tokenizer subclass!"
            )
        cls._tokenizer_subclass = tokenizer

    def __init__(
        self,
        text: str = None,
        file: str = None,
        encoding: str = None,
        tokenizer: Tokenizer = None,
    ):
        """Supports initializing the Parser class with the provided values."""

        logger.debug(
            "%s.__init__(text: %d, file: %s, encoding: %s, tokenizer: %s)",
            self.__class__.__name__,
            len(text) if isinstance(text, str) else 0,
            file,
            encoding,
            tokenizer,
        )

        if text is None and file is None:
            raise ParserError(
                "The Parser must be instantiated with either a text string or a valid file path!"
            )

        if text is None:
            pass
        elif not isinstance(text, str):
            raise TypeError(
                "The 'text' argument, if specified, must have a string value!"
            )

        if file is None:
            pass
        elif not isinstance(file, str):
            raise TypeError(
                "The 'file' argument, if specified, must have a string value!"
            )
        elif not os.path.exists(file):
            raise ParserError(
                f"The 'file' argument, {file}, must reference a valid file path!"
            )
        elif not os.path.isfile(file):
            raise ParserError(
                f"The 'file' argument, {file}, must reference a valid file!"
            )

        if tokenizer is None:
            if not (
                isinstance(self.__class__._tokenizer_subclass, type)
                and issubclass(self.__class__._tokenizer_subclass, Tokenizer)
            ):
                raise TypeError(
                    "If no 'tokenizer' argument is specified during Parser initialisation, a Tokenizer subclass must be registered with the Parser beforehand via the Parser.register_tokenizer() class method!"
                )
            tokenizer = self.__class__._tokenizer_subclass
        elif not issubclass(tokenizer, Tokenizer):
            raise TypeError(
                "The 'tokenizer' argument must reference a Tokenizer subclass!"
            )

        self._tokenizer: Tokenizer = tokenizer(text=text, file=file)

        if encoding is None:
            pass
        elif isinstance(encoding, str):
            self._encoding: str = encoding
        else:
            raise TypeError(
                "The 'encoding' argument, if specified, must have a string value!"
            )

    @property
    def text(self) -> str:
        """Return the associated Tokenizer class instance's text property value."""

        return self._tokenizer.text

    @property
    def file(self) -> str | None:
        """Return the associated Tokenizer class instance's file property value."""

        return self._tokenizer.file

    @property
    def tokenizer(self) -> Tokenizer:
        """Return the associated Tokenizer class instance."""

        return self._tokenizer

    @property
    def encoding(self) -> str | None:
        """Return the Parser class instance's initialized string encoding value."""

        return self._encoding

    @property
    def context(self) -> Context | None:
        """Return the Parser class instance's current context enumeration value."""

        return self._context

    @context.setter
    def context(self, context: Context):
        """Supports setting the Parser class instance's current context enumeration value."""

        if not isinstance(context, Context):
            raise TypeError(
                "The 'context' argument must reference a Context enumeration class option!"
            )

        self._context = context

    @abstractmethod
    def parse(self):
        """Parse over the individual tokens of the provided source text string obtained
        via the Tokenizer and Lexer, to generating the desired output. The method should
        raise a ParserError if unexpected input is encountered."""

        raise NotImplementedError(
            "The 'parse' method must be implemented in a subclass!"
        )
