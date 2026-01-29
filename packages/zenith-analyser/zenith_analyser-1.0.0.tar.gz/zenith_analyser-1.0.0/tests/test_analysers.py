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
Tests for the analyser classes.
"""

import json
import pytest

from src.zenith_analyser import (
    LawAnalyser,
    TargetAnalyser,
    ZenithAnalyser,
    ZenithAnalyserError,
)


def test_law_analyser_initialization(parser):
    """Test LawAnalyser initialization."""
    ast = parser.parse()[0]
    analyser = LawAnalyser(ast)

    assert analyser.ast == ast
    assert isinstance(analyser.laws, dict)
    assert len(analyser.laws) > 0


def test_extract_laws(sample_code):
    """Test law extraction."""
    from src.zenith_analyser import Lexer, Parser

    lexer = Lexer(sample_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast = parser.parse()[0]

    analyser = LawAnalyser(ast)
    laws = analyser.extract_laws(ast)

    assert isinstance(laws, dict)
    assert "test_law" in laws

    law = laws["test_law"]
    assert law["name"] == "test_law"
    assert law["date"] == "2024-01-01"
    assert law["time"] == "10:00"
    assert law["period"] == "1.0"
    assert isinstance(law["dictionnary"], list)
    assert isinstance(law["group"], list)

    # Check dictionnary
    assert len(law["dictionnary"]) == 2
    assert law["dictionnary"][0]["name"] == "A"
    assert law["dictionnary"][0]["index"] == "ev1"
    assert law["dictionnary"][0]["description"] == "First_event"

    # Check group
    assert len(law["group"]) == 2
    assert law["group"][0]["name"] == "A"
    assert law["group"][0]["chronocoherence"] == "30"
    assert law["group"][0]["chronodispersal"] == "15"


def test_get_law_names(parser):
    """Test getting law names."""
    ast = parser.parse()[0]
    analyser = LawAnalyser(ast)

    names = analyser.get_law_names()

    assert isinstance(names, list)
    assert "test_law" in names


def test_get_law(parser):
    """Test getting specific law."""
    ast = parser.parse()[0]
    analyser = LawAnalyser(ast)

    law = analyser.get_law("test_law")
    assert law is not None
    assert law["name"] == "test_law"

    # Non-existent law
    law = analyser.get_law("non_existent")
    assert law is None


def test_validate_law(parser):
    """Test law validation."""
    ast, _ = parser.parse()
    analyser = LawAnalyser(ast)

    errors = analyser.validate_law("test_law")
    assert len(errors) == 0

    # Test with invalid law data (simulated)
    analyser.laws["invalid_law"] = {"name": "invalid"}
    errors = analyser.validate_law("invalid_law")
    assert len(errors) > 0
    assert any("Missing required field" in error for error in errors)


def test_target_analyser_initialization(parser):
    """Test TargetAnalyser initialization."""
    ast = parser.parse()[0]
    analyser = TargetAnalyser(ast)

    assert analyser.ast == ast
    assert isinstance(analyser.law_analyser, LawAnalyser)
    assert isinstance(analyser.targets, dict)


def test_extract_targets(complex_code):
    """Test target extraction."""
    from src.zenith_analyser import Lexer, Parser

    lexer = Lexer(complex_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast = parser.parse()[0]

    analyser = TargetAnalyser(ast)
    targets = analyser.targets

    assert isinstance(targets, dict)
    assert "parent" in targets
    assert "child" in targets

    # Check parent target
    parent = targets["parent"]
    assert parent["name"] == "parent"
    assert parent["key"] == "Parent key"
    assert parent["depth"] == 1
    assert parent["path"] == ["parent"]
    assert "child" in parent["direct_targets"]

    # Check child target
    child = targets["child"]
    assert child["name"] == "child"
    assert child["key"] == "Child key"
    assert child["depth"] == 2
    assert child["path"] == ["parent", "child"]
    assert "child_law" in child["direct_laws"]


def test_get_target_hierarchy(complex_code):
    """Test getting target hierarchy."""
    from src.zenith_analyser import Lexer, Parser

    lexer = Lexer(complex_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast = parser.parse()[0]

    analyser = TargetAnalyser(ast)

    # Test parent hierarchy
    hierarchy = analyser.get_target_hierarchy("parent")
    assert hierarchy["name"] == "parent"
    assert hierarchy["parent"] is None
    assert "child" in hierarchy["children"]
    assert "child" in hierarchy["descendants"]
    assert "parent_law" in hierarchy["descendant_laws"]
    assert "child_law" in hierarchy["descendant_laws"]

    # Test child hierarchy
    hierarchy = analyser.get_target_hierarchy("child")
    assert hierarchy["name"] == "child"
    assert hierarchy["parent"] == "parent"
    assert hierarchy["children"] == []
    assert "child_law" in hierarchy["direct_laws"]


def test_extract_laws_for_target(complex_code):
    """Test extracting laws for target with inheritance."""
    from src.zenith_analyser import Lexer, Parser

    lexer = Lexer(complex_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast = parser.parse()[0]

    analyser = TargetAnalyser(ast)

    # Extract laws for child target
    laws = analyser.extract_laws_for_target("child")

    assert isinstance(laws, dict)
    assert "child_law" in laws

    child_law = laws["child_law"]
    assert child_law["name"] == "child_law"

    # Check that dictionary inheritance worked
    dictionnary = child_law["dictionnary"]
    assert len(dictionnary) == 1
    assert dictionnary[0]["description"] == "Derived_event"


def test_get_targets_by_generation(complex_code):
    """Test getting targets by generation."""
    from src.zenith_analyser import Lexer, Parser

    lexer = Lexer(complex_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast = parser.parse()[0]

    analyser = TargetAnalyser(ast)

    # Generation 1 (root)
    gen1 = analyser.get_targets_by_generation(1)
    assert "parent" in gen1
    assert len(gen1) == 1

    # Generation 2
    gen2 = analyser.get_targets_by_generation(2)
    assert "child" in gen2
    assert len(gen2) == 1

    # Generation 3 (nonexistent)
    gen3 = analyser.get_targets_by_generation(3)
    assert len(gen3) == 0


def test_get_max_generation(complex_code):
    """Test getting maximum generation."""
    from src.zenith_analyser import Lexer, Parser

    lexer = Lexer(complex_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast, _ = parser.parse()

    analyser = TargetAnalyser(ast)

    max_gen = analyser.get_max_generation()
    assert max_gen == 2


def test_get_targets_by_key(complex_code):
    """Test getting targets by key."""
    from src.zenith_analyser import Lexer, Parser

    lexer = Lexer(complex_code)
    tokens = lexer.tokenise()
    parser = Parser(tokens)
    ast, _ = parser.parse()

    analyser = TargetAnalyser(ast)

    # Test existing key
    targets = analyser.get_targets_by_key("Child key")
    assert "child" in targets

    # Test non-existent key
    targets = analyser.get_targets_by_key("Non-existent key")
    assert len(targets) == 0


def test_zenith_analyser_initialization(sample_code):
    """Test ZenithAnalyser initialization."""
    analyser = ZenithAnalyser(sample_code)

    assert analyser.code == sample_code
    assert analyser.tokens is not None
    assert analyser.ast is not None
    assert isinstance(analyser.law_analyser, LawAnalyser)
    assert isinstance(analyser.target_analyser, TargetAnalyser)


def test_law_description(sample_code):
    """Test law description generation."""
    analyser = ZenithAnalyser(sample_code)

    description = analyser.law_description("test_law")

    assert isinstance(description, dict)
    assert description["name"] == "test_law"
    assert description["start_date"] == "2024-01-01"
    assert description["start_time"] == "10:00"
    assert "period_minutes" in description
    assert "total_duration_minutes" in description
    assert "simulation" in description
    assert "event_metrics" in description

    # Check simulation
    simulation = description["simulation"]
    assert len(simulation) == 2
    assert simulation[0]["event_name"] == "First_event"
    assert "duration_minutes" in simulation[0]

    # Check event metrics
    metrics = description["event_metrics"]
    assert len(metrics) == 2
    assert metrics[0]["name"] == "First_event"
    assert "count" in metrics[0]
    assert "total_coherence_minutes" in metrics[0]


def test_law_description_nonexistent(sample_code):
    """Test law description for non-existent law."""
    analyser = ZenithAnalyser(sample_code)

    with pytest.raises(ZenithAnalyserError) as exc_info:
        analyser.law_description("non_existent")

    assert "not found" in str(exc_info.value)


def test_target_description(sample_code):
    """Test target description generation."""
    analyser = ZenithAnalyser(sample_code)

    description = analyser.target_description("test_target")

    assert isinstance(description, dict)
    assert "name" in description
    assert "simulation" in description
    assert "event_metrics" in description

    # Should have merged events from all laws in target
    simulation = description["simulation"]
    assert len(simulation) >= 2


def test_population_description(complex_code):
    """Test population description generation."""
    analyser = ZenithAnalyser(complex_code)

    # Test population 1 (root)
    description = analyser.population_description(1)

    assert isinstance(description, dict)
    assert "population_stats" in description
    assert "law_descriptions" in description
    assert "all_events" in description
    assert "event_statistics" in description

    stats = description["population_stats"]
    assert stats["population_level"] == 1
    assert stats["total_laws"] > 0

    # Test population -1 (max)
    description = analyser.population_description(-1)
    stats = description["population_stats"]
    assert stats["population_level"] == 2


def test_analyze_corpus(sample_code):
    """Test complete corpus analysis."""
    analyser = ZenithAnalyser(sample_code)

    analysis = analyser.analyze_corpus()

    assert isinstance(analysis, dict)
    assert "corpus_statistics" in analysis
    assert "ast_summary" in analysis
    assert "laws" in analysis
    assert "targets" in analysis
    assert "validation" in analysis

    stats = analysis["corpus_statistics"]
    assert "total_laws" in stats
    assert "total_targets" in stats
    assert "total_events" in stats

    validation = analysis["validation"]
    assert "lexer" in validation
    assert "parser" in validation
    assert "ast" in validation
    assert all(v is True for v in validation.values())


def test_export_json(sample_code, temp_json_file):
    """Test JSON export."""
    analyser = ZenithAnalyser(sample_code)

    analyser.export_json(temp_json_file)

    # Verify file was created and contains valid JSON
    with open(temp_json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert "corpus_statistics" in data


def test_get_debug_info(sample_code):
    """Test debug information."""
    analyser = ZenithAnalyser(sample_code)

    debug_info = analyser.get_debug_info()

    assert isinstance(debug_info, dict)
    assert "code_length" in debug_info
    assert "token_count" in debug_info
    assert "ast_size" in debug_info
    assert "law_count" in debug_info
    assert "target_count" in debug_info
    assert "parser_errors" in debug_info
    assert "timestamp" in debug_info


def test_point_conversion_utilities():
    """Test point conversion utilities."""
    from src.zenith_analyser.utils import minutes_to_point, point_to_minutes

    # Test point_to_minutes
    test_cases = [
        ("1.0", 60),
        ("1", 1),
        ("1.0.0", 1440),
        ("1.0.0.0", 43200),
        ("1.0.0.0.0", 518400),
        ("1.30", 90),
        ("1.15.0", 2340),
    ]

    for point, expected in test_cases:
        result = point_to_minutes(point)
        assert result == expected, (
            f"Failed for {point}: got {result}, expected {expected}"
        )

    # Test minutes_to_point (round trip)
    test_minutes = [60, 90, 1440, 1500, 43200, 525600]

    for minutes in test_minutes:
        point = minutes_to_point(minutes)
        converted_back = point_to_minutes(point)
        assert abs(converted_back - minutes) <= 1, (
            f"Round trip failed for {minutes}: got {converted_back}"
        )


def test_time_calculation_utilities():
    """Test time calculation utilities."""
    from src.zenith_analyser.utils import (
        add_minutes_to_datetime,
        calculate_duration,
        format_datetime,
        parse_datetime,
    )

    # Test parse_datetime
    dt = parse_datetime("2024-01-01", "10:30")
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 10
    assert dt.minute == 30

    # Test format_datetime
    formatted = format_datetime(dt)
    assert formatted["date"] == "2024-01-01"
    assert formatted["time"] == "10:30"

    # Test calculate_duration
    dt2 = parse_datetime("2024-01-01", "11:30")
    duration = calculate_duration(dt, dt2)
    assert duration == 60

    # Test add_minutes_to_datetime
    dt3 = add_minutes_to_datetime(dt, 90)
    assert dt3.hour == 12
    assert dt3.minute == 0


@pytest.mark.integration
def test_complete_workflow(complex_code):
    """Test complete analysis workflow."""
    analyser = ZenithAnalyser(complex_code)

    # 1. Get corpus analysis
    analysis = analyser.analyze_corpus()
    assert analysis["validation"]["lexer"] is True
    assert analysis["validation"]["parser"] is True

    # 2. Analyze specific law
    law_desc = analyser.law_description("parent_law")
    assert law_desc["name"] == "parent_law"

    # 3. Analyze specific target
    target_desc = analyser.target_description("child")
    assert "event_metrics" in target_desc

    # 4. Analyze population
    pop_desc = analyser.population_description(1)
    assert pop_desc["population_stats"]["population_level"] == 1

    # 5. Get debug info
    debug_info = analyser.get_debug_info()
    assert "timestamp" in debug_info


def test_error_handling():
    """Test error handling in analysers."""
    code = "invalid syntax here"

    with pytest.raises(Exception):
        ZenithAnalyser(code)

    code = """law test:
start_date:2024-01-01 at 10:00
period:1.0
Event: A:"test"
GROUP:(A 1.0^0)
end_law"""
    analyser = ZenithAnalyser(code)

    with pytest.raises(ZenithAnalyserError):
        analyser.law_description("non_existent")

    with pytest.raises(ZenithAnalyserError):
        analyser.target_description("non_existent")
