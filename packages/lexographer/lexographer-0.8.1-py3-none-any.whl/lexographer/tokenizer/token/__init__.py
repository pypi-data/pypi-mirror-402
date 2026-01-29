from __future__ import annotations

from lexographer.logging import logger
from lexographer.enumerations import Context, Type
from lexographer.lexer import Lexer, Position

logger = logger.getChild(__name__)


class Token(object):
    """The Token class represents a lexed token from the provided contents string."""

    _tokenizer: Tokenizer = None
    _type: Type = None
    _position: Position = None
    _text: str = None
    _level: int = None

    def __init__(
        self,
        tokenizer: Tokenizer,
        type: Type,
        position: Position | int = None,
        text: str = None,
        level: int = None,
    ):
        """Supports initializing the Token class with the provided values."""

        from lexographer.tokenizer import Tokenizer

        if not isinstance(tokenizer, Tokenizer):
            raise TypeError(
                "The 'tokenizer' argument must reference a Tokenizer class instance!"
            )

        self._tokenizer = tokenizer

        if not isinstance(type, Type):
            raise TypeError(
                "The 'type' argument must reference a Type enumeration class option!"
            )

        self._type = type

        if text is None:
            self._text = self.lexer.characters
        elif isinstance(text, str):
            self._text = text
        else:
            raise TypeError(
                "The 'text' argument, if specified, must have a string value!"
            )

        if position is None:
            self._position = self.lexer.position.copy().adjust(offset=(0 - self.length))
        elif isinstance(position, Position):
            self._position = position
        elif isinstance(position, int):
            if position >= 1:
                self._position = Position(index=position)
            elif position < 0:
                self._position = self.lexer.position.adjust(position)
        else:
            raise TypeError(
                "The 'position' argument, if specified, must have a positive integer value!"
            )

        if level is None:
            self._level = self.tokenizer.level
        elif isinstance(level, int) and level >= 0:
            self._level = level
        else:
            raise TypeError(
                "The 'level' argument, if specified, must have a positive integer value!"
            )

    def __str__(self) -> str:
        """Returns a string representation of current Token instance for debugging."""

        return "<%s.%s(position: %s, text: %r)>" % (
            self.__class__.__name__,
            self.name,
            self.position,
            self.text,
        )

    def __repr__(self) -> str:
        """Returns a string representation of current Token instance for debugging."""

        return "<%s.%s(position: %s, text: %r)> @ %0xh" % (
            self.__class__.__name__,
            self.name,
            self.position,
            self.text,
            hex(id(self)),
        )

    @property
    def tokenizer(self) -> Tokenizer:
        """Returns the Token instance's associated Tokenizer class instance."""

        return self._tokenizer

    @property
    def lexer(self) -> Lexer:
        """Returns the Token instance's associated Lexer class instance."""

        return self._tokenizer.lexer

    @property
    def type(self) -> Type:
        """Returns the Token instance's type enumeration option."""

        return self._type

    @property
    def name(self) -> str:
        """Returns the Token instance's type name."""

        return self.type.name

    @property
    def position(self) -> Position:
        """Returns the Token instance's text position within the source text string."""

        return self._position

    @property
    def length(self) -> int:
        """Returns the Token instance's text length."""

        return len(self._text) if isinstance(self._text, str) else 0

    @property
    def text(self) -> str:
        """Returns the Token instance's text as specified during instantiation."""

        return self._text

    @property
    def level(self) -> int:
        """Returns the Token instance's level as specified during instantiation."""

        return self._level

    @property
    def printable(self) -> str:
        """Returns a printable version of the current Token class instance's text."""

        if self.text == "\n":
            return "␤"
        if self.text == "\r":
            return "␍"
        elif self.text == "\t":
            return "␉"
        elif self.text == " ":
            return "␠"
        else:
            return self.text

    def context(self) -> Context:
        """Returns the Token instance's context in overridden implementations."""

        raise NotImplementedError
