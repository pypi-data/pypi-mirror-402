# Lexographer: A Pure Python Lexer, Tokenizer & Parser Base Library

The Lexographer library provides pure Python lexer, tokenizer and parser base classes
for building custom lexers, tokenizers and parsers.

### Requirements

The Lexographer library has been tested with Python 3.10, 3.11, 3.12 and 3.13. The
library is not compatible with Python 3.9 or earlier.

### Installation

The Lexographer library is available from PyPI, so may be added to a project's
dependencies via its `requirements.txt` file or similar by referencing the GraphQuery
library's name, `lexographer`, or the library may be installed directly into your local
runtime environment using `pip` via the `pip install` command by entering the following
into your shell:

	$ pip install lexographer

### Methods & Properties

The Lexographer library provides classes and base classes which can be used and extended
to build custom lexers, tokenizers and parsers for structured text such as query strings
or programming language code, as well as natural language text.

The classes and their methods and properties are listed below:

#### Lexer Class

The `Lexer` class supports lexing the provided text, and provides standard methods for
moving through structured text as are commonly needed in lexing operations, such as methods
to read, peek and consume the one or more characters from the current cursor position, as
well as to look-ahead and look-behind from the current cursor position for matching text.

These operations can be built upon within custom `Tokenizer` and `Parser` subclasses to 
develop tokenizers and parsers for structured text and natural language text inputs.

The `Lexer` class constructor `Lexer(...)` takes the following arguments:

 * `text` (`str`) – The optional `text` argument sets the text to lex.

 * `file` (`str`) – The optional `file` argument sets the file path of the file to lex.
 
Either one of the `text` or the `file` argument must be specified when instantiating an
instance of the `Lexer` class with valid values. If neither argument is specified, or is
invalid, an exception will be raised.

The `Lexer` class provides the following methods:

 * `read(length: int = 1)` (`str`) – The `read()` method supports reading the specified
 length of the input from the current cursor (index) position. By default the method
 will read and return a single character from the current cursor position or a custom
 length as specified by the optional `length` (`int`) parameter.
 
 If the specified value for the `length` parameter exceeds the number of available characters
 remaining before the end of the specified text string or the end of the file, only the
 remaining characters will be returned.
 
 The `read()` method advances the cursor position after completing the read, so that on
 the next read, the new cursor position is used.

 * `peek(length: int = 1)` (`str`) – The `peek()` method supports reading the specified
 length of the input from the current cursor (index) position. By default the method
 will read and return a single character from the current cursor position or a custom
 length as specified by the optional `length` (`int`) parameter.
 
 If the specified value for the `length` parameter exceeds the number of available characters
 remaining after the current cursor position, a `LexerError` exception will be raised.
 
 The `peek()` method does not advance the cursor position after completing the read, so
 on the next read, the same, unmodified cursor position is used. This allows for one or
 more characters from the current cursor position to be read and checked without affecting
 the cursor.

 * `previous(length: int = 1)` (`str`) – The `previous()` method supports reading the
 specified length of the input from the current cursor (index) position. By default the
 method will read and return a single character prior to the current cursor position or
 a custom length as specified by the optional `length` (`int`) parameter.
 
 If the specified value for the `length` parameter exceeds the number of available characters
 remaining before the current cursor position, a `LexerError` exception will be raised.
 
 The `previous()` method does not advance the cursor position after completing the read, so
 on the next read, the same, unmodified cursor position is used. This allows for one or
 more characters prior to the current cursor position to be read and checked without
 affecting the cursor.

* `consume(length: int = 1)` (`None`) – The `consume()` method supports moving the current
 cursor position forwards according to the specified length. By default the method will
 move the current cursor position a single character forwards from the current cursor
 position or the custom length as specified by the optional `length` (`int`) parameter,
 adjusting the current cursor position by the relevant number of characters.
 
 The method does not return a value; it simply moves the current cursor position.
 
 If the specified value for the `length` parameter exceeds the number of available characters
 remaining before the current cursor position, a `LexerError` exception will be raised.

