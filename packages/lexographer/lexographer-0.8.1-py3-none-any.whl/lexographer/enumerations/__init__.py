from enumerific import Enumeration, auto


class Context(Enumeration):
    """List of Tokenizer contexts, noting the section of text currently being processed.
    The list of contexts may be added to as needed for a given lexing or tokenization
    use case by calling the Context.register(<name>, <value>) enumeration class method.
    """

    Unknown = auto()

    Start = auto()
    Finish = auto()


class Type(Enumeration, overwritable=True):
    """List of high-level token types commonly used in lexing; these enumeration options
    may be added to as needed for a given lexing or tokenization use case by calling the
    Type.register(<name>, <value>) enumeration class method. Option values can also be
    overwritten for exsiting options if needed by specifying an enumeration option name
    and a different value to be assigned to that enumeration option – option values must
    not clash with each other as each option must have a unique name and value."""

    Unknown = auto()

    Space = auto(example=" ")
    Tab = auto(example="\t")
    NewLine = auto(example="\n")
    CarriageReturn = auto(example="\r")
    Spacing = auto(example=" ")
    Dash = auto(example="-")
    EmDash = auto(example="–")
    Tilde = auto(example="~")
    Backtick = auto(example="`")
    Exclamation = auto(example="!")
    AtSign = auto(example="@")
    Hash = auto(example="#")
    Dollar = auto(example="$")
    Percent = auto(example="%")
    Carret = auto(example="^")
    Ampersand = auto(example="&")
    Asterisk = auto(example="*")
    LeftParenthesis = auto(example="(")
    RightParenthesis = auto(example=")")
    LeftBracket = auto(example="{")
    RightBracket = auto(example="}")
    LeftSquareBracket = auto(example="[")
    RightSquareBracket = auto(example="]")
    Underscore = auto(example="_")
    Colon = auto(example=":")
    SemiColon = auto(example=";")
    SingleQuote = auto(example="'")
    DoubleQuote = auto(example='"')
    Period = auto(example=".")
    Comma = auto(example=",")
    Bar = auto(example="|")
    Plus = auto(example="+")
    Minus = auto(example="-")
    Times = auto(example="*")
    Divide = auto(example="/")
    Slash = auto(example="/")
    BackSlash = auto(example="\\")
    Equals = auto(example="=")
    Question = auto(example="?")

    EqualsEquals = auto(example="==")
    NotEquals = auto(example="!=")
    GreaterThan = auto(example=">")
    LessThan = auto(example="<")
    GreaterThanEqual = auto(example=">=")
    LessThanEqual = auto(example="<=")
