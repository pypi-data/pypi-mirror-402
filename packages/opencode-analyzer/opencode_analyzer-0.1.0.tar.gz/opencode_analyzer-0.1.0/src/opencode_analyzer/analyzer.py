"""Analysis engine for opencode data."""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from .data_parser import OpenCodeDataParser, Session, Message, Part, LogEntry


class OpenCodeAnalyzer:
    """Core analysis engine for opencode data."""

    def __init__(self, parser: Optional[OpenCodeDataParser] = None):
        """Initialize analyzer with optional custom parser."""
        self.parser = parser or OpenCodeDataParser()

    def analyze_sessions(
        self, sessions: Optional[List[Session]] = None
    ) -> Dict[str, Any]:
        """Analyze multiple sessions and return comprehensive insights."""
        if sessions is None:
            sessions = self.parser.parse_all_sessions()

        if not sessions:
            return {"error": "No sessions found"}

        # Basic statistics
        total_sessions = len(sessions)
        total_messages = sum(len(s.messages) for s in sessions)

        # Time analysis
        start_times = [s.start_time for s in sessions if s.start_time]
        end_times = [s.end_time for s in sessions if s.end_time]
        earliest_session = min(start_times) if start_times else None
        latest_session = max(end_times) if end_times else None

        # Duration analysis
        durations = []
        for session in sessions:
            if session.start_time and session.end_time:
                duration_ms = session.end_time - session.start_time
                durations.append(duration_ms)

        avg_duration_ms = sum(durations) / len(durations) if durations else 0

        # Model usage
        model_usage = Counter()
        for session in sessions:
            for message in session.messages:
                if message.model_id:
                    model_usage[message.model_id] += 1

        # Project analysis
        projects = Counter()
        for session in sessions:
            if session.project_id:
                projects[session.project_id] += 1

        return {
            "session_overview": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "avg_messages_per_session": total_messages / total_sessions
                if total_sessions > 0
                else 0,
                "earliest_session": datetime.fromtimestamp(
                    earliest_session / 1000
                ).isoformat()
                if earliest_session
                else None,
                "latest_session": datetime.fromtimestamp(
                    latest_session / 1000
                ).isoformat()
                if latest_session
                else None,
                "avg_duration_minutes": avg_duration_ms / 60000,
            },
            "model_usage": dict(model_usage),
            "projects": dict(projects.most_common(10)),
            "time_span": {
                "days_active": ((latest_session - earliest_session) / 1000 / 3600 / 24)
                if earliest_session and latest_session
                else 0
            },
        }

    def analyze_tool_usage(
        self, sessions: Optional[List[Session]] = None
    ) -> Dict[str, Any]:
        """Analyze tool usage patterns across sessions."""
        if sessions is None:
            sessions = self.parser.parse_all_sessions()

        tool_counts = Counter()
        tool_usage_by_session = defaultdict(list)
        tool_success_rates = defaultdict(lambda: {"success": 0, "total": 0})

        for session in sessions:
            session_tools = []

            for message in session.messages:
                if not message.parts:
                    continue

                for part in message.parts:
                    if part.type == "tool" and part.tool:
                        tool_name = part.tool
                        tool_counts[tool_name] += 1
                        session_tools.append(tool_name)

                        # Track success rates
                        if part.state:
                            tool_success_rates[tool_name]["total"] += 1
                            if part.state.get("status") == "completed":
                                tool_success_rates[tool_name]["success"] += 1

            if session_tools:
                tool_usage_by_session[session.id] = session_tools

        # Calculate success rates
        success_rates = {}
        for tool, rates in tool_success_rates.items():
            if rates["total"] > 0:
                success_rates[tool] = rates["success"] / rates["total"]

        return {
            "tool_frequency": dict(tool_counts.most_common()),
            "success_rates": success_rates,
            "sessions_with_tools": len(tool_usage_by_session),
            "avg_tools_per_session": sum(
                len(tools) for tools in tool_usage_by_session.values()
            )
            / len(tool_usage_by_session)
            if tool_usage_by_session
            else 0,
            "most_used_tool": tool_counts.most_common(1)[0] if tool_counts else None,
        }

    def analyze_content_themes(
        self, sessions: Optional[List[Session]] = None
    ) -> Dict[str, Any]:
        """Identify themes and patterns in user prompts and responses."""
        if sessions is None:
            sessions = self.parser.parse_all_sessions()

        # Collect all text content
        user_texts = []
        assistant_texts = []
        reasoning_texts = []

        for session in sessions:
            for message in session.messages:
                if message.role == "user" and message.content:
                    user_texts.append(message.content)

                if message.parts:
                    for part in message.parts:
                        if part.type == "text" and part.text:
                            if message.role == "assistant":
                                assistant_texts.append(part.text)
                        elif part.type == "reasoning" and part.text:
                            reasoning_texts.append(part.text)

        # Extract common keywords and themes
        def extract_themes(texts: List[str], top_n: int = 20) -> List[Dict[str, Any]]:
            """Extract common themes from text list."""
            all_text = " ".join(texts).lower()

            # Filter out common words and extract meaningful terms
            common_words = {
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

            # Extract words (3+ characters)
            words = re.findall(r"\b[a-zA-Z]{3,}\b", all_text)
            filtered_words = [word for word in words if word not in common_words]

            # Count frequencies
            word_counts = Counter(filtered_words)

            # Also look for bigrams (two-word phrases)
            bigrams = []
            words_list = all_text.split()
            for i in range(len(words_list) - 1):
                if len(words_list[i]) > 2 and len(words_list[i + 1]) > 2:
                    if (
                        words_list[i] not in common_words
                        and words_list[i + 1] not in common_words
                    ):
                        bigrams.append(f"{words_list[i]} {words_list[i + 1]}")

            bigram_counts = Counter(bigrams)

            return {
                "top_words": [
                    {"word": word, "count": count}
                    for word, count in word_counts.most_common(top_n)
                ],
                "top_bigrams": [
                    {"bigram": bigram, "count": count}
                    for bigram, count in bigram_counts.most_common(10)
                ],
                "total_texts": len(texts),
                "avg_text_length": sum(len(text) for text in texts) / len(texts)
                if texts
                else 0,
            }

        user_themes = extract_themes(user_texts)
        assistant_themes = extract_themes(assistant_texts)
        reasoning_themes = extract_themes(reasoning_texts)

        return {
            "user_prompts": user_themes,
            "assistant_responses": assistant_themes,
            "reasoning": reasoning_themes,
            "total_user_messages": len(user_texts),
            "total_assistant_responses": len(assistant_texts),
            "total_reasoning_blocks": len(reasoning_texts),
        }

    def analyze_activity_patterns(
        self, sessions: Optional[List[Session]] = None
    ) -> Dict[str, Any]:
        """Analyze activity patterns and productivity metrics."""
        if sessions is None:
            sessions = self.parser.parse_all_sessions()

        # Activity by hour of day
        hourly_activity = defaultdict(int)
        daily_activity = defaultdict(int)
        weekly_activity = defaultdict(int)

        # Session lengths
        session_lengths = []

        for session in sessions:
            if session.start_time and session.end_time:
                start_dt = datetime.fromtimestamp(session.start_time / 1000)
                end_dt = datetime.fromtimestamp(session.end_time / 1000)

                duration_minutes = (end_dt - start_dt).total_seconds() / 60
                session_lengths.append(duration_minutes)

                # Aggregate activity
                hour = start_dt.hour
                day = start_dt.strftime("%Y-%m-%d")
                weekday = start_dt.strftime("%A")

                hourly_activity[hour] += 1
                daily_activity[day] += 1
                weekly_activity[weekday] += 1

        # Calculate productivity metrics
        if session_lengths:
            avg_session_length = sum(session_lengths) / len(session_lengths)
            total_active_time = sum(session_lengths)
        else:
            avg_session_length = 0
            total_active_time = 0

        # Find most active periods
        most_active_hour = (
            max(hourly_activity.items(), key=lambda x: x[1])
            if hourly_activity
            else None
        )
        most_active_day = (
            max(weekly_activity.items(), key=lambda x: x[1])
            if weekly_activity
            else None
        )

        return {
            "session_metrics": {
                "total_sessions": len(sessions),
                "avg_session_length_minutes": avg_session_length,
                "total_active_time_hours": total_active_time / 60,
                "longest_session_minutes": max(session_lengths)
                if session_lengths
                else 0,
                "shortest_session_minutes": min(session_lengths)
                if session_lengths
                else 0,
            },
            "activity_patterns": {
                "by_hour": dict(sorted(hourly_activity.items())),
                "by_weekday": dict(weekly_activity),
                "most_active_hour": most_active_hour,
                "most_active_weekday": most_active_day,
            },
            "daily_activity": dict(sorted(daily_activity.items(), key=lambda x: x[0])),
            "productivity_insights": {
                "sessions_per_day": len(sessions) / len(daily_activity)
                if daily_activity
                else 0,
                "avg_messages_per_hour": sum(len(s.messages) for s in sessions)
                / len(hourly_activity)
                if hourly_activity
                else 0,
            },
        }

    def generate_progress_analysis(
        self, sessions: Optional[List[Session]] = None
    ) -> Dict[str, Any]:
        """Analyze project progress and development over time."""
        if sessions is None:
            sessions = self.parser.parse_all_sessions()

        if not sessions:
            return {"error": "No sessions found"}

        # Sort sessions by start time
        sorted_sessions = sorted(sessions, key=lambda s: s.start_time)

        # Track metrics over time
        timeline_data = []
        cumulative_tokens = 0
        cumulative_messages = 0
        cumulative_tools = 0

        for i, session in enumerate(sorted_sessions):
            session_date = datetime.fromtimestamp(session.start_time / 1000).strftime(
                "%Y-%m-%d"
            )

            # Count tokens in this session
            session_tokens = 0
            session_tools = 0

            for message in session.messages:
                if message.tokens:
                    session_tokens += sum(
                        [
                            message.tokens.get("input", 0),
                            message.tokens.get("output", 0),
                            message.tokens.get("reasoning", 0),
                        ]
                    )

                if message.parts:
                    for part in message.parts:
                        if part.type == "tool":
                            session_tools += 1

            cumulative_tokens += session_tokens
            cumulative_messages += len(session.messages)
            cumulative_tools += session_tools

            timeline_data.append(
                {
                    "date": session_date,
                    "session_count": i + 1,
                    "cumulative_tokens": cumulative_tokens,
                    "cumulative_messages": cumulative_messages,
                    "cumulative_tools": cumulative_tools,
                    "session_tokens": session_tokens,
                    "session_messages": len(session.messages),
                    "session_tools": session_tools,
                }
            )

        # Identify patterns and trends
        if len(timeline_data) >= 2:
            # Calculate trends
            early_sessions = timeline_data[: len(timeline_data) // 2]
            recent_sessions = timeline_data[len(timeline_data) // 2 :]

            avg_tokens_early = sum(s["session_tokens"] for s in early_sessions) / len(
                early_sessions
            )
            avg_tokens_recent = sum(s["session_tokens"] for s in recent_sessions) / len(
                recent_sessions
            )

            token_trend = (
                "increasing" if avg_tokens_recent > avg_tokens_early else "decreasing"
            )
        else:
            token_trend = "insufficient_data"

        return {
            "timeline": timeline_data,
            "trends": {
                "token_usage_trend": token_trend,
                "total_sessions": len(sessions),
                "date_range": {
                    "start": timeline_data[0]["date"] if timeline_data else None,
                    "end": timeline_data[-1]["date"] if timeline_data else None,
                },
            },
            "milestones": {
                "first_session": timeline_data[0]["date"] if timeline_data else None,
                "most_active_day": max(
                    timeline_data, key=lambda x: x["session_tokens"]
                )["date"]
                if timeline_data
                else None,
                "total_tokens_used": cumulative_tokens,
                "total_tools_used": cumulative_tools,
            },
        }

    def get_error_patterns(
        self, sessions: Optional[List[Session]] = None
    ) -> Dict[str, Any]:
        """Analyze error patterns and debugging activities."""
        if sessions is None:
            sessions = self.parser.parse_all_sessions()

        error_types = Counter()
        debugging_sessions = []

        # Also analyze log files for errors
        log_entries = self.parser.parse_all_logs()
        log_errors = [entry for entry in log_entries if entry.level == "ERROR"]

        for session in sessions:
            session_has_errors = False
            session_errors = []

            for message in session.messages:
                if message.parts:
                    for part in message.parts:
                        if part.type == "tool":
                            # Check for failed tool calls
                            if part.state and part.state.get("status") != "completed":
                                error_types[part.tool] += 1
                                session_has_errors = True
                                session_errors.append(
                                    {
                                        "tool": part.tool,
                                        "status": part.state.get("status"),
                                        "error": part.state.get("error"),
                                    }
                                )

            if session_has_errors:
                debugging_sessions.append(
                    {
                        "session_id": session.id,
                        "error_count": len(session_errors),
                        "errors": session_errors,
                    }
                )

        return {
            "tool_errors": dict(error_types),
            "debugging_sessions": len(debugging_sessions),
            "total_debugging_sessions": len(debugging_sessions),
            "error_rate": len(debugging_sessions) / len(sessions) if sessions else 0,
            "log_errors": {
                "total_errors": len(log_errors),
                "error_types": Counter(entry.service for entry in log_errors),
                "recent_errors": [
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "service": entry.service,
                        "details": entry.details,
                    }
                    for entry in log_errors[-10:]  # Last 10 errors
                ],
            },
        }
