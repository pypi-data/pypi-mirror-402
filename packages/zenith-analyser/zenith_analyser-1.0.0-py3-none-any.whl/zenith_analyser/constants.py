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
Constants for Zenith Analyser.
"""

TOKEN_TYPES = [
    ("comma", r"^,"),
    ("colon", r"^:"),
    ("hyphen", r"^-"),
    ("equals", r"^="),
    ("carrot", r"^\^"),
    ("lparen", r"^\("),
    ("rparen", r"^\)"),
    ("lbracket", r"^\["),
    ("rbracket", r"^\]"),
    ("law", r"^law\b"),
    ("start_date", r"^start_date\b"),
    ("period", r"^period\b"),
    ("Event", r"^Event\b"),
    ("GROUP", r"^GROUP\b"),
    ("end_law", r"^end_law\b"),
    ("at", r"^at\b"),
    ("target", r"^target\b"),
    ("key", r"^key\b"),
    ("dictionnary", r"^dictionnary\b"),
    ("end_target", r"^end_target\b"),
    ("date", r"^\d{4}-\d{2}-\d{2}\b"),
    ("time", r"^\d{2}:\d{2}\b"),
    ("dotted_number", r"^\d+(\.\d+)+"),
    ("number", r"^\d+(\.\d+)?"),
    ("string", r'^"[^"]*"'),
    ("identifier", r"^\w+[\w./{}]*\w*"),
    ("newline", r"^\n"),
    ("whitespace", r"^[ \t]+"),
]

ZENITH_KEYWORDS = {
    "law",
    "start_date",
    "period",
    "Event",
    "GROUP",
    "end_law",
    "at",
    "target",
    "key",
    "dictionnary",
    "end_target",
    "EOF",
}

TIME_UNITS = {
    "minutes": 1,
    "hours": 60,
    "days": 1440,
    "months": 43200,  # 30 days
    "years": 525600,  # 365 days
}

POINT_MULTIPLIERS = [1, 60, 1440, 43200, 518400]

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"

MAX_NESTING_DEPTH = 100
MAX_TOKENS = 100000
MAX_AST_SIZE = 10000

VALID_IDENTIFIER_REGEX = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
VALID_DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"
VALID_TIME_REGEX = r"^\d{2}:\d{2}$"
VALID_POINT_REGEX = r"^\d+(\.\d+)*$"

DEFAULT_POPULATION = -1
MAX_POPULATION = 100
