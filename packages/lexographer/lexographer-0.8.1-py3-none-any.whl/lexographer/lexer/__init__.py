from __future__ import annotations

from lexographer.logging import logger
from lexographer.exceptions import LexerError

import os

logger = logger.getChild(__name__)


class Lexer(object):
    """The Lexer class supports lexing over a provided string as well as convenience
    methods for lexing including look-ahead, look-behind and consume support."""

    _file: str = None
    _text: str = None
    _length: int = None
    _index: int = None
    _line: int = None
    _column: int = None
    _characters: str = None

    def __init__(self, text: str = None, file: str = None):
        """Supports initializing the Lexer class with the provided text string or file contents."""

        if text is None and file is None:
            raise LexerError(
                "The Lexer must be instantiated with either a text string or a valid file path!"
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
            raise LexerError("The 'file' argument must reference a valid file path!")
        elif not os.path.isfile(file):
            raise LexerError("The 'file' argument must reference a valid file!")

        if file:
            with open(file, "r") as handle:
                if isinstance(contents := handle.read(), str):
                    text = contents
                else:
                    raise LexerError(
                        f"Unable to read the contents of the specified file: {file}!"
                    )

        if (length := len(text.strip())) == 0:
            raise ValueError("The 'text' argument must have a non-empty string value!")

        self._text = text
        self._length: int = length
        self._file = file
        self._index: int = 0
        self._line: int = 0
        self._column: int = 0

    def __len__(self) -> int:
        """Return the source text string length."""

        return self._length

    def __iter__(self) -> Lexer:
        """Supports iterating over the source text string."""

        self._index = 0
        self._line = 0
        self._column = 0

        return self

    def __next__(self) -> str:
        """Supports iterating over the individual characters from the source text string."""

        return self.read(length=1)

    @property
    def file(self) -> str | None:
        """Returns the file path, if specified during class instantiation."""

        return self._file

    @property
    def text(self) -> str:
        """Returns the source text string."""

        return self._text

    @property
    def length(self) -> int:
        """Returns the source text string length."""

        return self._length

    @property
    def index(self) -> int:
        """Returns the zero-indexed character position, i.e. the indexing starts at 0."""

        return self._index  # remember self._index is incremented only after a read()

    @property
    def position(self) -> Position:
        """Returns the current character position as a Position instance."""

        return Position(index=self.index, line=self.line, column=self.column)

    @property
    def line(self) -> int:
        """Returns the one-indexed line number, i.e. the line numbers start at 1."""

        return self._line + 1

    @property
    def column(self) -> int:
        """Returns the one-indexed column number, i.e. the column numbers start at 1."""

        return self._column + 1

    @property
    def characters(self) -> str:
        """Returns the most recently lexed character string."""

        return self._characters

    def read(self, length: int = 1) -> str:
        """Reads the specified number of characters from the contents string."""

        if not (isinstance(length, int) and length >= 1):
            raise TypeError("The 'length' argument must have a positive integer value!")

        self._characters = characters = self._text[self._index : self._index + length]

        self._index += length
        self._column += length

        if characters == "\n":
            self._line += 1
            self._column = 0

        return characters

    def peek(self, length: int = 1) -> str:
        """Returns the specified number of characters ahead of the current position."""

        if not (isinstance(length, int) and length >= 1):
            raise TypeError("The 'length' argument must have a positive integer value!")

        return self._text[self._index : self._index + length]

    def previous(self, length: int = 1) -> str:
        """Returns the specified number of characters before the current position."""

        if not (isinstance(length, int) and length >= 1):
            raise TypeError("The 'length' argument must have a positive integer value!")

        return self._text[self._index : self._index - length]

    def consume(self, length: int | str = 1) -> None:
        """Consumes the specified number of characters, moving the position index."""

        if isinstance(length, str):
            length = len(length)
        elif not (isinstance(length, int) and length >= 1):
            raise TypeError("The 'length' argument must have a positive integer value!")

        self._index += length

    def push(self, length: int = 1) -> None:
        """Pushes the specified number of characters back, moving the position index."""

        if not (isinstance(length, int) and length >= 1):
            raise TypeError("The 'length' argument must have a positive integer value!")

        self._index -= length

    def lookbehind(self, contents: str, length: int = None) -> bool:
        """Checks if the contents proceeding the current position matches that provided."""

        if not isinstance(contents, str):
            raise TypeError("The 'contents' argument must have a string value!")

        if length is None:
            length = len(contents)
        elif not (isinstance(length, int) and length >= 1):
            raise TypeError("The 'length' argument must have a positive integer value!")

        previous: str = self.previous(length=length)

        matches: bool = previous == contents

        return matches

    def lookahead(
        self, contents: str, length: int = None, consume: bool = False
    ) -> bool:
        """Checks if the contents following the current position matches that provided."""

        if not isinstance(contents, str):
            raise TypeError("The 'contents' argument must have a string value!")

        if length is None:
            length = len(contents)
        elif not (isinstance(length, int) and length >= 1):
            raise TypeError("The 'length' argument must have a positive integer value!")

        if not isinstance(consume, bool):
            raise TypeError("The 'consume' argument must have a boolean value!")

        peeked: str = self.peek(length=length)

        matches: bool = peeked == contents

        # Consume only if the match was successful
        if matches is True and consume is True:
            self.consume(length=length)

        return matches


class Position(object):
    """The Position class encapsulates the current cursor position of the Lexer."""

    _index: int = None
    _line: int = None
    _column: int = None

    def __init__(self, index: int, line: int = 0, column: int = 0):
        """Initialize the new Position class instance with the specified values."""

        if not isinstance(index, int):
            raise TypeError("The 'index' argument must have an integer value!")
        elif not index >= 0:
            raise ValueError(
                "The 'index' argument must have an non-negative integer value!"
            )

        self._index = index

        if not isinstance(line, int):
            raise TypeError("The 'line' argument must have an integer value!")
        elif not line >= 1:
            raise ValueError(
                "The 'line' argument must have an non-negative integer value!"
            )

        self._line = line

        if not isinstance(column, int):
            raise TypeError("The 'column' argument must have an integer value!")
        elif not column >= 1:
            raise ValueError(
                "The 'column' argument must have an non-negative integer value!"
            )

        self._column = column

    def __str__(self) -> str:
        """Returns a string representation of current Position class instance."""

        return f"Position(index: {self._index}, line: {self._line}, column: {self._column})"

    @property
    def index(self) -> int:
        """Returns the current Position class instance's 'index' value."""

        return self._index

    @property
    def line(self) -> int:
        """Returns the current Position class instance's 'line' value."""

        return self._line

    @property
    def column(self) -> int:
        """Returns the current Position class instance's 'column' value."""

        return self._column

    def copy(self) -> Position:
        """Returns an exact copy of the current Position class instance."""

        return Position(index=self.index, line=self.line, column=self.column)

    def adjust(self, offset: int = 0, line: int = None, column: int = None) -> Position:
        """The 'adjust' method supports adjusting the current index position represented
        by the Position class instance, and allows for the line and column numbers to be
        adjusted as well as a change in the index position may also mean that the line
        number needs to change, and that the column number must change. If the line and
        column numbers are not easily computable when the adjustment is made, they should
        not be specified and will revert to having values of `0` which means that they
        are not known."""

        if not isinstance(offset, int):
            raise TypeError("The 'offset' argument must have an integer value!")

        # Adjust the index by the specified offset value
        self._index += offset

        if line is None:
            pass
        elif not isinstance(line, int):
            raise TypeError("The 'line' argument must have an integer value!")
        elif not line >= 1:
            raise ValueError("The 'line' argument must have a positive integer value!")
        else:
            self._line = line

        if column is None:
            # Adjust the column by the specified offset value
            self._column += offset
        elif not isinstance(column, int):
            raise TypeError("The 'column' argument must have an integer value!")
        elif not line >= 1:
            raise ValueError("The 'line' argument must have a positive integer value!")
        else:
            self._column = column

        return self
