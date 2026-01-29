"""Report generation for opencode analyzer."""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .data_parser import Session, Message, Part
from .analyzer import OpenCodeAnalyzer


class OpenCodeReporter:
    """Generate comprehensive reports from opencode analysis."""

    def __init__(self, analyzer: Optional[OpenCodeAnalyzer] = None):
        """Initialize reporter with optional analyzer."""
        self.analyzer = analyzer

    def generate_session_report(
        self, session: Session, output_file: Optional[Path] = None
    ) -> str:
        """Generate detailed report for a single session."""
        if not self.analyzer:
            raise ValueError("Analyzer required for session report generation")

        # Get comprehensive analysis for this session
        session_analysis = self.analyzer.analyze_sessions([session])
        tool_usage = self.analyzer.analyze_tool_usage([session])
        content_themes = self.analyzer.analyze_content_themes([session])

        report_lines = [
            f"# Session Report: {session.id}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Session Overview",
            "",
        ]

        # Basic session info
        start_time = datetime.fromtimestamp(session.start_time / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        end_time = datetime.fromtimestamp(session.end_time / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        duration_minutes = (session.end_time - session.start_time) / 60000

        session_info = [
            f"- **Start Time:** {start_time}",
            f"- **End Time:** {end_time}",
            f"- **Duration:** {duration_minutes:.1f} minutes",
            f"- **Messages:** {len(session.messages)}",
            f"- **Project:** {session.project_id or 'Unknown'}",
            f"- **Directory:** {session.directory or 'Unknown'}",
        ]

        report_lines.extend(session_info)
        report_lines.extend(["", "## Message Timeline", ""])

        # Message timeline
        for i, message in enumerate(session.messages, 1):
            msg_time = datetime.fromtimestamp(message.time_created / 1000).strftime(
                "%H:%M:%S"
            )
            report_lines.append(
                f"### Message {i} - {message.role.title()} ({msg_time})"
            )

            if message.content:
                report_lines.append(f"**Content:** {message.content}")
                report_lines.append("")

            if message.tokens:
                token_total = sum(
                    [
                        message.tokens.get("input", 0),
                        message.tokens.get("output", 0),
                        message.tokens.get("reasoning", 0),
                    ]
                )
                report_lines.append(
                    f"**Tokens:** {token_total} (Input: {message.tokens.get('input', 0)}, Output: {message.tokens.get('output', 0)}, Reasoning: {message.tokens.get('reasoning', 0)})"
                )
                report_lines.append("")

            if message.parts:
                for part in message.parts:
                    if part.type == "tool":
                        report_lines.append(f"- **Tool Call:** {part.tool}")
                        if part.state:
                            status = part.state.get("status", "unknown")
                            report_lines.append(f"  - **Status:** {status}")
                        if part.text:
                            report_lines.append(
                                f"  - **Output:** {part.text[:200]}{'...' if len(part.text) > 200 else ''}"
                            )
                        report_lines.append("")
                    elif part.type == "reasoning":
                        report_lines.append(
                            f"**Reasoning:** {part.text[:300]}{'...' if len(part.text) > 300 else ''}"
                        )
                        report_lines.append("")

        # Tool usage summary
        if tool_usage.get("tool_frequency"):
            report_lines.extend(["## Tool Usage Summary", ""])

            for tool, count in tool_usage["tool_frequency"].items():
                success_rate = tool_usage["success_rates"].get(tool, 0)
                report_lines.append(
                    f"- **{tool}:** {count} uses ({success_rate:.1%} success rate)"
                )

            report_lines.append("")

        # Content themes
        if content_themes.get("user_prompts", {}).get("top_words"):
            report_lines.extend(["## Content Themes", "", "### Top User Words", ""])

            for word_info in content_themes["user_prompts"]["top_words"][:10]:
                report_lines.append(
                    f"- {word_info['word']}: {word_info['count']} occurrences"
                )

            report_lines.append("")

        # Join all lines
        report_content = "\\n".join(report_lines)

        # Save to file if specified
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)

        return report_content

    def generate_summary_report(
        self, sessions: List[Session], output_file: Optional[Path] = None
    ) -> str:
        """Generate summary report for multiple sessions."""
        if not self.analyzer:
            raise ValueError("Analyzer required for summary report generation")

        # Get comprehensive analysis
        session_analysis = self.analyzer.analyze_sessions(sessions)
        tool_usage = self.analyzer.analyze_tool_usage(sessions)
        content_themes = self.analyzer.analyze_content_themes(sessions)
        activity_patterns = self.analyzer.analyze_activity_patterns(sessions)
        progress_analysis = self.analyzer.generate_progress_analysis(sessions)
        error_patterns = self.analyzer.get_error_patterns(sessions)

        report_lines = [
            "# Opencode Analysis Summary Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Sessions Analyzed: {len(sessions)}",
            "",
        ]

        # Executive Summary
        report_lines.extend(
            [
                "## Executive Summary",
                "",
                f"- **Total Sessions:** {session_analysis['session_overview']['total_sessions']}",
                f"- **Total Messages:** {session_analysis['session_overview']['total_messages']}",
                f"- **Average Session Duration:** {session_analysis['session_overview']['avg_duration_minutes']:.1f} minutes",
                f"- **Days Active:** {session_analysis['time_span']['days_active']:.1f}",
                f"- **Most Used Model:** {max(session_analysis['model_usage'].items(), key=lambda x: x[1])[0] if session_analysis['model_usage'] else 'N/A'}",
                "",
            ]
        )

        # Session Overview
        report_lines.extend(
            [
                "## Session Overview",
                "",
                f"### Time Period",
                f"- **From:** {session_analysis['session_overview']['earliest_session'] or 'N/A'}",
                f"- **To:** {session_analysis['session_overview']['latest_session'] or 'N/A'}",
                f"- **Active Days:** {session_analysis['time_span']['days_active']:.1f}",
                "",
            ]
        )

        # Model Usage
        if session_analysis["model_usage"]:
            report_lines.extend(["### Model Usage", ""])
            for model, count in session_analysis["model_usage"].items():
                report_lines.append(f"- **{model}:** {count} messages")
            report_lines.append("")

        # Tool Usage Analysis
        report_lines.extend(
            [
                "## Tool Usage Analysis",
                "",
                f"- **Sessions with Tools:** {tool_usage['sessions_with_tools']}",
                f"- **Average Tools per Session:** {tool_usage['avg_tools_per_session']:.1f}",
                f"- **Most Used Tool:** {tool_usage['most_used_tool'][0] if tool_usage['most_used_tool'] else 'N/A'}",
                "",
            ]
        )

        if tool_usage.get("tool_frequency"):
            report_lines.extend(["### Tool Frequency", ""])
            for tool, count in tool_usage["tool_frequency"].items():
                success_rate = tool_usage["success_rates"].get(tool, 0)
                report_lines.append(
                    f"- **{tool}:** {count} uses ({success_rate:.1%} success rate)"
                )
            report_lines.append("")

        # Activity Patterns
        report_lines.extend(
            [
                "## Activity Patterns",
                "",
                f"- **Total Active Time:** {activity_patterns['session_metrics']['total_active_time_hours']:.1f} hours",
                f"- **Average Session Length:** {activity_patterns['session_metrics']['avg_session_length_minutes']:.1f} minutes",
                f"- **Most Active Hour:** {activity_patterns['activity_patterns']['most_active_hour'][0]:02d}:00 ({activity_patterns['activity_patterns']['most_active_hour'][1]} sessions)"
                if activity_patterns["activity_patterns"]["most_active_hour"]
                else "- **Most Active Hour:** N/A",
                f"- **Most Active Day:** {activity_patterns['activity_patterns']['most_active_weekday'][0]} ({activity_patterns['activity_patterns']['most_active_weekday'][1]} sessions)"
                if activity_patterns["activity_patterns"]["most_active_weekday"]
                else "- **Most Active Day:** N/A",
                "",
            ]
        )

        # Content Themes
        if content_themes.get("user_prompts", {}).get("top_words"):
            report_lines.extend(["## Content Themes", "", "### Top User Keywords", ""])

            for word_info in content_themes["user_prompts"]["top_words"][:15]:
                report_lines.append(
                    f"{word_info['count']}. **{word_info['word']}** ({word_info['count']} occurrences)"
                )

            report_lines.append("")

        # Error Analysis
        if error_patterns.get("tool_errors"):
            report_lines.extend(
                [
                    "## Error Analysis",
                    "",
                    f"- **Error Rate:** {error_patterns['error_rate']:.1%} of sessions had errors",
                    f"- **Debugging Sessions:** {error_patterns['debugging_sessions']}",
                    "",
                    "### Tool Errors",
                    "",
                ]
            )

            for tool, count in error_patterns["tool_errors"].items():
                report_lines.append(f"- **{tool}:** {count} errors")
            report_lines.append("")

        # Progress Timeline
        if progress_analysis.get("timeline"):
            report_lines.extend(["## Progress Timeline", "", "### Key Milestones", ""])

            milestones = progress_analysis["milestones"]
            report_lines.extend(
                [
                    f"- **First Session:** {milestones['first_session']}",
                    f"- **Total Tokens Used:** {milestones['total_tokens_used']:,}",
                    f"- **Total Tools Used:** {milestones['total_tools_used']}",
                    "",
                ]
            )

            # Recent activity (last 5 sessions)
            recent_sessions = progress_analysis["timeline"][-5:]
            if recent_sessions:
                report_lines.extend(["### Recent Sessions", ""])
                for session_data in recent_sessions:
                    report_lines.append(
                        f"- **{session_data['date']}:** {session_data['session_messages']} messages, {session_data['session_tokens']} tokens"
                    )
                report_lines.append("")

        # Recommendations
        report_lines.extend(
            [
                "## Recommendations",
                "",
                "### Productivity",
                "- Peak activity occurs during "
                + (
                    f"{activity_patterns['activity_patterns']['most_active_hour'][0]:02d}:00"
                    if activity_patterns["activity_patterns"]["most_active_hour"]
                    else "unknown"
                )
                + " - consider scheduling important work during this time",
                "- Average session length is "
                + (
                    f"{activity_patterns['session_metrics']['avg_session_length_minutes']:.0f}"
                    if "avg_session_length_minutes"
                    in activity_patterns["session_metrics"]
                    else "unknown"
                )
                + " minutes",
                "",
                "### Tool Usage",
                "- Focus on tools with higher success rates for better efficiency",
                "- Consider training or documentation for frequently failed tools",
                "",
                "### Error Reduction",
                f"- Error rate is {error_patterns['error_rate']:.1%} - "
                + (
                    "good"
                    if error_patterns["error_rate"] < 0.1
                    else "consider reviewing failed operations"
                ),
                "",
                "---",
                f"*Report generated by Opencode Analyzer v0.1.0*",
            ]
        )

        # Join all lines
        report_content = "\\n".join(report_lines)

        # Save to file if specified
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)

        return report_content

    def export_json(self, data: Dict[str, Any], output_file: Path) -> None:
        """Export data as JSON."""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def export_csv(self, sessions: List[Session], output_file: Path) -> None:
        """Export session data as CSV."""
        import csv

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Session ID",
                    "Start Time",
                    "End Time",
                    "Duration (minutes)",
                    "Message Count",
                    "Project ID",
                    "Model ID",
                    "Tokens Used",
                ]
            )

            # Data rows
            for session in sessions:
                start_time = datetime.fromtimestamp(session.start_time / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                end_time = datetime.fromtimestamp(session.end_time / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                duration = (session.end_time - session.start_time) / 60000

                # Calculate tokens for this session
                session_tokens = 0
                primary_model = None

                for message in session.messages:
                    if message.tokens:
                        session_tokens += sum(
                            [
                                message.tokens.get("input", 0),
                                message.tokens.get("output", 0),
                                message.tokens.get("reasoning", 0),
                            ]
                        )
                    if message.model_id and not primary_model:
                        primary_model = message.model_id

                writer.writerow(
                    [
                        session.id,
                        start_time,
                        end_time,
                        f"{duration:.1f}",
                        len(session.messages),
                        session.project_id or "",
                        primary_model or "",
                        session_tokens,
                    ]
                )

    def generate_comparison_report(
        self,
        session_groups: Dict[str, List[Session]],
        output_file: Optional[Path] = None,
    ) -> str:
        """Generate comparison report between session groups."""
        if not self.analyzer:
            raise ValueError("Analyzer required for comparison report generation")

        report_lines = [
            "# Session Comparison Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Analyze each group
        group_analyses = {}
        for group_name, sessions in session_groups.items():
            if not sessions:
                continue

            analysis = self.analyzer.analyze_sessions(sessions)
            tool_usage = self.analyzer.analyze_tool_usage(sessions)
            activity = self.analyzer.analyze_activity_patterns(sessions)

            group_analyses[group_name] = {
                "session_count": len(sessions),
                "total_messages": analysis["session_overview"]["total_messages"],
                "avg_duration": analysis["session_overview"]["avg_duration_minutes"],
                "total_tokens": sum(
                    msg.tokens.get("input", 0)
                    + msg.tokens.get("output", 0)
                    + msg.tokens.get("reasoning", 0)
                    for session in sessions
                    for msg in session.messages
                    if msg.tokens
                ),
                "tool_usage": tool_usage,
                "activity": activity,
            }

        # Comparison table
        report_lines.extend(
            [
                "## Group Comparison",
                "",
                "| Metric | " + " | ".join(group_analyses.keys()) + " |",
                "|" + "|".join(["---"] * (len(group_analyses) + 1)) + "|",
            ]
        )

        metrics = [
            ("Sessions", "session_count"),
            ("Messages", "total_messages"),
            ("Avg Duration (min)", "avg_duration"),
            ("Total Tokens", "total_tokens"),
        ]

        for metric_name, metric_key in metrics:
            values = [
                str(
                    int(group_analyses[group][metric_key])
                    if isinstance(group_analyses[group][metric_key], float)
                    else group_analyses[group][metric_key]
                )
                for group in group_analyses
            ]
            report_lines.append(f"| {metric_name} | " + " | ".join(values) + " |")

        report_lines.append("")

        # Group-specific insights
        for group_name, analysis in group_analyses.items():
            report_lines.extend(
                [
                    f"## {group_name.title()} Details",
                    "",
                    f"- **Sessions:** {analysis['session_count']}",
                    f"- **Total Messages:** {analysis['total_messages']}",
                    f"- **Average Duration:** {analysis['avg_duration']:.1f} minutes",
                    "",
                ]
            )

            if analysis["tool_usage"].get("tool_frequency"):
                report_lines.append("### Top Tools")
                for tool, count in list(
                    analysis["tool_usage"]["tool_frequency"].items()
                )[:5]:
                    report_lines.append(f"- {tool}: {count} uses")
                report_lines.append("")

        # Join all lines
        report_content = "\\n".join(report_lines)

        # Save to file if specified
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)

        return report_content
