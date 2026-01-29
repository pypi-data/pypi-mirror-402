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
Analyzers for Zenith language structures.

Contains LawAnalyser, TargetAnalyser, and ZenithAnalyser classes.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
import json

from .exceptions import ZenithAnalyserError, ZenithTimeError, ZenithValidationError
from .utils import (
    add_minutes_to_datetime,
    format_datetime,
    minutes_to_point,
    parse_datetime,
    point_to_minutes,
)


class LawAnalyser:
    """
    Analyzer for individual laws.

    Extracts and validates law data from AST.
    """

    def __init__(self, ast: Dict[str, Any]):
        """
        Initialize the law analyzer.

        Args:
            ast: Abstract Syntax Tree from parser
        """
        self.ast = ast
        self.laws = self.extract_laws(self.ast)

    def extract_laws(self, ast: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract all laws from AST.

        Args:
            ast: Abstract Syntax Tree

        Returns:
            Dictionary of laws indexed by name
        """
        data_laws = {}

        def _traverse(elements: List[Dict[str, Any]]) -> None:
            for element in elements:
                if element.get("type") == "law":
                    self._extract_law_data(element, data_laws)
                elif element.get("type") == "target":
                    contents = element.get("contents", {})
                    blocks = contents.get("blocks", [])
                    _traverse(blocks)

        _traverse(ast.get("elements", []))
        return data_laws

    def _extract_law_data(
        self, law_node: Dict[str, Any], data_laws: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Extract data from a single law node.

        Args:
            law_node: Law AST node
            data_laws: Dictionary to populate
        """
        name = law_node.get("name")
        if not name:
            return

        contents = law_node.get("contents", {})
        start_date = contents.get("start_date", {})

        data_laws[name] = {
            "name": name,
            "date": start_date.get("date"),
            "time": start_date.get("time"),
            "period": contents.get("period"),
            "dictionnary": contents.get("events", []).copy(),
            "group": contents.get("group", []).copy(),
            "source_node": law_node,  # Keep reference for debugging
        }

    def get_law_names(self) -> List[str]:
        """
        Get all law names.

        Returns:
            List of law names
        """
        return list(self.laws.keys())

    def get_law(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific law by name.

        Args:
            name: Law name

        Returns:
            Law data or None if not found
        """
        return self.laws.get(name).copy() if name in self.laws else None

    def validate_law(self, name: str) -> List[str]:
        """
        Validate a specific law.

        Args:
            name: Law name

        Returns:
            List of validation errors
        """
        law = self.get_law(name)
        if not law:
            return [f"Law '{name}' not found"]

        errors = []

        required = ["date", "time", "period", "dictionnary", "group"]
        for field in required:
            if not law.get(field):
                errors.append(f"Missing required field: {field}")

        if errors:
            return errors

        try:
            parse_datetime(law["date"], law["time"])
        except ZenithTimeError as e:
            errors.append(str(e))

        try:
            point_to_minutes(law["period"])
        except ZenithTimeError as e:
            errors.append(f"Invalid period: {str(e)}")

        if not isinstance(law["dictionnary"], list):
            errors.append("Dictionnary must be a list")
        else:
            seen_names = set()
            for i, entry in enumerate(law["dictionnary"]):
                if not isinstance(entry, dict):
                    errors.append(f"Dictionnary entry {i} must be a dictionary")
                    continue

                entry_name = entry.get("name")
                if not entry_name:
                    errors.append(f"Dictionnary entry {i} missing name")
                    continue

                if entry_name in seen_names:
                    errors.append(f"Duplicate dictionnary entry: {entry_name}")
                seen_names.add(entry_name)

        if not isinstance(law["group"], list):
            errors.append("Group must be a list")
        else:
            for i, event in enumerate(law["group"]):
                if not isinstance(event, dict):
                    errors.append(f"Group event {i} must be a dictionary")
                    continue

                required_fields = ["name", "chronocoherence", "chronodispersal"]
                for field in required_fields:
                    if field not in event:
                        errors.append(f"Group event {i} missing '{field}'")

        return errors


class TargetAnalyser:
    """
    Analyzer for targets and their hierarchies.

    Extracts targets, analyzes relationships, and manages law inheritance.
    """

    def __init__(self, ast: Dict[str, Any]):
        """
        Initialize the target analyzer.

        Args:
            ast: Abstract Syntax Tree from parser
        """
        self.ast = ast
        self.law_analyser = LawAnalyser(ast)
        self.targets = self.extract_targets(ast)
        self._populate_descendants()

    def extract_targets(self, ast: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract all targets from AST.

        Args:
            ast: Abstract Syntax Tree

        Returns:
            Dictionary of targets indexed by name
        """
        data_targets = {}

        def _traverse(
            elements: List[Dict[str, Any]], current_path: List[str] = None
        ) -> None:
            if current_path is None:
                current_path = []

            for element in elements:
                if element.get("type") == "target":
                    self._extract_target_data(element, data_targets, current_path)

                    contents = element.get("contents", {})
                    blocks = contents.get("blocks", [])
                    new_path = current_path + [element["name"]]
                    _traverse(blocks, new_path)

        _traverse(ast.get("elements", []))
        return data_targets

    def _extract_target_data(
        self,
        target_node: Dict[str, Any],
        data_targets: Dict[str, Dict[str, Any]],
        current_path: List[str],
    ) -> None:
        """
        Extract data from a single target node.

        Args:
            target_node: Target AST node
            data_targets: Dictionary to populate
            current_path: Current path in hierarchy
        """
        name = target_node.get("name")
        if not name:
            return

        contents = target_node.get("contents", {})

        data_targets[name] = {
            "name": name,
            "key": contents.get("key", ""),
            "dictionnary": contents.get("dictionnary", []).copy(),
            "direct_laws": [],
            "direct_targets": [],
            "all_descendants_laws": set(),
            "all_descendants_targets": set(),
            "path": current_path + [name],
            "depth": len(current_path) + 1,
            "source_node": target_node,
        }

        blocks = contents.get("blocks", [])
        for block in blocks:
            if block.get("type") == "law":
                law_name = block.get("name")
                if law_name:
                    data_targets[name]["direct_laws"].append(law_name)
            elif block.get("type") == "target":
                target_name = block.get("name")
                if target_name:
                    data_targets[name]["direct_targets"].append(target_name)

    def _populate_descendants(self) -> None:
        """
        Populate descendant sets for all targets.
        """

        def _get_descendants(target_name: str) -> Tuple[Set[str], Set[str]]:
            if target_name not in self.targets:
                return set(), set()

            target = self.targets[target_name]

            if (
                target["all_descendants_laws"]
                and target["all_descendants_targets"]
                and len(target["all_descendants_laws"]) > 0
                and len(target["all_descendants_targets"]) > 0
            ):
                return target["all_descendants_laws"], target["all_descendants_targets"]

            descendant_laws = set(target["direct_laws"])
            descendant_targets = set(target["direct_targets"])

            for child_name in target["direct_targets"]:
                child_laws, child_targets = _get_descendants(child_name)
                descendant_laws.update(child_laws)
                descendant_targets.update(child_targets)

            target["all_descendants_laws"] = descendant_laws
            target["all_descendants_targets"] = descendant_targets

            return descendant_laws, descendant_targets

        for target_name in list(self.targets.keys()):
            _get_descendants(target_name)

    def get_target_names(self) -> List[str]:
        return list(self.targets.keys())

    def get_target(self, name: str) -> Optional[Dict[str, Any]]:
        return self.targets.get(name).copy() if name in self.targets else None

    def get_target_hierarchy(self, name: str) -> Dict[str, Any]:
        if name not in self.targets:
            raise ZenithAnalyserError(f"Target '{name}' not found", target_name=name)

        target = self.targets[name]

        return {
            "name": name,
            "path": target["path"],
            "depth": target["depth"],
            "parent": target["path"][-2] if len(target["path"]) > 1 else None,
            "children": target["direct_targets"],
            "descendants": list(target["all_descendants_targets"]),
            "direct_laws": target["direct_laws"],
            "descendant_laws": list(target["all_descendants_laws"]),
        }

    def extract_laws_for_target(self, name_target: str) -> Dict[str, Dict[str, Any]]:
        if name_target not in self.targets:
            raise ZenithAnalyserError(
                f"Target '{name_target}' not found", target_name=name_target
            )

        targets = self.extract_targets(self.ast)
        laws = self.law_analyser.extract_laws(self.ast)

        data_laws = {}

        def _traverse(target_name):
            direct_laws_names = targets[target_name]["direct_laws"]
            direct_laws = {}
            dictionnary = targets[target_name]["dictionnary"]
            direct_targets_names = targets[target_name].get("direct_targets", [])

            for name in direct_laws_names:
                direct_laws[name] = laws[name].copy()

            for dict_entry in dictionnary:
                for name in direct_laws_names:
                    for index, event in enumerate(direct_laws[name]["dictionnary"]):
                        if dict_entry["name"] == event.get("index", ""):
                            direct_laws[name]["dictionnary"][index]["description"] = (
                                dict_entry["description"]
                            )

                for name in direct_targets_names:
                    for index, event in enumerate(targets[name]["dictionnary"]):
                        if dict_entry["name"] == event.get("index", ""):
                            targets[name]["dictionnary"][index]["description"] = (
                                dict_entry["description"]
                            )

            for name in list(direct_laws.keys()):
                data_laws[name] = direct_laws[name].copy()

            for name in direct_targets_names:
                _traverse(name)

        _traverse(name_target)

        return data_laws

    def get_targets_by_generation(self, generation: int) -> List[str]:
        result = []
        for name, target in self.targets.items():
            if target["depth"] == generation:
                result.append(name)
        return result

    def get_max_generation(self) -> int:
        max_depth = 0
        for target in self.targets.values():
            if target["depth"] > max_depth:
                max_depth = target["depth"]
        return max_depth

    def get_targets_by_key(self, key: str) -> List[str]:
        result = []
        for name, target in self.targets.items():
            if target.get("key") == key:
                result.append(name)
        return result

    def corp_extract_laws_transformed(
        self, generation: int = 1
    ) -> Dict[str, Dict[str, Any]]:
        if generation < 1:
            raise ZenithValidationError(
                f"Generation level must be at least 1: {generation}",
                validation_type="generation",
            )

        data_laws = {}

        paths = {}
        targets_names = list(self.targets.keys())

        for name in targets_names:
            paths[name] = {
                "name": name,
                "path": self.targets[name]["path"],
                "generation": len(self.targets[name]["path"]),
            }

        allowed_targets_name = [
            name for name in targets_names if paths[name]["generation"] == generation
        ]

        for target_name in allowed_targets_name:
            laws = self.extract_laws_for_target(target_name)
            for name in laws:
                data_laws[name] = laws[name].copy()

        return data_laws

    def extract_laws_population(self, population: int = 1) -> Dict[str, Dict[str, Any]]:
        if population < 0:
            raise ZenithValidationError(
                f"Population level cannot be negative: {population}",
                validation_type="population",
            )

        laws_population = {}
        for i in range(population, 0, -1):
            current_gen_laws = self.corp_extract_laws_transformed(i)
            for name_gen, law_data in current_gen_laws.items():
                if name_gen not in laws_population:
                    laws_population[name_gen] = law_data.copy()

        top_level_laws = self.law_analyser.extract_laws(self.ast)

        for name_global, law_data in top_level_laws.items():
            if name_global not in laws_population:
                laws_population[name_global] = law_data.copy()

        return laws_population

    def extract_laws_max_population(self):
        return self.extract_laws_population(self.get_max_generation())


class ZenithAnalyser:
    """
    Main analyzer class with full functionality.

    Combines lexer, parser, and analyzers for complete analysis.
    """

    def __init__(self, code: str):
        """
        Initialize the Zenith analyzer.

        Args:
            code: Zenith code to analyze
        """
        from .lexer import Lexer
        from .parser import Parser
        from .validator import Validator

        self.code = code
        self.lexer = Lexer(code)
        self.tokens = self.lexer.tokenise()

        self.validator = Validator()
        validation_errors = self.validator.validate_tokens(self.tokens)
        if validation_errors:
            raise ZenithValidationError(
                f"Token validation failed: {validation_errors[0]}",
                validation_type="tokens",
            )

        self.parser = Parser(self.tokens)
        self.ast, self.parser_errors = self.parser.parse()

        if self.parser_errors:
            raise ZenithValidationError(
                f"Parsing failed: {self.parser_errors[0]}", validation_type="parsing"
            )

        ast_errors = self.validator.validate_ast(self.ast)
        if ast_errors:
            raise ZenithValidationError(
                f"AST validation failed: {ast_errors[0]}", validation_type="ast"
            )

        self.law_analyser = LawAnalyser(self.ast)
        self.target_analyser = TargetAnalyser(self.ast)

    def _simulate_law_events(
        self, law_data: Dict[str, Any], dict_map: Dict[str, str]
    ) -> List[Tuple[datetime, str, str, str]]:
        """
        Simulate events for a single law.

        Args:
            law_data: Law data dictionary
            dict_map: Dictionary mapping event names to descriptions

        Returns:
            List of simulated events as tuples
            (start_time, law_name, event_description, end_time)
        """
        if "group" not in law_data or "date" not in law_data or "time" not in law_data:
            return []
        law_name = law_data["name"]
        date = law_data["date"]
        time = law_data["time"]
        start_date = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        current_time = start_date

        simulated_events = []
        group_m = law_data["group"]

        event_descriptions = {
            item["name"]: dict_map.get(
                item["name"], item.get("description", item["name"])
            )
            for item in law_data.get("dictionnary", [])
        }

        for index, event in enumerate(group_m):
            event_id = event["name"]
            event_description = event_descriptions.get(event_id, event_id)

            chronocoherence = point_to_minutes(event["chronocoherence"])
            end_date_event = current_time + timedelta(minutes=chronocoherence)

            simulated_events.append(
                (current_time, law_name, event_description, end_date_event)
            )

            current_time = end_date_event

            if index < len(group_m) - 1:
                chronodispersal = point_to_minutes(event["chronodispersal"])
                current_time += timedelta(minutes=chronodispersal)

        return simulated_events

    def target_description(self, target_name: str) -> Dict[str, Any]:
        """
        Analyse les lois associées à un target spécifique en garantissant une séquence
        chronologique en simulant et triant les événements de toutes les lois liées,
        et retourne le résultat de law_description_data.
        """

        if target_name not in self.target_analyser.targets:
            raise ZenithAnalyserError(
                f"Target '{target_name}' not found", target_name=target_name
            )

        transformed_laws = self.target_analyser.extract_laws_for_target(target_name)

        if not transformed_laws:
            raise ZenithAnalyserError(
                f"Target '{target_name}' has no direct or descendant laws to analyze.",
                target_name=target_name,
            )

        target_dict = self.target_analyser.targets[target_name].get("dictionnary", [])
        merged_dictionnary_map = {
            item["name"]: item["description"] for item in target_dict
        }

        all_simulated_events = []

        for law_name, law_data in transformed_laws.items():
            simulated_events = self._simulate_law_events(
                law_data, merged_dictionnary_map
            )
            all_simulated_events.extend(simulated_events)

        all_simulated_events.sort(key=lambda x: x[0])

        if not all_simulated_events:
            raise ZenithAnalyserError(
                f"No simulatible events found for Target '{target_name}'.",
                target_name=target_name,
            )

        base_law_name = all_simulated_events[0][1]
        base_law_data = transformed_laws[base_law_name]

        merged_law_data = base_law_data.copy()
        merged_law_data["name"] = target_name

        first_event_start_time = all_simulated_events[0][0]
        merged_law_data["date"] = first_event_start_time.strftime("%Y-%m-%d")
        merged_law_data["time"] = first_event_start_time.strftime("%H:%M")

        new_group = []

        for i, (start_time, _, event_desc, end_time) in enumerate(all_simulated_events):
            coherence_minutes = int((end_time - start_time).total_seconds() / 60)

            dispersal_minutes = 0
            if i < len(all_simulated_events) - 1:
                next_start_time = all_simulated_events[i + 1][0]
                dispersal_minutes = int(
                    (next_start_time - end_time).total_seconds() / 60
                )

            coherence_str = (
                minutes_to_point(coherence_minutes) if coherence_minutes > 0 else "0"
            )
            dispersal_str = minutes_to_point(max(0, dispersal_minutes))

            new_group.append(
                {
                    "name": event_desc,
                    "chronocoherence": coherence_str,
                    "chronodispersal": dispersal_str,
                }
            )

        merged_law_data["group"] = new_group

        unique_event_names = sorted({event["name"] for event in new_group})
        final_dictionnary = [
            {"name": name, "description": name} for name in unique_event_names
        ]

        merged_law_data["dictionnary"] = final_dictionnary

        return self.law_description_data(target_name, merged_law_data)

    def law_description(self, name: str, population: int = 0) -> Dict[str, Any]:
        """
        Get a detailed description of a law.

        Args:
            name: Law name
            population: Population level for dictionary inheritance

        Returns:
            Detailed law description

        Raises:
            ZenithAnalyserError: If law not found or invalid
        """
        law_data = None

        if population > 0:
            transformed_laws = self.target_analyser.extract_laws_population(population)
            if name in transformed_laws:
                law_data = transformed_laws[name]

        if not law_data:
            law_data = self.law_analyser.get_law(name)
            if not law_data:
                raise ZenithAnalyserError(f"Law '{name}' not found", law_name=name)

        return self.law_description_data(name, law_data)

    def law_description_data(
        self, name: str, law_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate description from law data.

        Args:
            name: Law name
            law_data: Law data dictionary

        Returns:
            Detailed law description

        Raises:
            ZenithAnalyserError: If law data is invalid
        """
        required = ["date", "time", "period", "dictionnary", "group"]
        for field in required:
            if field not in law_data:
                raise ZenithAnalyserError(
                    f"Law data missing required field: {field}", law_name=name
                )

        group = law_data["group"].copy()

        event_descriptions = {}
        for entry in law_data["dictionnary"]:
            entry_name = entry.get("name")
            entry_desc = entry.get("description", "")
            event_descriptions[entry_name] = entry_desc or entry_name

        for event in group:
            event_name = event.get("name", "")
            if event_name in event_descriptions:
                event["name"] = event_descriptions[event_name]

        total_coherence = 0
        total_dispersal = 0

        for i, event in enumerate(group):
            coherence = point_to_minutes(event["chronocoherence"])
            total_coherence += coherence

            if i < len(group) - 1:
                dispersal = point_to_minutes(event["chronodispersal"])
                total_dispersal += dispersal

        total_duration = total_coherence + total_dispersal

        start_dt = parse_datetime(law_data["date"], law_data["time"])

        period_minutes = point_to_minutes(law_data["period"])

        end_dt = add_minutes_to_datetime(
            start_dt,
            total_duration if total_duration >= period_minutes else period_minutes,
        )

        simulation = []
        current_time = start_dt

        for i, event in enumerate(group):
            coherence = point_to_minutes(event["chronocoherence"])
            event_end = add_minutes_to_datetime(current_time, coherence)

            simulation.append(
                {
                    "event_name": event["name"],
                    "start": format_datetime(current_time),
                    "end": format_datetime(event_end),
                    "duration_minutes": int(coherence),
                }
            )

            current_time = event_end

            if i < len(group) - 1:
                dispersal = point_to_minutes(event["chronodispersal"])
                current_time = add_minutes_to_datetime(current_time, dispersal)

        event_metrics = {}
        for event in group:
            event_name = event["name"]
            if event_name not in event_metrics:
                event_metrics[event_name] = {
                    "count": 0,
                    "total_coherence": 0,
                    "total_dispersal": 0,
                }

            metrics = event_metrics[event_name]
            metrics["count"] += 1
            metrics["total_coherence"] += point_to_minutes(event["chronocoherence"])

        for i, event in enumerate(group):
            if i < len(group) - 1:
                event_name = event["name"]
                if event_name in event_metrics:
                    dispersal = point_to_minutes(event["chronodispersal"])
                    event_metrics[event_name]["total_dispersal"] += dispersal

        formatted_metrics = []
        for event_name, metrics in event_metrics.items():
            count = metrics["count"]
            formatted_metrics.append(
                {
                    "name": event_name,
                    "count": count,
                    "total_coherence_minutes": int(metrics["total_coherence"]),
                    "total_dispersal_minutes": int(metrics["total_dispersal"]),
                    "mean_coherence_minutes": int(
                        metrics["total_coherence"] / count if count > 0 else 0
                    ),
                    "mean_dispersal_minutes": int(
                        metrics["total_dispersal"] / count if count > 0 else 0
                    ),
                }
            )

        dispersion_metrics = {}
        event_positions = {}

        for i, event in enumerate(group):
            event_name = event["name"]
            event_positions.setdefault(event_name, []).append(i)

        for event_name, positions in event_positions.items():
            if len(positions) > 1:
                dispersions = []
                for j in range(len(positions) - 1):
                    start_pos = positions[j]
                    end_pos = positions[j + 1]
                    dispersion_time = 0
                    for k in range(start_pos, end_pos):
                        dispersion_time += point_to_minutes(group[k]["chronocoherence"])
                        if k < len(group) - 1:
                            dispersion_time += point_to_minutes(
                                group[k]["chronodispersal"]
                            )
                    dispersions.append(dispersion_time)

                dispersion_metrics[event_name] = {
                    "mean_dispersion_minutes": int(
                        sum(dispersions) / len(dispersions) if dispersions else 0
                    ),
                    "dispersion_count": len(dispersions),
                }

        formatted_dispersion = [
            {
                "name": event_name,
                "mean_dispersion_minutes": int(metrics["mean_dispersion_minutes"]),
                "dispersion_count": metrics["dispersion_count"],
            }
            for event_name, metrics in dispersion_metrics.items()
        ]

        return {
            "name": name,
            "start_date": law_data["date"],
            "start_time": law_data["time"],
            "start_datetime": format_datetime(start_dt),
            "period": law_data["period"],
            "period_minutes": period_minutes,
            "end_datetime": format_datetime(end_dt),
            "total_duration_minutes": total_duration,
            "coherence_total_minutes": total_coherence,
            "dispersal_total_minutes": total_dispersal,
            "event_count": len(group),
            "unique_event_count": len(event_metrics),
            "simulation": simulation,
            "event_metrics": formatted_metrics,
            "dispersion_metrics": formatted_dispersion,
            "mean_coherence_all_minutes": int(
                total_coherence / len(group) if group else 0
            ),
            "mean_dispersal_all_minutes": int(
                total_dispersal / (len(group) - 1) if len(group) > 1 else 0
            ),
            "events": list(event_metrics.keys()),
        }

    def population_description(self, population: int = -1) -> Dict[str, Any]:
        """
        Get description for a population level.

        Args:
            population: Population level (-1 for max population)

        Returns:
            Population description
        """
        if population == -1:
            population = self.target_analyser.get_max_generation()

        population_laws = {}

        if population > 0:
            targets = self.target_analyser.get_targets_by_generation(population)
            for target_name in targets:
                target_laws = self.target_analyser.extract_laws_for_target(target_name)
                for law_name, law_data in target_laws.items():
                    if law_name not in population_laws:
                        population_laws[law_name] = law_data.copy()
        else:
            all_target_laws = set()
            for target in self.target_analyser.targets.values():
                all_target_laws.update(target["all_descendants_laws"])

            for law_name, law_data in self.law_analyser.laws.items():
                if law_name not in all_target_laws:
                    population_laws[law_name] = law_data.copy()

        if not population_laws:
            raise ZenithAnalyserError(f"No laws found for population {population}")

        law_descriptions = {}
        all_events = []

        for law_name, law_data in population_laws.items():
            try:
                law_desc = self.law_description_data(law_name, law_data)
                law_descriptions[law_name] = law_desc

                for event in law_desc.get("simulation", []):
                    all_events.append(
                        {
                            "law_name": law_name,
                            "event_name": event["event_name"],
                            "start_datetime": event["start"],
                            "end_datetime": event["end"],
                            "duration_minutes": int(event["duration_minutes"]),
                        }
                    )
            except ZenithAnalyserError as e:
                law_descriptions[law_name] = {"error": str(e)}

        all_events.sort(
            key=lambda x: parse_datetime(
                x["start_datetime"]["date"], x["start_datetime"]["time"]
            )
        )

        total_duration = sum(
            desc.get("total_duration_minutes", 0)
            for desc in law_descriptions.values()
            if isinstance(desc, dict) and "error" not in desc
        )

        valid_descriptions = [
            desc
            for desc in law_descriptions.values()
            if isinstance(desc, dict) and "error" not in desc
        ]

        population_stats = {
            "population_level": population,
            "total_laws": len(population_laws),
            "valid_laws": len(valid_descriptions),
            "total_events": len(all_events),
            "total_duration_minutes": total_duration,
            "average_law_duration_minutes": int(
                total_duration / len(valid_descriptions) if valid_descriptions else 0
            ),
            "start_range": all_events[0]["start_datetime"] if all_events else None,
            "end_range": all_events[-1]["end_datetime"] if all_events else None,
        }

        event_stats = {}
        for event in all_events:
            event_name = event["event_name"]
            if event_name not in event_stats:
                event_stats[event_name] = {
                    "count": 0,
                    "total_duration": 0,
                    "laws": set(),
                }

            stats = event_stats[event_name]
            stats["count"] += 1
            stats["total_duration"] += event["duration_minutes"]
            stats["laws"].add(event["law_name"])

        formatted_event_stats = []
        for event_name, stats in event_stats.items():
            formatted_event_stats.append(
                {
                    "name": event_name,
                    "count": stats["count"],
                    "total_duration_minutes": stats["total_duration"],
                    "mean_duration_minutes": int(
                        stats["total_duration"] / stats["count"]
                        if stats["count"] > 0
                        else 0
                    ),
                    "law_count": len(stats["laws"]),
                    "laws": list(stats["laws"]),
                }
            )

        return {
            "population_stats": population_stats,
            "law_descriptions": law_descriptions,
            "all_events": all_events,
            "event_statistics": formatted_event_stats,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_corpus(self) -> Dict[str, Any]:
        """
        Perform complete corpus analysis.

        Returns:
            Complete corpus analysis
        """
        ast_summary = self.parser.get_ast_summary(self.ast)

        all_laws = {}
        for law_name in self.law_analyser.get_law_names():
            try:
                all_laws[law_name] = self.law_description(law_name)
            except ZenithAnalyserError as e:
                all_laws[law_name] = {"error": str(e)}

        all_targets = {}
        for target_name in self.target_analyser.get_target_names():
            try:
                all_targets[target_name] = self.target_analyser.get_target_hierarchy(
                    target_name
                )
            except ZenithAnalyserError as e:
                all_targets[target_name] = {"error": str(e)}

        total_events = 0
        total_duration = 0

        for law_data in all_laws.values():
            if isinstance(law_data, dict) and "error" not in law_data:
                total_events += law_data.get("event_count", 0)
                total_duration += law_data.get("total_duration_minutes", 0)

        corpus_stats = {
            "total_laws": len(all_laws),
            "total_targets": len(all_targets),
            "total_events": total_events,
            "total_duration_minutes": total_duration,
            "max_nesting": ast_summary.get("max_nesting", 0),
            "analysis_timestamp": datetime.now().isoformat(),
        }

        return {
            "corpus_statistics": corpus_stats,
            "ast_summary": ast_summary,
            "laws": all_laws,
            "targets": all_targets,
            "validation": {
                "lexer": len(self.validator.validate_tokens(self.tokens)) == 0,
                "parser": len(self.parser_errors) == 0,
                "ast": len(self.validator.validate_ast(self.ast)) == 0,
            },
        }

    def export_json(self, filepath: str) -> None:
        """
        Export complete analysis to JSON file.

        Args:
            filepath: Path to output JSON file

        Raises:
            IOError: If file cannot be written
        """
        analysis = self.analyze_corpus()

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, default=str)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to write JSON file: {str(e)}") from e

    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debug information about the analysis.

        Returns:
            Debug information
        """
        return {
            "code_length": len(self.code),
            "token_count": len(self.tokens),
            "ast_size": self.validator._calculate_ast_size(self.ast),
            "law_count": len(self.law_analyser.laws),
            "target_count": len(self.target_analyser.targets),
            "parser_errors": self.parser_errors,
            "lexer_debug": self.lexer.debug_tokens(),
            "timestamp": datetime.now().isoformat(),
        }
