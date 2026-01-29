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
Parser for the Zenith language.

Transforms tokens into an Abstract Syntax Tree (AST).
"""

from typing import Any, Dict, List, Optional, Tuple

from .exceptions import ZenithParserError
from .utils import validate_identifier


class Parser:
    """
    Parser for the Zenith language.

    Converts tokens into an Abstract Syntax Tree (AST) that can be analyzed.
    """

    def __init__(self, tokens: List[Dict[str, Any]]):
        """
        Initialize the parser.

        Args:
            tokens: List of tokens from the lexer
        """
        self.tokens = tokens
        self.pos = 0
        self.errors = []
        self._current_line = 1
        self._current_col = 1

    def parse(self) -> Tuple[Dict[str, Any], List[str]]:
        """
        Parse tokens into an AST.

        Returns:
            Tuple of (AST, list of errors)
        """
        self.errors = []
        self.pos = 0

        try:
            ast = self._parse_corpus()
            return ast, self.errors
        except ZenithParserError as e:
            self.errors.append(str(e))
            # Return partial AST if possible
            return {"type": "error", "message": str(e)}, self.errors
        except Exception as e:
            error_msg = f"Unexpected error during parsing: {str(e)}"
            self.errors.append(error_msg)
            return {"type": "error", "message": error_msg}, self.errors

    def _parse_corpus(self) -> Dict[str, Any]:
        """
        Parse the entire corpus (top-level structure).

        Returns:
            Corpus AST node
        """
        self._skip_whitespace()

        ast = {
            "type": "corpus_textuel",
            "elements": [],
            "start_line": 1,
            "start_col": 1,
        }

        while self.pos < len(self.tokens):
            token = self._peek()

            if not token:
                break

            if token["type"] == "EOF":
                self._consume("EOF")
                break

            if token["type"] == "law":
                law_node = self._parse_law()
                ast["elements"].append(law_node)
            elif token["type"] == "target":
                target_node = self._parse_target()
                ast["elements"].append(target_node)
            else:
                self._error(
                    f"Expected 'law' or 'target', got '{token['type']}' "
                    f"({token['value']})",
                    token,
                )

            self._skip_whitespace()

        ast["end_line"] = self._current_line
        ast["end_col"] = self._current_col

        return ast

    def _parse_law(self) -> Dict[str, Any]:
        """
        Parse a law block.

        Returns:
            Law AST node
        """
        start_token = self._consume("law")
        self._skip_whitespace()

        name_token = self._consume("identifier")
        if not validate_identifier(name_token["value"]):
            self._error(f"Invalid law name: {name_token['value']}", name_token)

        self._consume("colon")
        self._skip_whitespace()

        # Parse start_date
        self._consume("start_date")
        self._consume("colon")
        self._skip_whitespace()

        date_token = self._consume("date")
        self._skip_whitespace()

        self._consume("at")
        self._skip_whitespace()

        time_token = self._consume("time")
        self._skip_whitespace()

        # Parse period
        self._consume("period")
        self._consume("colon")
        self._skip_whitespace()

        period_token = self._consume_any(["dotted_number", "number"])
        self._skip_whitespace()

        # Parse Event section
        self._consume("Event")
        self._consume("colon")
        self._skip_whitespace()

        events = []
        while self.pos < len(self.tokens):
            token = self._peek()
            if not token or token["type"] in ["GROUP", "end_law"]:
                break

            event = self._parse_event()
            events.append(event)
            self._skip_whitespace()

        # Parse GROUP section
        self._consume("GROUP")
        self._consume("colon")
        self._skip_whitespace()

        self._consume("lparen")
        self._skip_whitespace()

        group = []
        first = True

        while self.pos < len(self.tokens):
            token = self._peek()
            if not token or token["type"] == "rparen":
                break

            if not first:
                self._consume("hyphen")
                self._skip_whitespace()

            group_event = self._parse_group_event()
            group.append(group_event)
            first = False
            self._skip_whitespace()

        self._consume("rparen")
        self._skip_whitespace()

        # Parse end_law
        self._consume("end_law")
        self._skip_whitespace()

        law_node = {
            "type": "law",
            "name": name_token["value"],
            "start_line": start_token["line"],
            "start_col": start_token["col"],
            "contents": {
                "start_date": {
                    "date": date_token["value"],
                    "time": time_token["value"],
                },
                "period": period_token["value"],
                "events": events,
                "group": group,
            },
            "end_line": self._current_line,
            "end_col": self._current_col,
        }

        return law_node

    def _parse_target(self) -> Dict[str, Any]:
        """
        Parse a target block.

        Returns:
            Target AST node
        """
        start_token = self._consume("target")
        self._skip_whitespace()

        name_token = self._consume("identifier")
        if not validate_identifier(name_token["value"]):
            self._error(f"Invalid target name: {name_token['value']}", name_token)

        self._consume("colon")
        self._skip_whitespace()

        # Parse key
        self._consume("key")
        self._consume("colon")
        self._skip_whitespace()

        key_token = self._consume("string")
        key_value = self._strip_quotes(key_token["value"])
        self._skip_whitespace()

        # Parse dictionnary
        self._consume("dictionnary")
        self._consume("colon")
        self._skip_whitespace()

        dictionnary = []
        while self.pos < len(self.tokens):
            token = self._peek()
            if not token or token["type"] in ["law", "target", "end_target"]:
                break

            dict_entry = self._parse_dictionnary_entry()
            dictionnary.append(dict_entry)
            self._skip_whitespace()

        # Parse blocks (laws and targets)
        blocks = []
        while self.pos < len(self.tokens):
            token = self._peek()
            if not token or token["type"] == "end_target":
                break

            if token["type"] == "law":
                law_node = self._parse_law()
                blocks.append(law_node)
            elif token["type"] == "target":
                target_node = self._parse_target()
                blocks.append(target_node)
            else:
                self._error(
                    f"Expected 'law' or 'target' in target block, "
                    f"got '{token['type']}'",
                    token,
                )

            self._skip_whitespace()

        # Parse end_target
        self._consume("end_target")
        self._skip_whitespace()

        target_node = {
            "type": "target",
            "name": name_token["value"],
            "start_line": start_token["line"],
            "start_col": start_token["col"],
            "contents": {
                "key": key_value,
                "dictionnary": dictionnary,
                "blocks": blocks,
            },
            "end_line": self._current_line,
            "end_col": self._current_col,
        }

        return target_node

    def _parse_event(self) -> Dict[str, Any]:
        """
        Parse an event in the Event section.

        Returns:
            Event dictionary
        """
        name_token = self._consume("identifier")
        self._skip_whitespace()

        index = None
        if self._peek() and self._peek()["type"] == "lbracket":
            self._consume("lbracket")
            index_token = self._consume("identifier")
            index = index_token["value"]
            self._consume("rbracket")
            self._skip_whitespace()

        self._consume("colon")
        self._skip_whitespace()

        description_token = self._consume("string")
        description = self._strip_quotes(description_token["value"])

        return {"name": name_token["value"], "index": index, "description": description}

    def _parse_dictionnary_entry(self) -> Dict[str, Any]:
        """
        Parse a dictionnary entry.

        Returns:
            Dictionnary entry dictionary
        """
        # Same as event parsing
        return self._parse_event()

    def _parse_group_event(self) -> Dict[str, Any]:
        """
        Parse an event in the GROUP section.

        Returns:
            Group event dictionary
        """
        name_token = self._consume("identifier")
        self._skip_whitespace()

        coherence_token = self._consume_any(["dotted_number", "number"])
        self._skip_whitespace()

        self._consume("carrot")
        self._skip_whitespace()

        dispersal_token = self._consume_any(["dotted_number", "number"])

        return {
            "name": name_token["value"],
            "chronocoherence": coherence_token["value"],
            "chronodispersal": dispersal_token["value"],
        }

    def _peek(self, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Look at a token without consuming it.

        Args:
            offset: Number of tokens to look ahead

        Returns:
            Token or None if end of stream
        """
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None

    def _consume(self, expected_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Consume and return the current token.

        Args:
            expected_type: Expected token type (optional)

        Returns:
            Consumed token

        Raises:
            ZenithParserError: If token doesn't match expected type
        """
        if self.pos >= len(self.tokens):
            self._error(f"Expected {expected_type}, but reached end of file")

        token = self.tokens[self.pos]

        if expected_type and token["type"] != expected_type:
            self._error(
                f"Expected {expected_type}, got {token['type']} ({token['value']})",
                token,
            )

        self.pos += 1
        self._current_line = token.get("line", self._current_line)
        self._current_col = token.get("col", self._current_col)

        return token

    def _consume_any(self, expected_types: List[str]) -> Dict[str, Any]:
        """
        Consume a token that matches one of the expected types.

        Args:
            expected_types: List of acceptable token types

        Returns:
            Consumed token

        Raises:
            ZenithParserError: If token doesn't match any expected type
        """
        if self.pos >= len(self.tokens):
            self._error(f"Expected one of {expected_types}, but reached end of file")

        token = self.tokens[self.pos]

        if token["type"] not in expected_types:
            self._error(
                f"Expected one of {expected_types}, "
                f"got {token['type']} ({token['value']})",
                token,
            )

        self.pos += 1
        self._current_line = token.get("line", self._current_line)
        self._current_col = token.get("col", self._current_col)

        return token

    def _skip_whitespace(self) -> None:
        """
        Skip whitespace and newline tokens.
        """
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token["type"] in ["whitespace", "newline"]:
                self.pos += 1
                self._current_line = token.get("line", self._current_line)
                self._current_col = token.get("col", self._current_col)
            else:
                break

    def _strip_quotes(self, s: str) -> str:
        """
        Strip quotes from a string token.

        Args:
            s: String with quotes

        Returns:
            String without quotes
        """
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        return s

    def _error(self, message: str, token: Optional[Dict[str, Any]] = None) -> None:
        """
        Raise a parsing error.

        Args:
            message: Error message
            token: Token that caused the error

        Raises:
            ZenithParserError: Always raised
        """
        if token is None:
            token = self._peek() or {
                "line": self._current_line,
                "col": self._current_col,
                "value": "",
            }

        line = token.get("line", self._current_line)
        col = token.get("col", self._current_col)
        value = token.get("value", "")

        full_message = f"Parsing error at line {line}, column {col}"
        if value:
            full_message += f" (near '{value}')"
        full_message += f": {message}"

        raise ZenithParserError(full_message, token)

    def get_ast_summary(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of the AST.

        Args:
            ast: Abstract Syntax Tree

        Returns:
            Summary dictionary
        """
        summary = {
            "total_laws": 0,
            "total_targets": 0,
            "max_nesting": 0,
            "events_by_law": {},
            "target_hierarchy": {},
        }

        def _traverse(node: Dict[str, Any], depth: int = 0, path: List[str] = None):
            if path is None:
                path = []

            if node["type"] == "law":
                summary["total_laws"] += 1
                law_name = node["name"]
                events = node["contents"].get("events", [])
                summary["events_by_law"][law_name] = len(events)

                if depth > summary["max_nesting"]:
                    summary["max_nesting"] = depth

            elif node["type"] == "target":
                summary["total_targets"] += 1
                target_name = node["name"]
                current_path = path + [target_name]
                summary["target_hierarchy"][target_name] = {
                    "depth": depth,
                    "path": current_path.copy(),
                    "has_laws": False,
                    "has_targets": False,
                }

                # Check contents
                contents = node["contents"]
                blocks = contents.get("blocks", [])

                for block in blocks:
                    if block["type"] == "law":
                        summary["target_hierarchy"][target_name]["has_laws"] = True
                    elif block["type"] == "target":
                        summary["target_hierarchy"][target_name]["has_targets"] = True

                if depth > summary["max_nesting"]:
                    summary["max_nesting"] = depth

                # Recurse into blocks
                for block in blocks:
                    _traverse(block, depth + 1, current_path)

            elif node["type"] == "corpus_textuel":
                for element in node.get("elements", []):
                    _traverse(element, depth, path)

        _traverse(ast)
        return summary
