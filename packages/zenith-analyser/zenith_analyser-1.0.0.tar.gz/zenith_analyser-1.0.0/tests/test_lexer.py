# Copyright 2026 François TUMUSAVYEYESU.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tests for the Lexer class.
"""

import pytest

from src.zenith_analyser import Lexer, ZenithLexerError


def test_lexer_initialization(sample_code):
    """Test lexer initialization."""
    lexer = Lexer(sample_code)
    assert lexer.input == sample_code
    assert lexer.pos == 0
    assert lexer.line == 1
    assert lexer.col == 1
    assert lexer.tokens == []


def test_tokenise_basic(sample_code):
    """Test basic tokenization."""
    lexer = Lexer(sample_code)
    tokens = lexer.tokenise()

    assert len(tokens) > 0
    assert tokens[-1]["type"] == "EOF"

    # Check for specific tokens
    token_types = [t["type"] for t in tokens]
    assert "target" in token_types
    assert "law" in token_types
    assert "identifier" in token_types
    assert "colon" in token_types


def test_tokenise_invalid_char():
    """Test tokenization with invalid character."""
    code = "target test: @ invalid"
    lexer = Lexer(code)

    with pytest.raises(ZenithLexerError) as exc_info:
        lexer.tokenise()

    assert "Unexpected character" in str(exc_info.value)


def test_tokenise_empty():
    """Test tokenization of empty input."""
    lexer = Lexer("")
    tokens = lexer.tokenise()

    assert len(tokens) == 1  # Only EOF token
    assert tokens[0]["type"] == "EOF"


def test_tokenise_whitespace():
    """Test tokenization with only whitespace."""
    code = "   \n\t  "
    lexer = Lexer(code)
    tokens = lexer.tokenise()

    # Should have newline tokens and EOF
    assert len(tokens) > 0
    assert tokens[-1]["type"] == "EOF"


def test_token_types():
    """Test all token types."""
    code = """
target test:
    key:"value"
    dictionnary:
        d1:"val1"
        d2:"val2"
    law example:
        start_date:2024-01-01 at 10:00
        period:1.30
        Event:
            A:"Test"
        GROUP:(A 45^15)
    end_law
end_target
"""

    lexer = Lexer(code)
    tokens = lexer.tokenise()

    expected_types = [
        "target",
        "identifier",
        "colon",
        "newline",
        "key",
        "colon",
        "string",
        "newline",
        "law",
        "identifier",
        "colon",
        "newline",
        "start_date",
        "colon",
        "date",
        "at",
        "time",
        "newline",
        "period",
        "colon",
        "dotted_number",
        "newline",
        "Event",
        "colon",
        "newline",
        "identifier",
        "colon",
        "string",
        "newline",
        "GROUP",
        "colon",
        "lparen",
        "identifier",
        "number",
        "carrot",
        "number",
        "rparen",
        "newline",
        "end_law",
        "newline",
        "end_target",
        "EOF",
        "dictionnary",
    ]

    actual_types = set([t["type"] for t in tokens if t["type"] != "whitespace"])
    assert actual_types == set(expected_types)


def test_get_tokens_without_whitespace(lexer):
    """Test filtering of whitespace tokens."""
    lexer.tokenise()
    filtered = lexer.get_tokens_without_whitespace()

    assert all(t["type"] not in ["whitespace", "newline", "EOF"] for t in filtered)


def test_debug_tokens(lexer):
    """Test debug tokens output."""
    debug_output = lexer.debug_tokens()
    assert isinstance(debug_output, str)
    assert len(debug_output) > 0
    assert "target" in debug_output
    assert "law" in debug_output


def test_token_positions():
    """Test token line and column positions."""
    code = """target test:
    key:"value"
"""

    lexer = Lexer(code)
    tokens = lexer.tokenise()

    # Check first token
    assert tokens[0]["type"] == "target"
    assert tokens[0]["line"] == 1
    assert tokens[0]["col"] == 1

    # Check identifier on first line
    identifier_tokens = [
        t for t in tokens if t["type"] == "identifier" and t["line"] == 1
    ]
    assert len(identifier_tokens) == 1
    assert identifier_tokens[0]["col"] == 8  # "test" starts at column 8


def test_multiline_string():
    """Test tokenization of multiline strings."""
    code = 'key:"multi\\nline\\nstring"'
    lexer = Lexer(code)
    tokens = lexer.tokenise()

    string_tokens = [t for t in tokens if t["type"] == "string"]
    assert len(string_tokens) == 1
    assert "multi\\nline\\nstring" in string_tokens[0]["value"]


def test_numbers_and_dotted_numbers():
    """Test tokenization of numbers and dotted numbers."""
    code = "1 1.0 1.0.0 1.0.0.0 1.0.0.0.0"
    lexer = Lexer(code)
    tokens = lexer.tokenise()

    # Filter out whitespace and EOF
    tokens = [t for t in tokens if t["type"] not in ["whitespace", "EOF"]]

    assert len(tokens) == 5
    assert tokens[0]["type"] == "number"
    assert tokens[0]["value"] == "1"
    assert tokens[1]["type"] == "dotted_number"
    assert tokens[1]["value"] == "1.0"
    assert tokens[4]["type"] == "dotted_number"
    assert tokens[4]["value"] == "1.0.0.0.0"


def test_keywords_as_identifiers():
    """Test that keywords can appear in identifiers."""
    code = "lawlaw targettarget start_datetime"
    lexer = Lexer(code)
    tokens = lexer.tokenise()

    # Filter out whitespace and EOF
    tokens = [t for t in tokens if t["type"] not in ["whitespace", "EOF"]]

    assert len(tokens) == 3
    assert all(t["type"] == "identifier" for t in tokens)
    assert tokens[0]["value"] == "lawlaw"
    assert tokens[1]["value"] == "targettarget"
    assert tokens[2]["value"] == "start_datetime"


@pytest.mark.slow
def test_large_input():
    """Test tokenization of large input."""
    # Template de loi pour le test de charge
    law_template = (
        "    law l{}:\n"
        "        start_date:2024-01-01 at 10:00\n"
        "        period:1.0\n"
        "        Event:\n"
        "            A:\"test\"\n"
        "        GROUP:(A 1.0^0)\n"
        "    end_law\n"
    )

    code = (
        'target large:\n    key:"test"\n'
        + "".join(law_template.format(i) for i in range(100))
        + "end_target"
    )

    lexer = Lexer(code)
    tokens = lexer.tokenise()

    assert len(tokens) > 1000
    assert tokens[-1]["type"] == "EOF"
