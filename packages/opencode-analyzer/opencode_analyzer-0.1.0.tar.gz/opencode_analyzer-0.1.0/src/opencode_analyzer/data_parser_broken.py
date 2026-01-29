"""Data parser module for opencode logs and JSON storage."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from functools import lru_cache
import concurrent.futures
import threading

# Fast JSON parsing
try:
    import orjson

    def parse_json(content: str) -> dict:
        return orjson.loads(content)
except ImportError:

    def parse_json(content: str) -> dict:
        return json.loads(content)


@dataclass
class Message:
    """Represents an opencode message."""

    id: str
    session_id: str
    role: str  # 'user' or 'assistant'
    time_created: int
    time_completed: int
    parent_id: Optional[str] = None
    model_id: Optional[str] = None
    provider_id: Optional[str] = None
    tokens: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    parts: Optional[List["Part"]] = None


@dataclass
class Part:
    """Represents a message part."""

    id: str
    session_id: str
    message_id: str
    type: str  # 'text', 'reasoning', 'tool', 'step-start', 'step-finish'
    text: Optional[str] = None
    tool: Optional[str] = None
    call_id: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    time_start: Optional[int] = None
    time_end: Optional[int] = None


@dataclass
class Session:
    """Represents an opencode session."""

    id: str
    messages: List[Message]
    start_time: int
    end_time: int
    project_id: Optional[str] = None
    directory: Optional[str] = None
    title: Optional[str] = None


@dataclass
class LogEntry:
    """Represents a structured log entry."""

    timestamp: datetime
    level: str
    service: str
    session_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class OpenCodeDataParser:
    """Parser for opencode logs and JSON storage data."""

    def __init__(self, opencode_dir: Optional[Path] = None):
        """Initialize parser with opencode directory."""
        self.opencode_dir = (
            opencode_dir or Path.home() / ".local" / "share" / "opencode"
        )
        self.log_dir = self.opencode_dir / "log"
        self.storage_dir = self.opencode_dir / "storage"
        self.message_dir = self.storage_dir / "message"
        self.part_dir = self.storage_dir / "part"

    def parse_session(self, session_id: str) -> Optional[Session]:
        """Parse a single session by ID."""
        session_path = self.message_dir / session_id
        if not session_path.exists():
            return None

        # Parse all messages in session directory
        messages = []
        message_files = list(session_path.glob("*.json"))

        for message_file in message_files:
            message = self._parse_message_file(message_file)
            if message:
                # Parse associated parts
                parts = self._parse_message_parts(message.id)
                message.parts = parts
                messages.append(message)

        if not messages:
            return None

        # Sort messages by creation time
        messages.sort(key=lambda m: m.time_created)

        # Extract session metadata
        first_message = messages[0]
        last_message = messages[-1]

        # Try to get session metadata from storage
        session_metadata = self._get_session_metadata(session_id)

        return Session(
            id=session_id,
            messages=messages,
            start_time=session_metadata.get("start_time", first_message.time_created),
            end_time=session_metadata.get("end_time", last_message.time_completed),
            project_id=session_metadata.get("project_id"),
            directory=session_metadata.get("directory"),
            title=session_metadata.get("title"),
        )

def parse_all_sessions(self) -> List[Session]:
        """Parse all available sessions with parallel processing."""
        sessions = []

        if not self.message_dir.exists():
            return sessions

        session_dirs = [d for d in self.message_dir.iterdir() if d.is_dir()]
        
        # Use parallel processing for better performance
        max_workers = min(4, len(session_dirs))  # Limit to 4 workers to avoid overwhelming
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all session parsing tasks
            future_to_session = {
                executor.submit(self.parse_session, session_dir.name): session_dir.name
                for session_dir in session_dirs
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_session):
                session = future.result()
                if session:
                    sessions.append(session)

        return sorted(sessions, key=lambda s: s.start_time)

    def parse_log_file(self, log_file: Union[str, Path]) -> List[LogEntry]:
        """Parse a structured log file."""
        log_file = Path(log_file)
        entries = []

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        entry = self._parse_log_line(line)
                        if entry:
                            entries.append(entry)
        except (FileNotFoundError, PermissionError) as e:
            print(f"Warning: Could not read log file {log_file}: {e}")

        return entries

    def parse_all_logs(self) -> List[LogEntry]:
        """Parse all available log files."""
        entries = []

        if not self.log_dir.exists():
            return entries

        log_files = sorted(self.log_dir.glob("*.log"))

        for log_file in log_files:
            entries.extend(self.parse_log_file(log_file))

        return sorted(entries, key=lambda e: e.timestamp)

@lru_cache(maxsize=1000)
    def _parse_message_file_cached(
        self, file_path: str, mtime: float
    ) -> Optional[Message]:
        """Parse a single message JSON file with caching."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Clean up common JSON issues
                content = content.strip()
                # Remove trailing comma before closing brace
                content = re.sub(r",(\s*})", r"\1", content)
                # Remove trailing comma before closing bracket
                content = re.sub(r",(\s*\])", r"\1", content)

                data = parse_json(content)

            # Handle time fields - user messages might only have 'created'
            time_data = data.get("time", {})
            time_created = time_data.get("created")
            time_completed = time_data.get("completed", time_created)  # Fallback to created for user messages

            # Handle model fields - might be nested under 'model' object
            model_id = data.get("modelID")
            provider_id = data.get("providerID")

            if not model_id and "model" in data:
                model_obj = data["model"]
                model_id = model_obj.get("modelID")
                provider_id = model_obj.get("providerID")

            return Message(
                id=data["id"],
                session_id=data["sessionID"],
                role=data["role"],
                time_created=time_created,
                time_completed=time_completed,
                parent_id=data.get("parentID"),
                model_id=model_id,
                provider_id=provider_id,
                tokens=data.get("tokens"),
                content=data.get("content"),
            )
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            # Only show error for actual parsing issues, not for expected malformed files
            if "Expecting property name enclosed in double quotes" not in str(e):
                print(f"Warning: Could not parse message file {file_path}: {e}")
            return None

    def _parse_message_file(self, message_file: Path) -> Optional[Message]:
        """Parse a single message JSON file with caching."""
        try:
            # Use file path and mtime for cache key
            mtime = message_file.stat().st_mtime
            cache_key = str(message_file)
            
            return self._parse_message_file_cached(cache_key, mtime)
        except (OSError, AttributeError):
            # Fallback for filesystem issues
            return self._parse_message_file_uncached(message_file)

    def _parse_message_file_uncached(self, message_file: Path) -> Optional[Message]:
        """Parse a single message JSON file without caching."""
        try:
            with open(message_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Clean up common JSON issues
                content = content.strip()
                # Remove trailing comma before closing brace
                content = re.sub(r",(\s*})", r"\1", content)
                # Remove trailing comma before closing bracket
                content = re.sub(r",(\s*\])", r"\1", content)

                data = parse_json(content)

            # Handle time fields - user messages might only have 'created'
            time_data = data.get("time", {})
            time_created = time_data.get("created")
            time_completed = time_data.get("completed", time_created)  # Fallback to created for user messages

            # Handle model fields - might be nested under 'model' object
            model_id = data.get("modelID")
            provider_id = data.get("providerID")
            
            if not model_id and "model" in data:
                model_obj = data["model"]
                model_id = model_obj.get("modelID")
                provider_id = model_obj.get("providerID")

            return Message(
                id=data["id"],
                session_id=data["sessionID"],
                role=data["role"],
                time_created=time_created,
                time_completed=time_completed,
                parent_id=data.get("parentID"),
                model_id=model_id,
                provider_id=provider_id,
                tokens=data.get("tokens"),
                content=data.get("content"),
            )
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            # Only show error for actual parsing issues, not for expected malformed files
            if "Expecting property name enclosed in double quotes" not in str(e):
                print(f"Warning: Could not parse message file {message_file}: {e}")
            return None

    def _parse_message_file(self, message_file: Path) -> Optional[Message]:
        """Parse a single message JSON file with caching."""
        try:
            # Use file path and mtime for cache key
            mtime = message_file.stat().st_mtime
            cache_key = str(message_file)

            return self._parse_message_file_cached(cache_key, mtime)
        except (OSError, AttributeError):
            # Fallback for filesystem issues
            return self._parse_message_file_uncached(message_file)

    def _parse_message_file_uncached(self, message_file: Path) -> Optional[Message]:
        """Parse a single message JSON file without caching."""
        try:
            with open(message_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Clean up common JSON issues
                content = content.strip()
                # Remove trailing comma before closing brace
                content = re.sub(r",(\s*})", r"\1", content)
                # Remove trailing comma before closing bracket
                content = re.sub(r",(\s*\])", r"\1", content)

                data = parse_json(content)

            # Handle time fields - user messages might only have 'created'
            time_data = data.get("time", {})
            time_created = time_data.get("created")
            time_completed = time_data.get(
                "completed", time_created
            )  # Fallback to created for user messages

            # Handle model fields - might be nested under 'model' object
            model_id = data.get("modelID")
            provider_id = data.get("providerID")

            if not model_id and "model" in data:
                model_obj = data["model"]
                model_id = model_obj.get("modelID")
                provider_id = model_obj.get("providerID")

            return Message(
                id=data["id"],
                session_id=data["sessionID"],
                role=data["role"],
                time_created=time_created,
                time_completed=time_completed,
                parent_id=data.get("parentID"),
                model_id=model_id,
                provider_id=provider_id,
                tokens=data.get("tokens"),
                content=data.get("content"),
            )
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            # Only show error for actual parsing issues, not for expected malformed files
            if "Expecting property name enclosed in double quotes" not in str(e):
                print(f"Warning: Could not parse message file {message_file}: {e}")
            return None

    def _parse_message_parts(self, message_id: str) -> List[Part]:
        """Parse all parts for a given message."""
        parts = []
        part_dir = self.part_dir / message_id

        if not part_dir.exists():
            return parts

        for part_file in part_dir.glob("*.json"):
            part = self._parse_part_file(part_file, message_id)
            if part:
                parts.append(part)

        return sorted(parts, key=lambda p: p.time_start or 0)

    def _parse_part_file(self, part_file: Path, message_id: str) -> Optional[Part]:
        """Parse a single part JSON file."""
        try:
            with open(part_file, "r", encoding="utf-8") as f:
                data = parse_json(f.read())

            time_data = data.get("time", {})
            state = data.get("state", {})

            # Handle messageID field - might be 'messageID' or need to extract from filename
            part_message_id = data.get("messageID")
            if not part_message_id:
                # Fallback: extract from filename (msg_... in path)
                import os

                filename = os.path.basename(part_file.parent.name)
                if filename.startswith("msg_"):
                    part_message_id = filename

            return Part(
                id=data["id"],
                session_id=data["sessionID"],
                message_id=part_message_id or message_id,
                type=data["type"],
                text=data.get("text"),
                tool=state.get("tool"),
                call_id=data.get("callID"),
                state=state,
                time_start=time_data.get("start"),
                time_end=time_data.get("end"),
            )
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Warning: Could not parse part file {part_file}: {e}")
            return None

    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse a structured log line."""
        # Example format: INFO  2026-01-19T19:20:25 +0ms service=session.prompt step=0 sessionID=ses_...
        pattern = r"^(\w+)\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+\+(\d+)ms\s+service=([^ ]+)(.*)$"
        match = re.match(pattern, line)

        if not match:
            return None

        level, timestamp_str, duration_ms, service, details_str = match.groups()

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("T", " "))
        except ValueError:
            return None

        # Parse details
        details = {}
        if details_str:
            # Extract key=value pairs from details
            kv_pattern = r"(\w+)=([^\s]+)"
            kv_matches = re.findall(kv_pattern, details_str)
            for key, value in kv_matches:
                details[key] = value

        return LogEntry(
            timestamp=timestamp,
            level=level,
            service=service,
            session_id=details.get("sessionID"),
            details=details,
        )

    def _get_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """Get session metadata from various sources."""
        metadata = {}

        # Try to find session info from logs
        log_entries = self.parse_all_logs()
        session_logs = [e for e in log_entries if e.session_id == session_id]

        if session_logs:
            # Extract from log entries
            first_log = min(session_logs, key=lambda e: e.timestamp)
            last_log = max(session_logs, key=lambda e: e.timestamp)

            metadata["start_time"] = int(first_log.timestamp.timestamp() * 1000)
            metadata["end_time"] = int(last_log.timestamp.timestamp() * 1000)

            # Extract project info if available
            for log in session_logs:
                details = log.details or {}
                if "projectID" in details:
                    metadata["project_id"] = details["projectID"]
                if "directory" in details:
                    metadata["directory"] = details["directory"]

        return metadata

    def search_sessions(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search through sessions for specific content."""
        results = []
        sessions = self.parse_all_sessions()

        query_lower = query.lower()

        for session in sessions:
            for message in session.messages:
                # Search in content
                if message.content and query_lower in message.content.lower():
                    results.append(
                        {
                            "session_id": session.id,
                            "message_id": message.id,
                            "role": message.role,
                            "timestamp": message.time_created,
                            "match_type": "content",
                            "preview": message.content[:200] + "..."
                            if len(message.content) > 200
                            else message.content,
                        }
                    )

                # Search in parts
                if message.parts:
                    for part in message.parts:
                        if part.text and query_lower in part.text.lower():
                            results.append(
                                {
                                    "session_id": session.id,
                                    "message_id": message.id,
                                    "part_id": part.id,
                                    "part_type": part.type,
                                    "role": message.role,
                                    "timestamp": message.time_created,
                                    "match_type": "part",
                                    "preview": part.text[:200] + "..."
                                    if len(part.text) > 200
                                    else part.text,
                                }
                            )

        return results[:limit]

    def get_token_usage(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate token usage statistics."""
        sessions = (
            [self.parse_session(session_id)]
            if session_id
            else self.parse_all_sessions()
        )
        sessions = [s for s in sessions if s is not None]

        total_input = 0
        total_output = 0
        total_reasoning = 0
        model_usage = {}

        for session in sessions:
            for message in session.messages:
                if message.tokens:
                    tokens = message.tokens
                    total_input += tokens.get("input", 0)
                    total_output += tokens.get("output", 0)
                    total_reasoning += tokens.get("reasoning", 0)

                    # Track model usage
                    model = message.model_id or "unknown"
                    if model not in model_usage:
                        model_usage[model] = {"input": 0, "output": 0, "reasoning": 0}

                    model_usage[model]["input"] += tokens.get("input", 0)
                    model_usage[model]["output"] += tokens.get("output", 0)
                    model_usage[model]["reasoning"] += tokens.get("reasoning", 0)

        return {
            "total_input": total_input,
            "total_output": total_output,
            "total_reasoning": total_reasoning,
            "total_tokens": total_input + total_output + total_reasoning,
            "model_usage": model_usage,
            "sessions_analyzed": len(sessions),
        }
