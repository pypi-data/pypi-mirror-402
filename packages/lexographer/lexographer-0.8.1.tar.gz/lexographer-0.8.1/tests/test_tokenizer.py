import pytest
import lexographer

from lexographer import Context, Type, Token
from examples.text import Tokenizer, Parser


def test_tokenizer(data: callable):
    """Test the instantiation of the Tokenizer class."""

    # Load some sample text data
    text: str = data("sample.txt")

    # Ensure that the sample text data loaded as expected
    assert isinstance(text, str)
    assert len(text) > 0

    # Create an instance of the custom Tokenizer subclass
    tokenizer = Tokenizer(text=text)

    # Ensure that the Tokenizer subclass instance has the expected types
    assert isinstance(tokenizer, lexographer.Tokenizer)
    assert isinstance(tokenizer, Tokenizer)

    # Ensure that the text specified during instantiation is as expected
    assert isinstance(tokenizer.text, str)
    assert tokenizer.text == text
    assert tokenizer.text == "The quick brown fox jumped over the lazy corgi."

    # Ensure that the sample text was tokenized into the expected number of tokens based
    # on the tokenization performed by the custom Tokenizer class imported above.
    assert tokenizer.length == 18

    # Ensure that the tokens extracted from the sample text are as expected
    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[0]
    assert token.type is Type.Word
    assert token.text == "The"
    assert token.position.line == 1
    assert token.position.index == 0
    assert token.length == 3

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[1]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 3
    assert token.position.column == 4
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[2]
    assert token.type is Type.Word
    assert token.text == "quick"
    assert token.position.line == 1
    assert token.position.index == 4
    assert token.position.column == 5
    assert token.length == 5

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[3]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 9
    assert token.position.column == 10
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[4]
    assert token.type is Type.Word
    assert token.text == "brown"
    assert token.position.line == 1
    assert token.position.index == 10
    assert token.position.column == 11
    assert token.length == 5

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[5]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 15
    assert token.position.column == 16
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[6]
    assert token.type is Type.Word
    assert token.text == "fox"
    assert token.position.line == 1
    assert token.position.index == 16
    assert token.position.column == 17
    assert token.length == 3

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[7]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 19
    assert token.position.column == 20
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[8]
    assert token.type is Type.Word
    assert token.text == "jumped"
    assert token.position.line == 1
    assert token.position.index == 20
    assert token.position.column == 21
    assert token.length == 6

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[9]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 26
    assert token.position.column == 27
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[10]
    assert token.type is Type.Word
    assert token.text == "over"
    assert token.position.line == 1
    assert token.position.index == 27
    assert token.position.column == 28
    assert token.length == 4

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[11]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 31
    assert token.position.column == 32
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[12]
    assert token.type is Type.Word
    assert token.text == "the"
    assert token.position.line == 1
    assert token.position.index == 32
    assert token.position.column == 33
    assert token.length == 3

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[13]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 35
    assert token.position.column == 36
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[14]
    assert token.type is Type.Word
    assert token.text == "lazy"
    assert token.position.line == 1
    assert token.position.index == 36
    assert token.position.column == 37
    assert token.length == 4

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[15]
    assert token.type is Type.Spacing
    assert token.text == " "
    assert token.position.line == 1
    assert token.position.index == 40
    assert token.position.column == 41
    assert token.length == 1

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[16]
    assert token.type is Type.Word
    assert token.text == "corgi"
    assert token.position.line == 1
    assert token.position.index == 41
    assert token.position.column == 42
    assert token.length == 5

    assert isinstance(token := tokenizer.next(), Token)
    assert token is tokenizer[17]
    assert token.type is Type.Period
    assert token.text == "."
    assert token.position.line == 1
    assert token.position.index == 46
    assert token.position.column == 47
    assert token.length == 1


def test_parser(data: callable):
    """Test the instantiation of the Tokenizer class."""

    # Load some sample text data
    text: str = data("sample.txt")

    # Ensure that the sample text data loaded as expected
    assert isinstance(text, str)
    assert len(text) > 0

    # Create an instance of the custom Parser subclass
    parser = Parser(text=text)

    # Ensure that the Parser subclass instance has the expected types
    assert isinstance(parser, lexographer.Parser)
    assert isinstance(parser, Parser)

    # Ensure that the text specified during instantiation is as expected
    assert isinstance(parser.text, str)
    assert parser.text == text
    assert parser.text == "The quick brown fox jumped over the lazy corgi."

    # The custom Parser subclass takes the source text, and passes it through the Lexer
    # and custom Tokenizer subclass, and then processes the tokens, reassembling the
    # source text string from the tokens. While doing so it replaces any spaces with "•"
    # characters and swaps "!" with "." and vice-versa; this is a trivial example of the
    # sort of processing that could be performed on the tokens to generate other types
    # of output, while in reality there is no upper limit to the level of sophistication
    # in the types of output that can be generated from the parsed tokens.
    parsed: str = parser.parse()

    # Ensure that the output from the Parser is as expected.
    assert isinstance(parsed, str)

    # As per the custom Parser subclass' implementation, we expect to see that all space
    # characters are replaced with "•" characters and "." and "!" characters are swapped:
    assert parsed == text.replace(" ", "•").replace(".", "!")
    assert parsed == "The•quick•brown•fox•jumped•over•the•lazy•corgi!"
