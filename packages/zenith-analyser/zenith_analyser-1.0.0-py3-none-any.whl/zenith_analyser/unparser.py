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
AST Unparser for Zenith language.

Reconstructs Zenith code from an Abstract Syntax Tree (AST).
"""

from typing import Any, Dict


class ASTUnparser:
    """
    Unparser for Zenith AST.

    Converts AST back into Zenith code string.
    """

    def __init__(self, ast: Dict[str, Any]):
        """
        Initialize the unparser.

        Args:
            ast: Abstract Syntax Tree to unparse
        """
        self.ast = ast
        self.output_lines = []
        self.current_indent = 0

    def unparse(self) -> str:
        """
        Convert AST back to Zenith code.

        Returns:
            Zenith code string
        """
        self.output_lines = []
        self.current_indent = 0

        self._unparse_corpus(self.ast)

        # Ensure final newline
        if self.output_lines and not self.output_lines[-1].endswith("\n"):
            self.output_lines.append("")

        return "\n".join(self.output_lines)

    def _indent_str(self) -> str:
        """Get current indentation string."""
        return "    " * self.current_indent

    def _add_line(self, line: str) -> None:
        """Add a line with proper indentation."""
        self.output_lines.append(f"{self._indent_str()}{line}")

    def _unparse_corpus(self, corpus: Dict[str, Any]) -> None:
        """Unparse corpus (top-level)."""
        elements = corpus.get("elements", [])
        for element in elements:
            if element["type"] == "law":
                self._unparse_law(element)
            elif element["type"] == "target":
                self._unparse_target(element)

    def _unparse_target(self, target_node: Dict[str, Any]) -> None:
        """Unparse a target block."""
        # Target header
        self._add_line(f"target {target_node['name']}:")
        self.current_indent += 1

        contents = target_node.get("contents", {})

        # Key
        key = contents.get("key", "")
        self._add_line(f'key:"{key}"')

        # Dictionnary
        dictionnary = contents.get("dictionnary", [])
        if dictionnary:
            self._add_line("dictionnary:")
            self.current_indent += 1
            for entry in dictionnary:
                self._unparse_dictionnary_entry(entry)
            self.current_indent -= 1

        # Blocks (laws and targets)
        blocks = contents.get("blocks", [])
        for block in blocks:
            if block["type"] == "law":
                self._unparse_law(block)
            elif block["type"] == "target":
                self._unparse_target(block)

        # End target
        self.current_indent -= 1
        self._add_line("end_target")

    def _unparse_law(self, law_node: Dict[str, Any]) -> None:
        """Unparse a law block."""
        # Law header
        self._add_line(f"law {law_node['name']}:")
        self.current_indent += 1

        contents = law_node.get("contents", {})

        # Start date
        start_date = contents.get("start_date", {})
        date = start_date.get("date", "0000-00-00")
        time = start_date.get("time", "00:00")
        self._add_line(f"start_date:{date} at {time}")

        # Period
        period = contents.get("period", "0")
        self._add_line(f"period:{period}")

        # Event section
        events = contents.get("events", [])
        if events:
            self._add_line("Event:")
            self.current_indent += 1
            for event in events:
                self._unparse_event(event)
            self.current_indent -= 1

        # GROUP section
        group = contents.get("group", [])
        if group:
            group_parts = []
            for event in group:
                coherence = event.get("chronocoherence", "0")
                dispersal = event.get("chronodispersal", "0")
                group_parts.append(f"{event['name']} {coherence}^{dispersal}")

            group_line = f"GROUP:({' - '.join(group_parts)})"
            self._add_line(group_line)

        # End law
        self.current_indent -= 1
        self._add_line("end_law")

    def _unparse_dictionnary_entry(self, entry: Dict[str, Any]) -> None:
        """Unparse a dictionnary entry."""
        name = entry.get("name", "")
        index = entry.get("index")
        description = entry.get("description", "")

        if index:
            self._add_line(f'{name}[{index}]:"{description}"')
        else:
            self._add_line(f'{name}:"{description}"')

    def _unparse_event(self, event: Dict[str, Any]) -> None:
        """Unparse an event (same as dictionnary entry)."""
        self._unparse_dictionnary_entry(event)

    def format_code(self, code: str) -> str:
        """
        Format Zenith code with consistent indentation.

        Args:
            code: Raw Zenith code

        Returns:
            Formatted Zenith code
        """
        lines = code.split("\n")
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            if not stripped:
                formatted_lines.append("")
                continue

            # Decrease indent for end blocks
            if stripped in ["end_law", "end_target"]:
                indent_level = max(0, indent_level - 1)

            # Add line with proper indentation
            formatted_lines.append("    " * indent_level + stripped)

            # Increase indent for start blocks
            if stripped.startswith(("law ", "target ", "dictionnary:", "Event:")):
                indent_level += 1

        return "\n".join(formatted_lines)

    def validate_unparse(self) -> bool:
        """
        Validate that unparsing produces valid code.

        Returns:
            True if validation successful
        """
        try:
            unparsed = self.unparse()

            # Basic validation
            lines = unparsed.split("\n")

            # Check for basic structure
            law_count = sum(1 for line in lines if line.strip().startswith("law "))
            end_law_count = sum(1 for line in lines if line.strip() == "end_law")

            target_count = sum(
                1 for line in lines if line.strip().startswith("target ")
            )
            end_target_count = sum(1 for line in lines if line.strip() == "end_target")

            if law_count != end_law_count:
                return False

            if target_count != end_target_count:
                return False

            return True

        except Exception:
            return False

    def get_unparse_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the unparsed code.

        Returns:
            Statistics dictionary
        """
        unparsed = self.unparse()
        lines = unparsed.split("\n")

        stats = {
            "total_lines": len(lines),
            "non_empty_lines": sum(1 for line in lines if line.strip()),
            "law_count": sum(1 for line in lines if line.strip().startswith("law ")),
            "target_count": sum(
                1 for line in lines if line.strip().startswith("target ")
            ),
            "event_count": sum(
                1
                for line in lines
                if ':"' in line and not line.strip().startswith('key:"')
            ),
            "total_length": len(unparsed),
            "valid_structure": self.validate_unparse(),
        }

        return stats