* `push(length: int = 1)` (`None`) – The `push()` method supports moving the current
 cursor position backwards according to the specified length. By default the method will
 move the current cursor position a single character backwards from the current cursor
 position or the custom length as specified by the optional `length` (`int`) parameter,
 adjusting the current cursor position by the relevant number of characters.
 
 The method does not return a value; it simply moves the current cursor position.
 
 If the specified value for the `length` parameter exceeds the number of available characters
 remaining before the current cursor position, a `LexerError` exception will be raised.

 * `lookbehind(text: str, length: int = 1)` (`bool`) – The `lookbehind()` method
 supports checking if the specified text can be matched exactly with the text of the
 specified length prior to the current cursor position. If the specified `text` value
 exactly matches the text prior to the current cursor position of the specified length,
 the method returns `True`, otherwise the method returns `False`. By default the method
 will compare the provided `text` string with a single character of text prior to the
 current cursor position, or the custom length as specified by the optional `length`
 (`int`) parameter.

 * `lookahead(text: str, length: int = 1)` (`bool`) – The `lookahead()` method
 supports checking if the specified text can be matched exactly with the text of the
 specified length from the current cursor position. If the specified `text` value
 exactly matches the text from the current cursor position of the specified length,
 the method returns `True`, otherwise the method returns `False`. By default the method
 will compare the provided `text` string with a single character of text from the
 current cursor position, or the custom length as specified by the optional `length`
 (`int`) parameter.

The `Lexer` class provides the following properties:

 * `text` (`str`) – The `text` property provides access to the text string that the `Lexer`
 class was instantiated with, either via the initializer's `text` argument or by reading
 the file specified via the initializer's `file` argument.

 * `file` (`str | None`) – The `file` property provides access to the file path that the
 `Lexer` class was instantiated with, via the initializer's `file` argument, if one was
 specified during class initialization.

 * `length` (`int`) – The `length` property provides access to the length of the text
 string that the `Lexer` class was instantiated with, either via the initializer's `text`
 argument or by reading the file specified via the initializer's `file` argument.

 * `index` (`int`) – The `index` property provides access to the current cursor index
 position of the text string that the `Lexer` is processing. During class initialization
 the index is set to its default value of `0` and will advance from there, or be moved
 backwards as necessary, according to the method calls made to the `Lexer`. The value will
 never be less than `0` nor more than the length of the text string being processed less
 one as the `index` is a zero-indexed position, rather than a one-indexed position. This
 same value is also available via the `Position` instance's `index` property.

 * `position` (`Position`) – The `position` property provides access to the current cursor
 position via an instance of the `Position` class, which provides access to the cursor's
 current zero-indexed position, as well as the relevant line and column numbers. See the
 information below regarding the `Position` class and its properties.

 * `line` (`int`) – The `line` property provides access to the line number corresponding
 with the cursor's current position in the text string being processed. This same value
 is also available via the `Position` instance's `line` property.

 * `column` (`int`) – The `column` property provides access to the column number corresponding
 with the cursor's current position in the text string being processed. This same value
 is also available via the `Position` instance's `column` property.

 * `characters` (`str`) – The `characters` property provides access to the most recently
 read character or characters, read via the `read()` method. The length of the returned
 string will be dependent on if the `read()` method was called with a custom `length`
 value or not. The value returned by the `characters` property is only affected by calls
 to the `read()` method, not to any other `Lexer` class method such as `peek()`.

#### Position Class

The `Position` class supports reporting the `Lexer` class' current cursor position within
the text being lexed, including the current character index position, and the corresponding
line and column numbers.

The `Position` class offers the following methods:

 * `copy()` (`Position`) – The `copy()` method creates an exact copy of the current
 `Position` class instance and returns it.

 * `adjust(offset: int, line: int = None, column: int = None)` (`Position`) – The `adjust()`
 method supports modifying the the attributes of the current `Position` class instance,
 such as changing the current `index` relative to the specified `offset` – if the `offset`
 has a positive value, it will be added to the current `index` value, and if it has a
 negative value it will be subtracted from the current `index` value; the `line` and `column`
 values can be set to the new values if specified; if the `line` and `column` values are not
 specified these values will default to `0` indicating that no `line` or `column` value is
 available as both the `line` and `column` numbering starts at `1`.

