"""Utility functions for opencode analyzer."""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


def format_timestamp(timestamp_ms: int, format_type: str = "iso") -> str:
    """Format timestamp to human-readable string with proper UTC handling.

    Timestamps are expected to be in UTC milliseconds since epoch.
    They are converted to local time for display.
    """
    if not timestamp_ms:
        return "N/A"

    from datetime import timezone

    # Treat timestamp as UTC and convert to local time
    # timestamp_ms is milliseconds since epoch (UTC)
    utc_dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    # Convert to local timezone for display
    local_dt = utc_dt.astimezone()

    if format_type == "iso":
        return local_dt.isoformat()
    elif format_type == "date":
        return local_dt.strftime("%Y-%m-%d")
    elif format_type == "time":
        return local_dt.strftime("%H:%M:%S")
    elif format_type == "datetime":
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "relative":
        now = datetime.now(tz=timezone.utc).astimezone()
        diff = now - local_dt
        if diff.days < 0:
            return "In the future"
        elif diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    else:
        return str(local_dt)


def format_duration(start_ms: int, end_ms: int) -> str:
    """Format duration between two timestamps."""
    if not start_ms or not end_ms:
        return "N/A"

    duration_ms = end_ms - start_ms
    if duration_ms < 1000:
        return f"{duration_ms}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.1f}s"
    elif duration_ms < 3600000:
        return f"{duration_ms / 60000:.1f}m"
    else:
        hours = duration_ms // 3600000
        minutes = (duration_ms % 3600000) // 60000
        return f"{hours}h {minutes}m"


def format_number(number: Union[int, float]) -> str:
    """Format number with appropriate suffixes."""
    if isinstance(number, float):
        return f"{number:.1f}"

    if number >= 1000000:
        return f"{number / 1000000:.1f}M"
    elif number >= 1000:
        return f"{number / 1000:.1f}K"
    else:
        return str(number)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if not text or len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text, removing common words."""
    if not text:
        return []

    # Common stop words
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "can",
        "may",
        "might",
        "must",
        "shall",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
        "this",
        "that",
        "these",
        "those",
        "what",
        "which",
        "who",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
    }

    # Extract words (alphanumeric only, minimum length)
    words = re.findall(r"\b[a-zA-Z]{" + str(min_length) + ",}\b", text.lower())

    # Filter out stop words
    keywords = [word for word in words if word not in stop_words]

    return list(set(keywords))  # Remove duplicates


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile value from list of numbers."""
    if not values:
        return 0

    sorted_values = sorted(values)
    index = (percentile / 100) * (len(sorted_values) - 1)

    if index.is_integer():
        return sorted_values[int(index)]
    else:
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def safe_divide(
    numerator: Union[int, float], denominator: Union[int, float], default: float = 0
) -> float:
    """Safely divide two numbers, returning default if denominator is 0."""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ValueError):
        return default


def validate_opencode_directory(path: Path) -> bool:
    """Validate that a directory contains opencode data."""
    if not path.exists():
        return False

    # Check for expected subdirectories
    log_dir = path / "log"
    storage_dir = path / "storage"

    return log_dir.exists() and storage_dir.exists()


def get_session_summary(session) -> Dict[str, Any]:
    """Get a quick summary of a session."""
    if not session:
        return {}

    # Calculate basic metrics
    message_count = len(session.messages) if session.messages else 0
    duration_ms = (
        session.end_time - session.start_time
        if session.start_time and session.end_time
        else 0
    )

    # Count tokens
    total_tokens = 0
    tool_count = 0

    for message in session.messages:
        if message.tokens:
            total_tokens += sum(
                [
                    message.tokens.get("input", 0),
                    message.tokens.get("output", 0),
                    message.tokens.get("reasoning", 0),
                ]
            )

        if message.parts:
            tool_count += sum(1 for part in message.parts if part.type == "tool")

    return {
        "id": session.id,
        "message_count": message_count,
        "duration_minutes": duration_ms / 60000,
        "total_tokens": total_tokens,
        "tool_count": tool_count,
        "project_id": session.project_id,
        "start_time": session.start_time,
        "end_time": session.end_time,
    }


