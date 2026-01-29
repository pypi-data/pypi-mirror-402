import pytest
import lexographer

from lexographer import Context, Type, Token


def test_tokens():
    """Test the instantiation of the Tokens class."""

    # Create an instance of the Tokens class
    tokens = lexographer.Tokens(context=Context.Unknown)

    # Ensure that the Tokens class instance has the expected type
    assert isinstance(tokens, lexographer.Tokens)

    # Ensure that the context specified during instantiation is as expected
    assert isinstance(tokens.context, Context)
    assert tokens.context is Context.Unknown
