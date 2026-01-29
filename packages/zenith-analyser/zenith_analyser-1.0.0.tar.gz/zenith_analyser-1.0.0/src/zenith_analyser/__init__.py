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
Zenith Analyser - A comprehensive library for analyzing structured temporal laws.

Analyze and simulate temporal laws with events, chronocoherence, chronodispersal,
and hierarchical targets using the Zenith language.
"""

__version__ = "1.0.0"
__author__ = "François TUMUSAVYEYESU"
__email__ = "frasasudev@gmail.com"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2026 François TUMUSAVYEYESU"

from .analysers import LawAnalyser, TargetAnalyser, ZenithAnalyser

# Constants
from .constants import TIME_UNITS, TOKEN_TYPES, ZENITH_KEYWORDS

# Exceptions
from .exceptions import (
    ZenithAnalyserError,
    ZenithError,
    ZenithLexerError,
    ZenithParserError,
    ZenithValidationError,
)

# Core classes
from .lexer import Lexer
from .parser import Parser
from .unparser import ASTUnparser
from .utils import minutes_to_point, point_to_minutes, validate_zenith_code
from .validator import Validator

__all__ = [
    # Core classes
    "Lexer",
    "Parser",
    "LawAnalyser",
    "TargetAnalyser",
    "ZenithAnalyser",
    "ASTUnparser",
    "Validator",
    # Utility functions
    "point_to_minutes",
    "minutes_to_point",
    "validate_zenith_code",
    # Exceptions
    "ZenithError",
    "ZenithLexerError",
    "ZenithParserError",
    "ZenithAnalyserError",
    "ZenithValidationError",
    # Constants
    "TOKEN_TYPES",
    "TIME_UNITS",
    "ZENITH_KEYWORDS",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
]