def group_by_time_period(sessions: List, period: str = "day") -> Dict[str, List]:
    """Group sessions by time period.

    Timestamps are treated as UTC and converted to local time for grouping.
    """
    if not sessions:
        return {}

    from datetime import timezone

    groups = {}

    for session in sessions:
        if not session.start_time:
            continue

        # Treat timestamp as UTC and convert to local time
        utc_dt = datetime.fromtimestamp(session.start_time / 1000, tz=timezone.utc)
        dt = utc_dt.astimezone()

        if period == "day":
            key = dt.strftime("%Y-%m-%d")
        elif period == "week":
            # Get Monday of the week
            monday = dt - timedelta(days=dt.weekday())
            key = monday.strftime("%Y-%m-%d")
        elif period == "month":
            key = dt.strftime("%Y-%m")
        elif period == "hour":
            key = dt.strftime("%Y-%m-%d %H:00")
        else:
            key = dt.strftime("%Y-%m-%d")

        if key not in groups:
            groups[key] = []
        groups[key].append(session)

    return groups


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later values overriding earlier ones."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def clean_json_string(json_str: str) -> str:
    """Clean JSON string for parsing."""
    if not json_str:
        return ""

    # Remove common problematic characters
    cleaned = json_str.strip()

    # Handle various control characters
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)

    return cleaned


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_human(path: Path) -> str:
    """Get human-readable file size."""
    if not path.exists():
        return "N/A"

    size = path.stat().st_size

    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f}GB"


def colorize_text(text: str, color: str) -> str:
    """Add ANSI color codes to text."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }

    color_code = colors.get(color, colors["white"])
    return f"{color_code}{text}{colors['reset']}"


def progress_bar(current: int, total: int, width: int = 50, char: str = "█") -> str:
    """Generate a simple text progress bar."""
    if total == 0:
        return "[" + " " * width + "]"

    filled = int(width * current / total)
    bar = char * filled + " " * (width - filled)
    return f"[{bar}] {current}/{total} ({current / total:.1%})"


def find_peaks(values: List[float], threshold: float = 0.1) -> List[int]:
    """Find peaks in a list of values."""
    if len(values) < 3:
        return []

    peaks = []
    for i in range(1, len(values) - 1):
        prev_val = values[i - 1]
        current_val = values[i]
        next_val = values[i + 1]

        # Check if this is a peak
        if (
            current_val > prev_val
            and current_val > next_val
            and current_val > threshold * max(values)
        ):
            peaks.append(i)

    return peaks


def calculate_trend(values: List[float]) -> str:
    """Calculate trend direction from list of values."""
    if len(values) < 2:
        return "insufficient_data"

    # Simple linear regression
    n = len(values)
    x = list(range(n))

    # Calculate means
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    # Calculate covariance and variance
    covariance = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    variance = sum((x[i] - x_mean) ** 2 for i in range(n))

    if variance == 0:
        return "stable"

    slope = covariance / variance

    # Determine trend based on slope
    if abs(slope) < 0.01:
        return "stable"
    elif slope > 0:
        return "increasing"
    else:
        return "decreasing"


def escape_markdown(text: str) -> str:
    """Escape markdown special characters."""
    if not text:
        return ""

    # Escape basic markdown characters
    special_chars = [
        "\\",
        "`",
        "*",
        "_",
        "{",
        "}",
        "[",
        "]",
        "(",
        ")",
        "#",
        "+",
        "-",
        ".",
        "!",
        "|",
    ]

    for char in special_chars:
        text = text.replace(char, "\\" + char)

    return text


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def can_make_call(self) -> bool:
        """Check if a call can be made."""
        now = datetime.now().timestamp()

        # Remove old calls outside time window
        self.calls = [
            call_time for call_time in self.calls if now - call_time < self.time_window
        ]

        return len(self.calls) < self.max_calls

    def record_call(self):
        """Record a call."""
        self.calls.append(datetime.now().timestamp())

    def wait_time(self) -> float:
        """Get time to wait before next call."""
        if not self.calls:
            return 0

        oldest_call = min(self.calls)
        now = datetime.now().timestamp()
        time_since_oldest = now - oldest_call

        if time_since_oldest >= self.time_window:
            return 0

        return self.time_window - time_since_oldest
