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
Validation module for Zenith Analyser.
"""

import re
from datetime import datetime
from typing import Any, Dict, List

from .constants import (
    MAX_AST_SIZE,
    MAX_NESTING_DEPTH,
    MAX_TOKENS,
    ZENITH_KEYWORDS,
)
from .exceptions import ZenithLimitError
from .utils import validate_date, validate_identifier, validate_point, validate_time


class Validator:
    """
    Validator for Zenith code, tokens, and AST.
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_code(self, code: str) -> List[str]:
        """
        Validate Zenith code for syntax issues.

        Args:
            code: Zenith code to validate

        Returns:
            List of validation errors
        """
        self.errors = []

        if not code or not code.strip():
            self.errors.append("Code is empty or contains only whitespace")
            return self.errors

        # Check code length
        if len(code) > 1000000:  # 1MB limit
            self.warnings.append(
                "Code is very large, consider splitting into smaller files"
            )

        # Check line length
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            if len(line) > 1000:
                self.warnings.append(f"Line {i} is very long ({len(line)} characters)")

        # Check for common issues
        self._validate_basic_syntax(code)
        self._validate_block_structure(code)
        self._validate_keywords(code)

        return self.errors

    def validate_tokens(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """
        Validate tokens from the lexer.

        Args:
            tokens: List of tokens

        Returns:
            List of validation errors
        """
        self.errors = []

        if not tokens:
            self.errors.append("No tokens generated")
            return self.errors

        # Check token count limit
        if len(tokens) > MAX_TOKENS:
            raise ZenithLimitError("Token count", MAX_TOKENS, len(tokens))

        # Validate each token
        for i, token in enumerate(tokens):
            self._validate_token(token, i)

        return self.errors

    def validate_ast(self, ast: Dict[str, Any]) -> List[str]:
        """
        Validate AST from the parser.

        Args:
            ast: Abstract Syntax Tree

        Returns:
            List of validation errors
        """
        self.errors = []

        if not ast:
            self.errors.append("AST is empty")
            return self.errors

        # Check AST size
        ast_size = self._calculate_ast_size(ast)
        if ast_size > MAX_AST_SIZE:
            raise ZenithLimitError("AST size", MAX_AST_SIZE, ast_size)

        # Validate AST structure
        self._validate_ast_structure(ast)

        return self.errors

    def validate_law_data(self, law_data: Dict[str, Any]) -> List[str]:
        """
        Validate law data structure.

        Args:
            law_data: Law data dictionary

        Returns:
            List of validation errors
        """
        self.errors = []

        required_fields = ["name", "date", "time", "period", "dictionnary", "group"]

        for field in required_fields:
            if field not in law_data:
                self.errors.append(f"Missing required field: {field}")

        if self.errors:
            return self.errors

        # Validate individual fields
        self._validate_law_name(law_data["name"])
        self._validate_date_time(law_data["date"], law_data["time"])
        self._validate_period(law_data["period"])
        self._validate_dictionnary(law_data["dictionnary"])
        self._validate_group(law_data["group"], law_data["dictionnary"])

        return self.errors

    def _validate_basic_syntax(self, code: str):
        """Validate basic syntax issues."""
        # Check for unmatched quotes
        quote_count = code.count('"')
        if quote_count % 2 != 0:
            self.errors.append("Unmatched quotes in code")

        # Check for unclosed parentheses/brackets
        if code.count("(") != code.count(")"):
            self.errors.append("Unmatched parentheses")

        if code.count("[") != code.count("]"):
            self.errors.append("Unmatched square brackets")

        # Check for invalid characters (basic check)
        invalid_chars = re.findall(r"[^\w\s\-:\.\"\'\[\]\(\)\{\}^,=]", code)
        if invalid_chars:
            unique_chars = set(invalid_chars)
            self.warnings.append(
                f"Potentially invalid characters found: {unique_chars}"
            )

    def _validate_block_structure(self, code: str):
        """Validate block structure."""
        lines = code.split("\n")
        in_law = False
        in_target = False

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            # Check indentation
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 4 != 0 and leading_spaces != 0:
                self.warnings.append(
                    f"Line {i}: Indentation should be multiples of 4 spaces"
                )

            # Track block state
            if stripped.startswith("law "):
                in_law = True
            elif stripped == "end_law":
                in_law = False
            elif stripped.startswith("target "):
                in_target = True
            elif stripped == "end_target":
                in_target = False

            # Check for statements outside blocks
            if not in_law and not in_target:
                if ":" in stripped and not stripped.startswith(("law", "target")):
                    if not any(stripped.startswith(f"{kw}:") for kw in ZENITH_KEYWORDS):
                        self.errors.append(
                            f"Line {i}: Statement outside law or target block"
                        )

    def _validate_keywords(self, code: str):
        """Validate keyword usage."""
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            words = re.findall(r"\b\w+\b", line)
            for word in words:
                if word in ZENITH_KEYWORDS:
                    # Check if it's used as a keyword
                    #  (should be followed by colon or space+colon)
                    if not re.search(rf"\b{word}\s*[:\(]", line):
                        self.warnings.append(
                            f"Line {i}: Reserved word '{word}' used as identifier"
                        )

    def _validate_token(self, token: Dict[str, Any], index: int):
        """Validate a single token."""
        required_fields = ["type", "value", "line", "col"]

        for field in required_fields:
            if field not in token:
                self.errors.append(f"Token {index}: Missing required field '{field}'")

        if self.errors:
            return

        # Validate token type
        valid_types = [t for t in ZENITH_KEYWORDS] + [
            "comma",
            "colon",
            "hyphen",
            "equals",
            "carrot",
            "lparen",
            "rparen",
            "lbracket",
            "rbracket",
            "date",
            "time",
            "dotted_number",
            "number",
            "string",
            "identifier",
            "newline",
            "whitespace",
        ]

        if token["type"] not in valid_types:
            self.errors.append(f"Token {index}: Invalid token type '{token['type']}'")

        # Validate based on type
        value = token["value"]

        if token["type"] == "identifier":
            if not validate_identifier(value):
                self.errors.append(f"Token {index}: Invalid identifier '{value}'")

        elif token["type"] == "date":
            if not validate_date(value):
                self.errors.append(f"Token {index}: Invalid date '{value}'")

        elif token["type"] == "time":
            if not validate_time(value):
                self.errors.append(f"Token {index}: Invalid time '{value}'")

        elif token["type"] in ["dotted_number", "number"]:
            if not validate_point(value):
                self.errors.append(f"Token {index}: Invalid number format '{value}'")

    def _validate_ast_structure(self, ast: Dict[str, Any], depth: int = 0):
        """Recursively validate AST structure."""
        if depth > MAX_NESTING_DEPTH:
            raise ZenithLimitError("Nesting depth", MAX_NESTING_DEPTH, depth)

        if "type" not in ast:
            self.errors.append("AST node missing 'type' field")
            return

        node_type = ast["type"]

        if node_type == "corpus_textuel":
            if "elements" not in ast:
                self.errors.append("Corpus node missing 'elements' field")
            else:
                for element in ast["elements"]:
                    self._validate_ast_structure(element, depth + 1)

        elif node_type == "law":
            required = ["name", "contents"]
            for field in required:
                if field not in ast:
                    self.errors.append(f"Law node missing '{field}' field")

        elif node_type == "target":
            required = ["name", "contents"]
            for field in required:
                if field not in ast:
                    self.errors.append(f"Target node missing '{field}' field")

            if "contents" in ast:
                contents = ast["contents"]
                if "blocks" in contents:
                    for block in contents["blocks"]:
                        self._validate_ast_structure(block, depth + 1)
        else:
            self.errors.append(f"Unknown AST node type: '{node_type}'")

    def _calculate_ast_size(self, node: Dict[str, Any]) -> int:
        """Calculate the size of the AST."""
        size = 1

        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    size += self._calculate_ast_size(value)
                else:
                    size += 1
        elif isinstance(node, list):
            for item in node:
                size += self._calculate_ast_size(item)

        return size

    def _validate_law_name(self, name: str):
        """Validate law name."""
        if not name or not name.strip():
            self.errors.append("Law name cannot be empty")

        if not validate_identifier(name):
            self.errors.append(f"Invalid law name: '{name}'")

    def _validate_date_time(self, date_str: str, time_str: str):
        """Validate date and time."""
        if not validate_date(date_str):
            self.errors.append(f"Invalid date: '{date_str}'")

        if not validate_time(time_str):
            self.errors.append(f"Invalid time: '{time_str}'")

        # Check if date is reasonable (not too far in past/future)
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

            # Allow dates from 2000 to 2100
            if dt.year < 2000 or dt.year > 2100:
                self.warnings.append(
                    f"Date {date_str} is outside recommended range (2000-2100)"
                )
        except ValueError:
            pass  # Already caught by validation

    def _validate_period(self, period: str):
        """Validate period."""
        if not validate_point(period):
            self.errors.append(f"Invalid period format: '{period}'")

        # Check if period is reasonable (less than 10 years)
        try:
            from .utils import point_to_minutes

            minutes = point_to_minutes(period)
            if minutes > 5256000:  # 10 years in minutes
                self.warnings.append(
                    f"Period {period} is very long ({minutes} minutes)"
                )
        except Exception:
            pass

    def _validate_dictionnary(self, dictionnary: List[Dict[str, Any]]):
        """Validate dictionnary."""
        if not isinstance(dictionnary, list):
            self.errors.append("Dictionnary must be a list")
            return

        seen_names = set()

        for i, entry in enumerate(dictionnary):
            if not isinstance(entry, dict):
                self.errors.append(f"Dictionnary entry {i} must be a dictionary")
                continue

            if "name" not in entry:
                self.errors.append(f"Dictionnary entry {i} missing 'name' field")
                continue

            name = entry["name"]

            if name in seen_names:
                self.errors.append(f"Duplicate dictionnary entry name: '{name}'")
            else:
                seen_names.add(name)

            if not validate_identifier(name):
                self.errors.append(f"Invalid dictionnary entry name: '{name}'")

            if "description" not in entry:
                self.errors.append(
                    f"Dictionnary entry '{name}' missing 'description' field"
                )

    def _validate_group(
        self, group: List[Dict[str, Any]], dictionnary: List[Dict[str, Any]]
    ):
        """Validate group with reference to dictionnary."""
        if not isinstance(group, list):
            self.errors.append("Group must be a list")
            return

        if len(group) == 0:
            self.warnings.append("Group is empty")

        dictionnary_names = {entry["name"] for entry in dictionnary if "name" in entry}

        for i, event in enumerate(group):
            if not isinstance(event, dict):
                self.errors.append(f"Group event {i} must be a dictionary")
                continue

            required = ["name", "chronocoherence", "chronodispersal"]
            for field in required:
                if field not in event:
                    self.errors.append(f"Group event {i}" f" missing '{field}' field")

            if "name" in event:
                name = event["name"]
                if name not in dictionnary_names:
                    self.errors.append(
                        f"Group event " f"'{name}' not found in dictionnary"
                    )

            if "chronocoherence" in event:
                if not validate_point(event["chronocoherence"]):
                    self.errors.append(
                        f"Invalid chronocoherence in event {i}: "
                        f"'{event['chronocoherence']}'"
                    )

            if "chronodispersal" in event:
                if not validate_point(event["chronodispersal"]):
                    self.errors.append(
                        f"Invalid chronodispersal in event {i}: ,"
                        f"'{event['chronodispersal']}'"
                    )