The `Position` class offers the following properties:

 * `index` (`int`) – The `index` property provides access to the current cursor index
 position of the text string that the `Lexer` is processing. During class initialization
 the index is set to its default value of `0` and will advance from there, or be moved
 backwards as necessary, according to the method calls made to the `Lexer`. The value will
 never be less than `0` nor more than the length of the text string being processed less
 one as the `index` is a zero-indexed position, rather than a one-indexed position.

 * `line` (`int`) – The `line` property provides access to the line number corresponding
 with the cursor's current position in the text string being processed.

 * `column` (`int`) – The `column` property provides access to the column number corresponding
 with the cursor's current position in the text string being processed.

Instances of the `Position` class should not need to be created manually, rather instances are
returned whenever the `Lexer` class' `position` property is accessed.

#### Tokenizer Class

The `Tokenizer` class provides support for translating the provided text into a series
of `Token` class instances which represent all or part of the lexed text.

The `Tokenizer` class offers the following methods:

 * `__len__()` (`int`) – The `__len__()` method provides access to the current length of the
 `Tokenizer` class' internal list of tokenized tokens.

 * `__iter__()` (`Tokenizer`) – The `__iter__()` method provides support for iterating over
 the `Tokenizer` class' internal list of tokenized tokens using standard Python iterator
 patterns.

 * `__next__()` (`Tokenizer`) – The `__next__()` method provides support for iterating over
 the `Tokenizer` class' internal list of tokenized tokens using standard Python iterator
 patterns.

 * `next()` (`Token` | `None`) – The `next()` method provides support for obtaining the next `Token` from
 the `Tokenizer` class' internal list of tokenized tokens.

 * `next(offset: int = 0)` (`Token` | `None`) – The `next()` method provides support for
 obtaining the next `Token` from the `Tokenizer` class' internal list of tokenized tokens
 either at the current cursor position, or from the current cursor position plus the offset
 specified via the optional `offset` argument. The `next()` method will also advance the
 current cursor position within the `Tokenizer` class' internal list of tokenized tokens.
 If the specified offset is out of the bounds of the list, the method will return `None`.

 * `seek(index: int = 0)` (`Token` | `None`) – The `seek()` method provides support for
 seeking to the specified index within the `Tokenizer` class' internal list of tokenized
 tokens. The `seek()` method will seek back to the beginning of the list by default,
 unless a different index position is specified. The specified `index` position must be
 between `0` and the current length of the token list less one as the value is zero-indexed.

 * `peek(offset: int = 0)` (`Token` | `None`) – The `peek()` method provides support for
 obtaining the next `Token` from the `Tokenizer` class' internal list of tokenized tokens
 either at the current cursor position, or from the current cursor position plus the offset
 specified via the optional `offset` argument. The `peek()` method will not advance the
 current cursor position within the `Tokenizer` class' internal list of tokenized tokens,
 so allows a token to be checked without affecting the current list position. If the
 specified offset is out of the bounds of the list, the method will return `None`.

 * `previous(offset: int = 0)` (`Token` | `None`) – The `previous()` method provides
 support for obtaining the previous `Token` from the `Tokenizer` class' internal list of
 tokenized tokens prior to the current cursor position, or from the current cursor position
 plus the offset specified via the optional `offset` argument. The `previous()` method will
 modify the current cursor position within the `Tokenizer` class' internal list of tokenized
 tokens to the position of the token being retrieved. If the specified offset is out of the
 bounds of the list, the method will return `None`.

 * `parse()` (`None`) – The `parse()` abstract method must be implemented in custom subclass
 implementations of the `Tokenizer` base class in order to tokenize the provided source text
 into one or more `Token` class instances. See the documentation and the test suite for examples
 of how to implement a custom `Tokenizer` subclass and to override the `parse()` method.

