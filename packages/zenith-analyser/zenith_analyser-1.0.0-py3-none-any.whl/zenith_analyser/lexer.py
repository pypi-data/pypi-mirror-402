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
Lexer for the Zenith language.

Transforms Zenith code into tokens for parsing.
"""

import re
from typing import Any, Dict, List, Optional

from .constants import TOKEN_TYPES
from .exceptions import ZenithLexerError


class Lexer:
    """
    Lexical analyzer for the Zenith language.

    Converts source code into a stream of tokens that can be parsed.
    """

    def __init__(self, input_text: str):
        """
        Initialize the lexer.

        Args:
            input_text: Source code to tokenize
        """
        self.input = input_text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        self._token_patterns = [
            (name, re.compile(pattern)) for name, pattern in TOKEN_TYPES
        ]

    def tokenise(self) -> List[Dict[str, Any]]:
        """
        Tokenize the input text.

        Returns:
            List of tokens with type, value, line, and column

        Raises:
            ZenithLexerError: If an unexpected character is encountered
        """
        self.tokens = []

        while self.pos < len(self.input):
            token = self._get_next_token()
            if token:
                self.tokens.append(token)

        # Add EOF token
        self.tokens.append(
            {
                "type": "EOF",
                "value": "",
                "line": self.line,
                "col": self.col,
            }
        )

        return self.tokens

    def _get_next_token(self) -> Optional[Dict[str, Any]]:
        """
        Get the next token from the input.

        Returns:
            Token dictionary or None for whitespace/newline

        Raises:
            ZenithLexerError: If no token pattern matches
        """
        # Skip whitespace (but track newlines)
        while self.pos < len(self.input) and self.input[self.pos] in " \t\r":
            self.pos += 1
            self.col += 1

        if self.pos >= len(self.input):
            return None

        # Handle newlines separately
        if self.input[self.pos] == "\n":
            token = {
                "type": "newline",
                "value": "\n",
                "line": self.line,
                "col": self.col,
            }
            self.pos += 1
            self.line += 1
            self.col = 1
            return token

        # Try to match each token pattern
        for token_type, pattern in self._token_patterns:
            match = pattern.match(self.input[self.pos:])
            if match:
                value = match.group(0)

                # Create token
                token = {
                    "type": token_type,
                    "value": value,
                    "line": self.line,
                    "col": self.col,
                }

                # Update position
                self.pos += len(value)
                self.col += len(value)

                # Skip whitespace tokens (they're only for parsing structure)
                if token_type == "whitespace":
                    return self._get_next_token()

                return token

        # No pattern matched
        raise ZenithLexerError(
            f"Unexpected character: '{self.input[self.pos]}'",
            line=self.line,
            column=self.col,
        )

    def peek(self, offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Look ahead at tokens without consuming them.

        Args:
            offset: Number of tokens to look ahead

        Returns:
            Token at offset or None if end of stream
        """
        if not self.tokens:
            self.tokenise()

        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

    def reset(self) -> None:
        """Reset the lexer position to the beginning."""
        self.pos = 0
        self.line = 1
        self.col = 1

    def get_tokens_without_whitespace(self) -> List[Dict[str, Any]]:
        """
        Get tokens excluding whitespace and newlines.

        Returns:
            Filtered list of tokens
        """
        if not self.tokens:
            self.tokenise()

        return [
            token
            for token in self.tokens
            if token["type"] not in ["whitespace", "newline", "EOF"]
        ]

    def debug_tokens(self) -> str:
        """
        Return a debug string of all tokens.

        Returns:
            Formatted string of tokens
        """
        if not self.tokens:
            self.tokenise()

        lines = []
        for i, token in enumerate(self.tokens):
            if token["type"] in ["whitespace", "newline"]:
                continue

            lines.append(
                f"{i:4d} {token['type']:15s} '{token['value']:10s}' "
                f"line {token['line']:3d} col {token['col']:3d}"
            )

        return "\n".join(lines)
