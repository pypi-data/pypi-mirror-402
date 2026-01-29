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
Integration tests for Zenith Analyser.
"""

import json
import os
import tempfile
import time
import tracemalloc

import pytest

from src.zenith_analyser import ASTUnparser, Validator, ZenithAnalyser


@pytest.mark.integration
def test_full_workflow(sample_code):
    """Test complete workflow from code to analysis."""
    # 1. Create analyser
    analyser = ZenithAnalyser(sample_code)

    # 2. Validate no errors in parsing
    assert len(analyser.parser_errors) == 0

    # 3. Get corpus statistics
    analysis = analyser.analyze_corpus()
    assert analysis["validation"]["lexer"] is True
    assert analysis["validation"]["parser"] is True
    assert analysis["validation"]["ast"] is True

    # 4. Analyze specific law
    law_desc = analyser.law_description("test_law")
    assert law_desc["name"] == "test_law"
    assert law_desc["total_duration_minutes"] > 0

    # 5. Analyze specific target
    target_desc = analyser.target_description("test_target")
    assert "event_metrics" in target_desc

    # 6. Test unparse
    unparser = ASTUnparser(analyser.ast)
    unparsed = unparser.unparse()
    assert len(unparsed) > 0

    # 7. Parse unparsed code
    analyser2 = ZenithAnalyser(unparsed)
    assert len(analyser2.parser_errors) == 0

    # 8. Compare key elements
    law_desc2 = analyser2.law_description("test_law")
    assert law_desc2["name"] == "test_law"
    # Allow small differences in time calculations
    duration_diff = abs(
        law_desc["total_duration_minutes"] - law_desc2["total_duration_minutes"]
    )
    assert duration_diff <= 1


@pytest.mark.integration
def test_complex_hierarchy_workflow(complex_code):
    """Test workflow with complex hierarchy."""
    analyser = ZenithAnalyser(complex_code)

    # Check all components are present
    assert "parent" in analyser.target_analyser.targets
    assert "child" in analyser.target_analyser.targets
    assert "parent_law" in analyser.law_analyser.laws
    assert "child_law" in analyser.law_analyser.laws

    # Test population analysis
    for population in [1, 2, -1]:
        pop_desc = analyser.population_description(population)
        expected_level = 2 if population == -1 else population
        stats = pop_desc["population_stats"]
        assert stats["population_level"] == expected_level
        assert stats["total_laws"] > 0

    # Test target hierarchy
    hierarchy = analyser.target_analyser.get_target_hierarchy("child")
    assert hierarchy["parent"] == "parent"
    assert hierarchy["depth"] == 2
    assert "child_law" in hierarchy["direct_laws"]
    assert "parent_law" in hierarchy["descendant_laws"]

    # Test dictionary inheritance
    child_laws = analyser.target_analyser.extract_laws_for_target("child")
    assert "child_law" in child_laws
    # Check that event description is from child's dictionary
    event_desc = child_laws["child_law"]["dictionnary"][0]["description"]
    assert event_desc == "Base_event"


@pytest.mark.integration
def test_file_io_workflow(sample_code, temp_file, temp_json_file):
    """Test file input/output workflow."""
    # 1. Write code to file
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(sample_code)

    # 2. Read and analyze
    with open(temp_file, "r", encoding="utf-8") as f:
        code = f.read()

    analyser = ZenithAnalyser(code)

    # 3. Export to JSON
    analyser.export_json(temp_json_file)

    # 4. Verify JSON
    with open(temp_json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "corpus_statistics" in data
    assert "laws" in data
    assert "targets" in data

    # 5. Unparse from AST and write back
    unparser = ASTUnparser(analyser.ast)
    unparsed = unparser.unparse()

    unparsed_file = temp_file + ".unparsed"
    with open(unparsed_file, "w", encoding="utf-8") as f:
        f.write(unparsed)

    # Cleanup
    if os.path.exists(unparsed_file):
        os.unlink(unparsed_file)


@pytest.mark.integration
def test_performance_workflow():
    """Test performance of complete workflow."""
    # Create moderately large code
    code_parts = ['target perf_test:\n    key:"test"\n    dictionnary:']

    # Add 100 dictionary entries
    for i in range(100):
        code_parts.append(f'        ev{i}:"Event {i}"')

    code_parts.append("")

    # Add 30 laws
    for i in range(30):
        code_parts.append(
            f"""    law law_{i}:
        start_date:2024-01-{i+1:02d} at 10:00
        period:1.0
        Event:
            A[ev{i % 100}]:"Description {i}"
        GROUP:(A 1.0^0)
    end_law"""
        )

    code_parts.append("end_target")
    code = "\n".join(code_parts)

    # Time the analysis
    start_time = time.time()
    analyser = ZenithAnalyser(code)
    parse_time = time.time() - start_time

    # Should complete in reasonable time
    assert parse_time < 5.0, f"Parsing took too long: {parse_time:.2f}s"

    # Time corpus analysis
    start_time = time.time()
    analysis = analyser.analyze_corpus()
    analysis_time = time.time() - start_time

    assert analysis_time < 2.0, f"Analysis took too long: {analysis_time:.2f}s"

    # Verify results
    assert analysis["corpus_statistics"]["total_laws"] == 30
    assert analysis["corpus_statistics"]["total_targets"] == 1


@pytest.mark.integration
def test_cli_simulation():
    """Simulate CLI workflow programmatically."""
    from src.zenith_analyser.cli import format_output

    # Test code
    code = """
