import pytest
import lexographer

from lexographer import Context, Type, Token


def test_lexer_instantiation_with_text(data: callable):
    """Test the instantiation of the Lexer class."""

    # Load some sample text data
    text: str = data("sample.txt")

    # Ensure that the sample text data loaded as expected
    assert isinstance(text, str)
    assert len(text) > 0

    # Create an instance of the Lexer subclass
    lexer = lexographer.Lexer(text=text)

    # Ensure that the Lexer class instance has the expected type
    assert isinstance(lexer, lexographer.Lexer)

    # Ensure that the text specified during instantiation is as expected
    assert lexer.text == text

    # Ensure the length of the text specified during instantiation is as expected
    assert lexer.length == len(text)


def text_lexer_instantiation_with_file(path: callable, data: callable):
    """Test the instantiation of the Lexer class with a file path."""

    # Obtain the file path for the sample file
    file = path("sample.txt")

    # Ensure that the file path has the expected type
    assert isinstance(file, str)

    # Create an instance of the Lexer subclass
    lexer = lexographer.Lexer(file=file)

    # Ensure that the Lexer class instance has the expected type
    assert isinstance(lexer, lexographer.Lexer)

    # Ensure that the file specified during instantiation is as expected
    assert lexer.file == file

    # Load some sample text data
    text: str = data("sample.txt")

    # Ensure that the sample text data loaded as expected
    assert isinstance(text, str)
    assert len(text) > 0

    # Ensure that the text specified during instantiation is as expected
    assert lexer.text == text

    # Ensure the length of the text specified during instantiation is as expected
    assert lexer.length == len(text)