The `Tokenizer` class offers the following properties:

 * `lexer` (`Lexer`) – The `lexer` property provides access to the current `Lexer` class
 instance associated with and being used by the `Tokenizer` class instance.

 * `text` (`str`) – The `text` property provides access to the current text being tokenized
 by the `Tokenizer` instance where the text is either text that was directly supplied to
 the `Tokenizer` class instance or sourced from the file that was specified during instantiation.

 * `file` (`str`) – The `file` property provides access to the current file being tokenized
 by the `Tokenizer` instance, if one was specified during instantiation.

 * `tokens` (`list[Token]`) – The `tokens` property provides access to the list of `Token`
 class instances which have been tokenized by the the `Tokenizer` instance from the provided
 source text.

 * `context` (`Context`) – The `context` property provides access to the current tokenizer
 context, a custom property that can be used to keep track of where within source text that
 the `Tokenizer` currently is working. The property returns the `Context` enumeration value
 that was assigned within the custom `Tokenizer` subclass' `parse()` method, and can be one
 of the default `Context` enumeration values provided by the library by default, or a custom
 `Context` enumeration value that has been added to the `Context` enumeration class. See the
 `Context` enumeration documentation below for more details.

 * `index` (`int`) – The `index` property provides access to the current position within
 the list of tokens that have been tokenized from the provided text or file; this property
 keeps track for the current position for the `Tokenizer` class' iterator support.

 * `length` (`int`) – The `length` property provides access to the current length of the
 list of tokens that have been tokenized from the provided text or file; this property
 keeps track for the current position for the `Tokenizer` class' iterator support.

 * `level` (`int`) – The `level` property provides access to the current level of depth
 within the source text that the `Tokenizer` is processing; this property can be used in
 the custom `parse()` method implementation within the custom `Tokenizer` subclass to
 keep track of tokenizing within multi-level structured text such as indentation levels
 within code or queries for example. The `level` property value is not directly managed
 by the `Tokenizer` base class implementation, and if not used will just return `0`.

 * `character` (`str`) – The `character` property provides access to the current character
 within the source text that the `Tokenizer` is processing.

 * `token` (`Token`) – The `token` property provides access to the append the most recently
 tokenized `Token` instance to the list of tokens that have been tokenized by the `Tokenizer`
 class instance. The `token` property does not provide a getter implementation, only a setter
 implementation, and is provided as a convenience to append tokens to the internal list of
 tokens and to update the token length counter.

#### Token Class

The `Token` class provides support for representing an tokenized piece of lexed text,
including attributes such as the position that the piece of lexed text originated in the
source text, and other assigned attributes such as its type or purpose within the source
text, such as if it represents punctuation or a word for example.

The `Token` class offers the following methods:

 * `__str__` (`str`) – The `__str__()` method returns a string representation of the token
 for logging or debugging purposes.
 
 * `__repr__` (`str`) – The `__repr__()` method returns a string representation of the token
 for debugging purposes with more detail than the string representation provided by `__str__()`.

The `Token` class offers the following properties:

 * `tokenizer` (`Tokenizer`) – The `tokenizer` property provides access to the current
 `Tokenizer` class instance that is associated with the `Token` class instance.
 
 * `lexer` (`Lexer`) – The `lexer` property provides access to the current `Lexer` class
 instance that is associated with the `Token` class instance.

 * `type` (`Type`) – The `type` property provides access to the `Token` class' assigned
 `type` value, which is a `Type` enumeration value which specifies what type of token is
 represented by the `Token` class instance, such as a punctuation character or a word or
 a number for example. The `type` value will be one of the values provided by the `Type`
 enumeration class by default or a custom enumeration option value added to the `Type`
 class during customization.

 * `name` (`str`) – The `name` property provides access to the name of the type of the `Token`
 as assigned to the `Token` class' `type` property.

 * `position` (`Position`) – The `position` property provides access to the `Token` class'
 position within the source text.
 
 * `length` (`int`) – The `length` property provides access to the length of the `Token`
 class' text value, which is the substring from source text represented by this token of
 one or more characters.

 * `text` (`str`) – The `text` property provides access to the `Token` class' text value,
 which is the substring from source text represented by this token of one or more characters.
 
 * `level` (`int`) – The `level` property provides access to the `Token` class' level value,
 which, if assigned during tokenization, will be the relevant level within the source text
 that the token was obtained from. This property is not managed by the library itself, but
 can be set in custom tokenization code to set the relevant level from the source text that
 a token exists at, this is particularly useful when tokenizing multi-level structured text
 such as code where there may be different levels of indentation.

 * `printable` (`str`) – The `printable` property provides access to a printable version
 of the `Token` class' text value, where a subset of special characters such as tabs, spaces,
 new lines and carriage returns are translated to a printable character for debugging purposes
 and all remaining characters are returned as-is.

#### Tokens Class

The `Tokens` class provides support for creating collections of one or more `Token` class
instances, which can be moved through like lists using standard Python iterator functionality.