target cli_test:
    key:"CLI Test"
    dictionnary:
        ev1:"CLI_event"
    law example:
        start_date:2024-01-01 at 10:00
        period:1.0
        Event:
            A:"Test event"
        GROUP:(A 1.0^0)
    end_law
end_target
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".zenith") as f:
        f.write(code)
        temp_path = f.name

    try:
        # Test validation
        class Args:
            def __init__(self):
                self.input = temp_path
                self.strict = False

        _ = Args()  # Corrected F841: variable assigned but never used

        validator = Validator()
        errors = validator.validate_code(code)
        assert len(errors) == 0

        # Test analysis
        analyser = ZenithAnalyser(code)
        result = analyser.analyze_corpus()

        # Test formatting
        json_output = format_output(result, "json", True)
        assert '"corpus_statistics"' in json_output

        text_output = format_output(result, "text", False)
        assert "Corpus Statistics:" in text_output

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.integration
def test_round_trip_fidelity():
    """Test that round-trip parsing preserves semantics."""
    code = """
target fidelity_test:
    key:"Fidelity test"
    dictionnary:
        work:"Work_activity"
        break:"Break_time"

    law daily:
        start_date:2024-01-01 at 09:00
        period:8.0
        Event:
            morning[work]:"Morning_work_session"
            lunch[break]:"Lunch_break"
            afternoon[work]:"Afternoon_work_session"
        GROUP:(morning 4.0^1.0 - lunch 1.0^1.0 - afternoon 3.0^0)
    end_law
end_target
"""

    # Parse
    analyser1 = ZenithAnalyser(code)
    law_desc1 = analyser1.law_description("daily")

    # Unparse
    unparser = ASTUnparser(analyser1.ast)
    unparsed = unparser.unparse()

    # Parse again
    analyser2 = ZenithAnalyser(unparsed)
    law_desc2 = analyser2.law_description("daily")

    # Compare key metrics
    metrics1 = [
        law_desc1["total_duration_minutes"],
        law_desc1["coherence_total_minutes"],
        law_desc1["dispersal_total_minutes"],
        len(law_desc1["simulation"]),
    ]

    metrics2 = [
        law_desc2["total_duration_minutes"],
        law_desc2["coherence_total_minutes"],
        law_desc2["dispersal_total_minutes"],
        len(law_desc2["simulation"]),
    ]

    for m1, m2 in zip(metrics1, metrics2):
        assert abs(m1 - m2) <= 1, f"Metric mismatch: {m1} vs {m2}"

    # Compare event names and order
    events1 = [e["event_name"] for e in law_desc1["simulation"]]
    events2 = [e["event_name"] for e in law_desc2["simulation"]]
    assert events1 == events2


@pytest.mark.integration
def test_memory_usage():
    """Test memory usage doesn't explode."""
    # Create large code
    code_lines = ['target large:\n    key:"test"\n    dictionnary:']

    for i in range(1000):
        code_lines.append(f'        e{i}:"Event {i}"')

    code_lines.append("")

    for i in range(100):
        code_lines.append(
            f"""    law l{i}:
        start_date:2024-01-01 at 10:00
        period:1.0
        Event:
            A[e{i % 1000}]:"Description"
        GROUP:(A 1.0^0)
    end_law"""
        )

    code_lines.append("end_target")
    code = "\n".join(code_lines)

    tracemalloc.start()
    try:
        snapshot1 = tracemalloc.take_snapshot()
        analyser = ZenithAnalyser(code)
        snapshot2 = tracemalloc.take_snapshot()

        stats = snapshot2.compare_to(snapshot1, "lineno")
        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

        assert total_increase < 50 * 1024 * 1024

        snapshot3 = tracemalloc.take_snapshot()
        _ = analyser.analyze_corpus()  # Corrected F841: unused analysis
        snapshot4 = tracemalloc.take_snapshot()

        stats = snapshot4.compare_to(snapshot3, "lineno")
        analysis_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

        assert analysis_increase < 10 * 1024 * 1024

    finally:
        tracemalloc.stop()
