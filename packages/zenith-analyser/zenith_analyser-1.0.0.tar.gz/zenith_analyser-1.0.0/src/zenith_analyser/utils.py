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
Utility functions for Zenith Analyser.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List
import math

from .constants import DATE_FORMAT, DATETIME_FORMAT, POINT_MULTIPLIERS, TIME_FORMAT
from .exceptions import ZenithTimeError


def point_to_minutes(point: str) -> int:
    """
    Convert a Zenith point (format M.H.D.M.Y) to minutes.

    Args:
        point: Point in Zenith format (e.g., "30.0.0" for 30 days)

    Returns:
        Total number of minutes

    Raises:
        ZenithTimeError: If point format is invalid
        ValueError: If any part is negative

    Examples:
        >>> point_to_minutes("1.0")
        60
        >>> point_to_minutes("0.1.30")
        90
        >>> point_to_minutes("30.0.0")
        43200  # 30 days
    """
    if not point:
        raise ZenithTimeError("Point cannot be empty")

    # Handle negative points
    is_negative = point.startswith("-")
    if is_negative:
        point = point[1:]

    parts = point.split(".")

    # Validate parts
    for part in parts:
        if not part.isdigit():
            raise ZenithTimeError(f"Invalid point part: '{part}' in '{point}'")

    # Convert to minutes
    total_minutes = 0
    for i, part in enumerate(reversed(parts)):
        if i >= len(POINT_MULTIPLIERS):
            raise ZenithTimeError(f"Point has too many parts: '{point}'")

        value = int(part)
        if value < 0:
            raise ZenithTimeError(
                f"Point part cannot be negative: '{value}' in '{point}'"
            )

        total_minutes += value * POINT_MULTIPLIERS[i]

    # Validate reasonable duration (max 1000 years)
    max_minutes = 518400 * 100  # 1000 years
    if total_minutes > max_minutes:
        raise ZenithTimeError(
            f"Duration too large: {total_minutes} minutes "
            f"({total_minutes/518400:.1f} years). Check point format: '{point}'"
        )

    return -total_minutes if is_negative else total_minutes


def minutes_to_point(total_minutes: int | float) -> str:
    """
    Convert minutes to a Zenith point (format Y.M.D.H.M).

    Args:
        total_minutes: Total number of minutes

    Returns:
        Point in Zenith format

    Raises:
        ZenithTimeError: If total_minutes is invalid

    Examples:
        >>> minutes_to_point(60)
        '1.0'
        >>> minutes_to_point(90)
        '0.1.30'
        >>> minutes_to_point(43200)
        '30.0.0'  # 30 days
    """
    if not isinstance(total_minutes, (int, float)):
        raise ZenithTimeError(
            f"Total minutes must be a number, got {type(total_minutes)}"
        )

    if math.isnan(total_minutes) or math.isinf(total_minutes):
        raise ZenithTimeError("Total minutes cannot be NaN or infinite")

    # Handle negative values
    if total_minutes < 0:
        return "0"

    remaining_minutes = int(total_minutes)

    if remaining_minutes == 0:
        return "0"

    parts = []

    # Process from most significant to least significant
    for multiplier in reversed(POINT_MULTIPLIERS):
        count = remaining_minutes // multiplier

        # Add part if it's non-zero OR if we already have some parts
        if count == 0 and len(parts) > 0:
            parts.append(str(count))
        elif count > 0:
            parts.append(str(count))
            remaining_minutes -= count * multiplier

    # If no parts were added, return "0"
    if not parts:
        return "0"

    # Join with dots
    point = ".".join(parts)

    return point


def parse_datetime(date_str: str, time_str: str) -> datetime:
    """
    Parse date and time strings into a datetime object.

    Args:
        date_str: Date string in YYYY-MM-DD format
        time_str: Time string in HH:MM format

    Returns:
        datetime object

    Raises:
        ZenithTimeError: If date or time format is invalid
    """
    try:
        return datetime.strptime(f"{date_str} {time_str}", DATETIME_FORMAT)
    except ValueError as e:
        raise ZenithTimeError(f"Invalid date/time format: {date_str} {time_str}") from e