The `Tokens` class offers the following methods:

 * `clear()` (`None`) – The `clear()` method provides support for clearing the current list
 of `Token` class instances from the internal list maintained by the `Tokens` class.

 * `add(token: Token)` (`None`) – The `add()` method provides support for adding a `Token`
 to the internal list of `Token` class instances maintained by the `Tokens` class.

 * `__len__()` (`int`) – The `__len__()` method provides access to the current length of
 the internal list of `Token` class instances maintained by the `Tokens` class instance.

 * `__iter__()` (`Tokenizer`) – The `__iter__()` method provides support for iterating
 over the `Tokens` class' internal list of `Token` class instances using standard Python
 iteration patterns.

 * `__next__()` (`Tokenizer`) – The `__next__()` method provides support for iterating
 over the `Tokens` class' internal list of `Token` class instances using standard Python
 iteration patterns.

The `Tokens` class offers the following properties:

 * `context` (`Context`) – The `context` property provides access to the context value
 that was assigned to the `Tokens` class instance at the time of instantiation.

 * `name` (`str`) – The `name` property provides access to the name value that was
 assigned to the `Tokens` class instance at the time of instantiation.

 * `note` (`str`) – The `note` property provides access to the name value that was
 assigned to the `Tokens` class instance at the time of instantiation.

 * `level` (`int`) – The `level` property provides access to the level value obtained
 from the tokens held by the `Tokens` class instance. It is expected that all of the
 `Token` class instances held by a `Tokens` class instance will all have originated from
 the same level within the source text and as such will all have been assigned the same
 level value, or that their level value was not set and defaulted to `0`. If one or more
 of the `Token` class instances held by a `Tokens` class instance are found to have originated
 from more than one level from the source text an `TokenizerError` exception will be raised.

 * `token` (`Token`) – The `token` property is provided as a convenience for adding a `Token`
 class instance to the internal list of `Token` class instances held by the `Tokens` class
 instance. The `token` property only defines the setter method to support this convenience,
 and does not provide a getter method implementation.

#### Parser Class

The `Parser` class provides support for creating custom `Parser` subclasses that can be
used to parse through the tokenized text and to generate custom output.

The `Parser` class offers the following methods:

 * `parse()` (`None`) – The `parse()` abstract method must be implemented in custom subclass
 implementations of the `Parser` base class in order to parse the provided tokens into the
 desired output. See the documentation and the test suite for examples of how to implement
 a custom `Parser` subclass and to override the `parse()` method.

The `Parser` class offers the following properties:

 * `text` (`str`) – The `text` property provides access to the text that has been tokenized
 by the custom `Tokenizer` subclass into the tokens being used by the parser.

 * `encoding` (`str` | `None`) – The `encoding` property provides access to the specified
 encoding of the source text, if any, that was set at the time of instantiation.

 * `tokenizer` (`Tokenizer`) – The `tokenizer` property provides access to the current
 `Tokenizer` class instance associated with the current `Parser` class instance.
 
 * `context` (`Context` | `None`) – The `context` property provides access to the specified
 context of the `Parser`, if any, returned as a `Context` enumeration class value. This
 value is not maintained by the library, but rather can be used in custom subclass
 implementations of the `Parser` class to keep track of context state.

### Example Usage

See the test suite for example usage, including examples of custom `Tokenizer` and `Parser`
subclasses used to parse raw structured text into tokens and downstream outputs.

### Unit Tests

The Lexographer library includes a suite of comprehensive unit tests which ensure that
the library functionality operates as expected. The unit tests were developed with and
are run via `pytest`.

To ensure that the unit tests are run within a predictable runtime environment where all
of the necessary dependencies are available, a [Docker](https://www.docker.com) image is
created within which the tests are run. To run the unit tests, ensure Docker and Docker
Compose is [installed](https://docs.docker.com/engine/install/), and perform the following
commands, which will build the Docker image via `docker compose build` and then run the
tests via `docker compose run` – the output of running the tests will be displayed:

```shell
$ docker compose build
$ docker compose run tests
```

To run the unit tests with optional command line arguments being passed to `pytest`, append
the relevant arguments to the `docker compose run tests` command, as follows, for example
passing `-vv` to enable verbose output:

```shell
$ docker compose run tests -vv
```

See the documentation for [PyTest](https://docs.pytest.org/en/latest/) regarding available
optional command line arguments.

### Copyright & License Information

Copyright © 2026 Daniel Sissman; licensed under the MIT License.
