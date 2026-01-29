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
Tests for the Parser class.
"""

import pytest

from src.zenith_analyser import Parser


def test_parser_initialization(sample_code, lexer):
    """Test parser initialization."""
    tokens = lexer.tokenise()
    parser = Parser(tokens)

    assert parser.tokens == tokens
    assert parser.pos == 0
    assert parser.errors == []


def test_parse_basic(sample_code, parser):
    """Test basic parsing."""
    ast, errors = parser.parse()

    assert isinstance(ast, dict)
    assert ast["type"] == "corpus_textuel"
    assert "elements" in ast
    assert len(errors) == 0

    # Check structure
    elements = ast["elements"]
    assert len(elements) == 1
    assert elements[0]["type"] == "target"
    assert elements[0]["name"] == "test_target"


def test_parse_empty():
    """Test parsing empty input."""
    from src.zenith_analyser import Lexer

    lexer = Lexer("")
    tokens = lexer.tokenise()
    parser = Parser(tokens)

    ast, errors = parser.parse()

    assert ast["type"] == "corpus_textuel"
    assert ast["elements"] == []
    assert len(errors) == 0


def test_parse_invalid_syntax():
    """Test parsing invalid syntax."""
    from src.zenith_analyser import Lexer

    code = "target test: law missing_colon"
    lexer = Lexer(code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)

    ast, errors = parser.parse()

    assert len(errors) > 0
    assert "Expected" in errors[0] or "Parsing error" in errors[0]


def test_parse_law_structure(sample_code, parser):
    """Test parsing of law structure."""
    ast, errors = parser.parse()

    target = ast["elements"][0]
    blocks = target["contents"]["blocks"]
    law = blocks[0]

    assert law["type"] == "law"
    assert law["name"] == "test_law"

    contents = law["contents"]
    assert contents["start_date"]["date"] == "2024-01-01"
    assert contents["start_date"]["time"] == "10:00"
    assert contents["period"] == "1.0"

    # Check events
    events = contents["events"]
    assert len(events) == 2
    assert events[0]["name"] == "A"
    assert events[0]["index"] == "ev1"
    assert events[0]["description"] == "First_event"

    # Check group
    group = contents["group"]
    assert len(group) == 2
    assert group[0]["name"] == "A"
    assert group[0]["chronocoherence"] == "30"
    assert group[0]["chronodispersal"] == "15"


def test_parse_target_structure(sample_code, parser):
    """Test parsing of target structure."""
    ast, errors = parser.parse()

    target = ast["elements"][0]

    assert target["type"] == "target"
    assert target["name"] == "test_target"
    assert target["contents"]["key"] == "Test key"

    # Check dictionnary
    dictionnary = target["contents"]["dictionnary"]
    assert len(dictionnary) == 2
    assert dictionnary[0]["name"] == "ev1"
    assert dictionnary[0]["description"] == "Test_event 1"

    # Check blocks
    blocks = target["contents"]["blocks"]
    assert len(blocks) == 1
    assert blocks[0]["type"] == "law"


def test_parse_complex_hierarchy(complex_code):
    """Test parsing of complex hierarchy."""
    from src.zenith_analyser import Lexer

    lexer = Lexer(complex_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)

    ast, errors = parser.parse()

    assert len(errors) == 0

    # Check parent target
    parent = ast["elements"][0]
    assert parent["name"] == "parent"
    assert parent["contents"]["key"] == "Parent key"

    # Check child target
    blocks = parent["contents"]["blocks"]
    child = blocks[0]
    assert child["type"] == "target"
    assert child["name"] == "child"
    assert child["contents"]["key"] == "Child key"

    # Check laws
    child_blocks = child["contents"]["blocks"]
    assert child_blocks[0]["type"] == "law"
    assert child_blocks[0]["name"] == "child_law"


def test_get_ast_summary(parser):
    """Test get_ast_summary method."""
    ast, errors = parser.parse()
    summary = parser.get_ast_summary(ast)

    assert isinstance(summary, dict)
    assert "total_laws" in summary
    assert "total_targets" in summary
    assert "max_nesting" in summary
    assert "events_by_law" in summary
    assert "target_hierarchy" in summary

    # Check specific values for sample code
    assert summary["total_laws"] == 1
    assert summary["total_targets"] == 1
    assert "test_law" in summary["events_by_law"]
    assert summary["events_by_law"]["test_law"] == 2


@pytest.mark.integration
def test_parse_round_trip(sample_code):
    """Test parse -> unparse round trip."""
    from src.zenith_analyser import ASTUnparser, Lexer, Parser

    # Parse
    lexer = Lexer(sample_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast, errors = parser.parse()

    assert len(errors) == 0

    # Unparse
    unparser = ASTUnparser(ast)
    unparsed = unparser.unparse()

    # Parse again
    lexer2 = Lexer(unparsed)
    tokens2 = lexer2.tokenise()
    parser2 = Parser(tokens2)
    ast2, errors2 = parser2.parse()

    assert len(errors2) == 0

    # Basic structure should match
    assert ast["type"] == ast2["type"]
    assert len(ast["elements"]) == len(ast2["elements"])
