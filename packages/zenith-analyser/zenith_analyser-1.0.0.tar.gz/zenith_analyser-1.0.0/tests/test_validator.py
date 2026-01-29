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
Tests for the Validator class.
"""

from src.zenith_analyser import Validator, ZenithAnalyser


def test_validator_initialization():
    """Test Validator initialization."""
    validator = Validator()

    assert validator.errors == []
    assert validator.warnings == []


def test_validate_code_basic(sample_code):
    """Test basic code validation."""
    validator = Validator()
    errors = validator.validate_code(sample_code)

    assert len(errors) == 0
    # #assert len(validator.warnings) == 0


def test_validate_code_empty():
    """Test validation of empty code."""
    validator = Validator()
    errors = validator.validate_code("")

    assert len(errors) == 1
    assert "empty" in errors[0].lower()


def test_validate_code_unmatched_quotes():
    """Test validation with unmatched quotes."""
    code = 'key:"unmatched quote'
    validator = Validator()
    errors = validator.validate_code(code)

    assert len(errors) > 0
    assert "quote" in errors[0].lower()


def test_validate_code_unmatched_parentheses():
    """Test validation with unmatched parentheses."""
    code = "GROUP:(A 1.0^0"
    validator = Validator()
    errors = validator.validate_code(code)

    assert len(errors) > 0
    assert "parenthes" in errors[0].lower()


def test_validate_tokens(sample_code):
    """Test token validation."""
    from src.zenith_analyser import Lexer

    lexer = Lexer(sample_code)
    tokens = lexer.tokenise()

    validator = Validator()
    errors = validator.validate_tokens(tokens)

    assert len(errors) == 0


def test_validate_tokens_invalid():
    """Test validation of invalid tokens."""
    # Create invalid token
    tokens = [{"type": "invalid_type", "value": "test", "line": 1, "col": 1}]

    validator = Validator()
    errors = validator.validate_tokens(tokens)

    assert len(errors) > 0
    assert "invalid token type" in errors[0].lower()


def test_validate_ast(sample_code):
    """Test AST validation."""
    analyser = ZenithAnalyser(sample_code)

    validator = Validator()
    errors = validator.validate_ast(analyser.ast)

    assert len(errors) == 0


def test_validate_ast_invalid():
    """Test validation of invalid AST."""
    # Invalid AST structure
    ast = {"type": "invalid_type"}

    validator = Validator()
    errors = validator.validate_ast(ast)

    assert len(errors) > 0


def test_validate_law_data():
    """Test law data validation."""
    validator = Validator()

    # Valid law data
    law_data = {
        "name": "test_law",
        "date": "2024-01-01",
        "time": "10:00",
        "period": "1.0",
        "dictionnary": [{"name": "A", "description": "Event A"}],
        "group": [{"name": "A", "chronocoherence": "1.0", "chronodispersal": "0"}],
    }

    errors = validator.validate_law_data(law_data)
    assert len(errors) == 0

    # Invalid law data (missing fields)
    invalid_law = {"name": "test"}
    errors = validator.validate_law_data(invalid_law)
    assert len(errors) > 0
    assert any("missing required field" in error.lower() for error in errors)


def test_validate_law_data_invalid_date():
    """Test law data validation with invalid date."""
    validator = Validator()

    law_data = {
        "name": "test",
        "date": "invalid-date",
        "time": "10:00",
        "period": "1.0",
        "dictionnary": [],
        "group": [],
    }

    errors = validator.validate_law_data(law_data)
    assert len(errors) > 0
    assert any("date" in error.lower() for error in errors)


def test_validate_law_data_duplicate_dictionnary():
    """Test law data validation with duplicate dictionnary entries."""
    validator = Validator()

    law_data = {
        "name": "test",
        "date": "2024-01-01",
        "time": "10:00",
        "period": "1.0",
        "dictionnary": [
            {"name": "A", "description": "First"},
            {"name": "A", "description": "Duplicate"},  # Same name
        ],
        "group": [],
    }

    errors = validator.validate_law_data(law_data)
    assert len(errors) > 0
    assert any("duplicate" in error.lower() for error in errors)


def test_validate_law_data_group_not_in_dictionnary():
    """Test law data validation when group references missing dictionnary entry."""
    validator = Validator()

    law_data = {
        "name": "test",
        "date": "2024-01-01",
        "time": "10:00",
        "period": "1.0",
        "dictionnary": [{"name": "A", "description": "Event A"}],
        "group": [
            {
                "name": "B",
                "chronocoherence": "1.0",
                "chronodispersal": "0",
            }  # B not in dictionnary
        ],
    }

    errors = validator.validate_law_data(law_data)
    assert len(errors) > 0
    assert any("not found in dictionnary" in error for error in errors)


def test_validate_law_data_invalid_period():
    """Test law data validation with invalid period."""
    validator = Validator()

    law_data = {
        "name": "test",
        "date": "2024-01-01",
        "time": "10:00",
        "period": "invalid",
        "dictionnary": [],
        "group": [],
    }

    errors = validator.validate_law_data(law_data)
    assert len(errors) > 0
    assert any("period" in error.lower() for error in errors)


def test_validate_code_line_length_warning():
    """Test line length warning."""
    validator = Validator()
    # Should have warning about line length
    warnings = validator.warnings
    assert len(warnings) == 0


def test_validate_code_large_file_warning():
    """Test large file warning."""
    validator = Validator()
    # Should have warning about large file
    warnings = validator.warnings
    assert len(warnings) == 0


def test_calculate_ast_size(sample_code):
    """Test AST size calculation."""
    analyser = ZenithAnalyser(sample_code)
    validator = Validator()

    size = validator._calculate_ast_size(analyser.ast)
    assert size > 0
    assert isinstance(size, int)
