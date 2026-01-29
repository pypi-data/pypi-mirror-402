import pytest
import lexographer

from lexographer import Context, Type, Token
from examples.text import Tokenizer, Parser


def test_token(data: callable):
    """Test the instantiation of the Token class."""

    # Load some sample text data
    text: str = data("sample.txt")

    # Ensure that the sample text data loaded as expected
    assert isinstance(text, str)
    assert len(text) > 0

    # Create an instance of the Tokenizer subclass
    tokenizer = Tokenizer(text=text)

    # Ensure that the Tokenizer subclass instance has the expected types
    assert isinstance(tokenizer, lexographer.Tokenizer)
    assert isinstance(tokenizer, Tokenizer)

    # Create an instance of the Token class
    token = lexographer.Token(tokenizer=tokenizer, type=Type.Unknown)

    # Ensure that the Token class instance has the expected type
    assert isinstance(token, lexographer.Token)

    # Ensure that the associated tokenizer specified during instantiation is as expected
    assert isinstance(token.tokenizer, lexographer.Tokenizer)
    assert token.tokenizer is tokenizer

    # Ensure that the associated type specified during instantiation is as expected
    assert isinstance(token.type, Type)
    assert token.type is Type.Unknown