def format_datetime(dt: datetime) -> Dict[str, str]:
    """
    Format a datetime object into date and time strings.

    Args:
        dt: datetime object

    Returns:
        Dictionary with 'date' and 'time' keys
    """
    return {"date": dt.strftime(DATE_FORMAT), "time": dt.strftime(TIME_FORMAT)}


def calculate_duration(start: datetime, end: datetime) -> int:
    """
    Calculate duration in minutes between two datetimes.

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        Duration in minutes

    Raises:
        ZenithTimeError: If end is before start
    """
    if end < start:
        raise ZenithTimeError(f"End time {end} is before start time {start}")

    duration = end - start
    return int(duration.total_seconds() // 60)


def add_minutes_to_datetime(dt: datetime, minutes: int) -> datetime:
    """
    Add minutes to a datetime.

    Args:
        dt: datetime object
        minutes: Number of minutes to add (can be negative)

    Returns:
        New datetime object
    """
    return dt + timedelta(minutes=minutes)


def validate_identifier(identifier: str) -> bool:
    """
    Validate an identifier according to Zenith rules.

    Args:
        identifier: Identifier to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier))


def validate_date(date_str: str) -> bool:
    """
    Validate a date string.

    Args:
        date_str: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return True
    except ValueError:
        return False


def validate_time(time_str: str) -> bool:
    """
    Validate a time string.

    Args:
        time_str: Time string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(time_str, TIME_FORMAT)
        return True
    except ValueError:
        return False


def validate_point(point_str: str) -> bool:
    """
    Validate a point string.

    Args:
        point_str: Point string to validate

    Returns:
        True if valid, False otherwise
    """
    if not point_str:
        return False

    # Handle negative points
    if point_str.startswith("-"):
        point_str = point_str[1:]

    parts = point_str.split(".")

    # Check each part
    for part in parts:
        if not part.isdigit():
            return False

    # Check maximum parts (5: minutes, hours, days, months, years)
    if len(parts) > 5:
        return False

    return True


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    Flatten a nested list.

    Args:
        nested_list: Nested list to flatten

    Returns:
        Flattened list
    """
    result = []

    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)

    return result


def safe_get(dictionary: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get a value from a nested dictionary.

    Args:
        dictionary: Dictionary to search
        keys: List of keys to traverse
        default: Default value if key not found

    Returns:
        Value or default
    """
    current = dictionary

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def format_duration(minutes: int) -> str:
    """
    Format minutes into a human-readable string.

    Args:
        minutes: Duration in minutes

    Returns:
        Human-readable duration string
    """
    if minutes == 0:
        return "0 minutes"

    # Using your custom multipliers: 518400 minutes = 1 year (360 days)
    years = minutes // 518400
    months = (minutes % 518400) // 43200
    days = (minutes % 43200) // 1440
    hours = (minutes % 1440) // 60
    mins = minutes % 60

    parts = []

    if years > 0:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if mins > 0:
        parts.append(f"{mins} minute{'s' if mins > 1 else ''}")

    return ", ".join(parts)


def validate_zenith_code(code: str) -> List[str]:
    """
    Validate Zenith code for common issues.

    Args:
        code: Zenith code to validate

    Returns:
        List of validation errors
    """
    errors = []

    if not code:
        errors.append("Code is empty")
        return errors

    # Check for unclosed blocks
    law_count = code.count("law")
    end_law_count = code.count("end_law")
    target_count = code.count("target")
    end_target_count = code.count("end_target")

    if law_count != end_law_count:
        errors.append(
            f"Mismatched law blocks: {law_count} law vs {end_law_count} end_law"
        )

    if target_count != end_target_count:
        errors.append(
            f"Mismatched target blocks: {target_count} target vs "
            f"{end_target_count} end_target"
        )

    # Check for common syntax errors
    if "::" in code:
        errors.append("Double colon found (should be single colon)")

    if '""' in code:
        errors.append("Empty string found")

    # Check for missing colons after keywords
    keywords = [
        "law",
        "target",
        "start_date",
        "period",
        "Event",
        "GROUP",
        "key",
        "dictionnary",
    ]

    for keyword in keywords:
        pattern = rf"\b{keyword}\b\s*[^\s:]"
        if re.search(pattern, code):
            errors.append(f"Missing colon after '{keyword}'")

    return errors
