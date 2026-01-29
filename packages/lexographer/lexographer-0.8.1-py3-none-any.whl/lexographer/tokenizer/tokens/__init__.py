from __future__ import annotations

from lexographer.logging import logger
from lexographer.enumerations import Context, Type
from lexographer.exceptions import TokenizerError
from lexographer.lexer import Lexer
from lexographer.tokenizer.token import Token

from collections.abc import Sequence

logger = logger.getChild(__name__)


class Tokens(Sequence):
    """The Tokens class provides a container to hold one or more Token instances."""

    _context: Context = None
    _name: str = None
    _note: str = None
    _tokens: list[Token] = None
    _length: int = None
    _index: int = None
    _parent: Tokens = None
    _children: list[Tokens] = None

    def __init__(self, context: Context, name: str = None, note: str = None):
        """Supports initializing the Tokens class with the provided values."""

        if not isinstance(context, Context):
            raise TypeError(
                "The 'context' argument must reference a Context enumeration option!"
            )

        self._context: Context = context

        if name is None:
            pass
        elif not isinstance(name, str):
            raise TypeError(
                "The 'name' argument, if specified, must have a string value!"
            )

        self._name: str = name

        if note is None:
            pass
        elif not isinstance(note, str):
            raise TypeError(
                "The 'note' argument, if specified, must have a string value!"
            )

        self._note: str = note

        self._tokens: list[Token] = []

        self._length: int = 0

        self._index: int = 0

        self._parent: Tokens = None

        self._children: list[Tokens] = []

    def __len__(self) -> int:
        """Returns the current length of the Tokens sequence."""

        return self._length

    def __iter__(self) -> Tokens:
        """Returns an iterator for the Tokens sequence."""

        self._index = 0

        return self

    def __next__(self) -> Token:
        """Returns the next available Token from the Tokens sequence."""

        if self._index + 1 <= self._length:
            token: Token = self._tokens[self._index]
            self._index += 1
            return token
        else:
            raise StopIteration

    def __getitem__(self, index: int) -> Token:
        """Returns the specified Token, via its index, from the Tokens sequence."""

        if not isinstance(index, int):
            raise TypeError("The 'index' argument must have an integer value!")

        if index < self._length:
            return self._tokens[index]
        else:
            raise KeyError(
                "The index, {index}, is out of range for this Tokens sequence!"
            )

    def clear(self) -> None:
        """Supports clearning and resetting the current Tokens sequence."""

        self._tokens.clear()
        self._length = 0
        self._index = 0
        self._children.clear()

    def add(self, token: Token) -> None:
        """Supports adding a Token to the Tokens sequence."""

        if not isinstance(token, Token):
            raise TypeError(
                "The 'token' argument must reference a Token class instance!"
            )

        self._tokens.append(token)
        self._length += 1

    @property
    def context(self) -> Context:
        """Returns the Tokens sequence context as set during instantiation."""

        return self._context

    @property
    def name(self) -> str | None:
        """Returns the Tokens sequence name as set during instantiation."""

        return self._name

    @property
    def note(self) -> str | None:
        """Returns the Tokens sequence note, if any, as set during instantiation."""

        return self._note

    @property
    def level(self) -> int:
        """Returns the derived level of the Token instances held by the Tokens sequence."""

        levels: set[int] = set()

        for token in self._tokens:
            levels.add(token.level)

        if len(levels) > 1:
            return levels.pop()
        else:
            raise TokenizerError(
                "One or more tokens added to the Tokens mapping are from different nesting levels!"
            )

    @property
    def token(self) -> None:
        """Supports adding a single Token to the Tokens sequence via the property setter
        while the property getter is intentionally unimplemented."""

        raise NotImplementedError

    @token.setter
    def token(self, token: Token):
        """Supports adding a single Token to the Tokens sequence via the property setter
        while the property getter is intentionally unimplemented."""

        if not isinstance(token, Token):
            raise TypeError(
                "The 'token' argument must reference a Token class instance!"
            )

        self._tokens.append(token)
        self._length += 1

    @property
    def root(self) -> Tokens:
        """Returns the root of the Tokens tree, callable from any other Tokens node."""

        if self.parent is None:
            return self

        return self.parent.root

    @property
    def parent(self) -> Tokens | None:
        """Returns the parent of the current Tokens node."""

        return self._parent

    @parent.setter
    def parent(self, parent: Tokens) -> None:
        if not isinstance(parent, Tokens):
            raise TypeError(
                "The 'parent' argument must reference a Tokens class instance!"
            )

        self._parent = parent

    @property
    def children(self) -> list[Tokens]:
        return self._children

    @property
    def child(self) -> None:
        raise NotImplementedError

    @child.setter
    def child(self, tokens: Tokens) -> None:
        if not isinstance(tokens, Tokens):
            raise TypeError(
                "The 'tokens' argument must reference a Tokens class instance!"
            )

        tokens.parent = self

        self._children.append(tokens)
