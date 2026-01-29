import pytest
import lexographer

from lexographer import Context, Type, Token
from examples.text import Tokenizer, Parser


def test_parser(data: callable):
    """Test the instantiation of the Parser class."""

    # Load some sample text data
    text: str = data("sample.txt")

    # Ensure that the sample text data loaded as expected
    assert isinstance(text, str)
    assert len(text) > 0

    # Create an instance of the Parser subclass
    parser = Parser(text=text)

    # Ensure that the Parser subclass instance has the expected types
    assert isinstance(parser, lexographer.Parser)
    assert isinstance(parser, Parser)

    # Ensure that the text specified during instantiation is as expected
    assert parser.text == text
