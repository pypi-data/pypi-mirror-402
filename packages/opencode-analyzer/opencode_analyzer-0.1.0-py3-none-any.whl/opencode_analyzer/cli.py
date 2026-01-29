"""Command-line interface for opencode analyzer."""

import click
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.text import Text

from .data_parser import OpenCodeDataParser
from .analyzer import OpenCodeAnalyzer
from .reporter import OpenCodeReporter


console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--opencode-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Path to opencode directory",
)
@click.pass_context
def cli(ctx, verbose, opencode_dir):
    """Opencode Analyzer - Analyze opencode logs and development activity."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["opencode_dir"] = opencode_dir


@cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    help="Output format",
)
@click.pass_context
def overview(ctx, output_format):
    """Show overview of all sessions."""
    if ctx.obj.get("verbose"):
        console.print("[bold blue]Loading opencode data...[/bold blue]")

    parser = OpenCodeDataParser(ctx.obj.get("opencode_dir"))
    analyzer = OpenCodeAnalyzer(parser)

    # Get basic session analysis
    sessions = parser.parse_all_sessions()
    if not sessions:
        console.print("[bold red]No sessions found![/bold red]")
        return

    analysis = analyzer.analyze_sessions(sessions)
    tool_usage = analyzer.analyze_tool_usage(sessions)

    if output_format == "json":
        result = {
            "session_analysis": analysis,
            "tool_usage": tool_usage,
            "total_sessions": len(sessions),
        }
        console.print(json.dumps(result, indent=2))
        return

    if output_format == "markdown":
        console.print(_format_overview_markdown(analysis, tool_usage, len(sessions)))
        return

    # Default: Rich table format
    _display_overview_table(analysis, tool_usage, len(sessions))


@cli.command()
@click.argument("session_id")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    help="Output format",
)
@click.pass_context
def analyze(ctx, session_id, output_format):
    """Analyze a specific session in detail."""
    if ctx.obj.get("verbose"):
        console.print(f"[bold blue]Analyzing session: {session_id}[/bold blue]")

    parser = OpenCodeDataParser(ctx.obj.get("opencode_dir"))
    session = parser.parse_session(session_id)

    if not session:
        console.print(f"[bold red]Session {session_id} not found![/bold red]")
        return

    analyzer = OpenCodeAnalyzer(parser)

    # Get detailed analysis
    session_analysis = analyzer.analyze_sessions([session])
    tool_usage = analyzer.analyze_tool_usage([session])
    content_themes = analyzer.analyze_content_themes([session])

    if output_format == "json":
        result = {
            "session": {
                "id": session.id,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "message_count": len(session.messages),
            },
            "analysis": session_analysis,
            "tool_usage": tool_usage,
            "content_themes": content_themes,
        }
        console.print(json.dumps(result, indent=2))
        return

    if output_format == "markdown":
        console.print(
            _format_session_analysis_markdown(
                session, session_analysis, tool_usage, content_themes
            )
        )
        return

    # Default: Rich display
    _display_session_analysis(session, session_analysis, tool_usage, content_themes)


@cli.command()
@click.argument("session_id")
@click.option("--pretty/--no-pretty", default=True, help="Pretty print JSON output")
@click.pass_context
def cat(ctx, session_id, pretty):
    """Output all JSON data for a session."""
    from dataclasses import asdict

    parser = OpenCodeDataParser(ctx.obj.get("opencode_dir"))
    session = parser.parse_session(session_id)

    if not session:
        console.print(f"[bold red]Session {session_id} not found![/bold red]")
        return

    # Convert session to dict for JSON serialization
    session_dict = asdict(session)

    if pretty:
        print(json.dumps(session_dict, indent=2))
    else:
        print(json.dumps(session_dict))


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=20, help="Maximum number of results")
@click.option("--session-id", help="Search within specific session")
@click.pass_context
def search(ctx, query, limit, session_id):
    """Search through all prompts and responses."""
    if ctx.obj.get("verbose"):
        console.print(f"[bold blue]Searching for: {query}[/bold blue]")

    parser = OpenCodeDataParser(ctx.obj.get("opencode_dir"))

    if session_id:
        # Search within specific session
        session = parser.parse_session(session_id)
        if not session:
            console.print(f"[bold red]Session {session_id} not found![/bold red]")
            return
        sessions = [session]
    else:
        sessions = None  # Search all

    results = parser.search_sessions(query, limit)

    if not results:
        console.print(f"[bold yellow]No results found for: {query}[/bold yellow]")
        return

    _display_search_results(results, query)


@cli.command()
@click.option(
    "--period",
    type=click.Choice(["today", "week", "month", "all"]),
    default="all",
    help="Time period for report",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    help="Output format",
)
@click.pass_context
def report(ctx, period, output_format):
    """Generate time-based reports."""
    if ctx.obj.get("verbose"):
        console.print(f"[bold blue]Generating {period} report...[/bold blue]")

    parser = OpenCodeDataParser(ctx.obj.get("opencode_dir"))
    analyzer = OpenCodeAnalyzer(parser)

    # Filter sessions by period
    all_sessions = parser.parse_all_sessions()
    if not all_sessions:
        console.print("[bold red]No sessions found![/bold red]")
        return

    filtered_sessions = _filter_sessions_by_period(all_sessions, period)

    if not filtered_sessions:
        console.print(
            f"[bold yellow]No sessions found for period: {period}[/bold yellow]"
        )
        return

    # Generate comprehensive analysis
    session_analysis = analyzer.analyze_sessions(filtered_sessions)
    tool_usage = analyzer.analyze_tool_usage(filtered_sessions)
    activity_patterns = analyzer.analyze_activity_patterns(filtered_sessions)
    progress_analysis = analyzer.generate_progress_analysis(filtered_sessions)

    if output_format == "json":
        result = {
            "period": period,
            "session_count": len(filtered_sessions),
            "session_analysis": session_analysis,
            "tool_usage": tool_usage,
            "activity_patterns": activity_patterns,
            "progress_analysis": progress_analysis,
        }
        console.print(json.dumps(result, indent=2))
        return

    if output_format == "markdown":
        console.print(
            _format_report_markdown(
                period,
                session_analysis,
                tool_usage,
                activity_patterns,
                progress_analysis,
                len(filtered_sessions),
            )
        )
        return

    # Default: Rich display
    _display_report(
        period, session_analysis, tool_usage, activity_patterns, progress_analysis
    )


@cli.command()
@click.option("--limit", "-l", default=20, help="Maximum number of sessions to list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list(ctx, limit, output_format):
    """List all sessions in reverse chronological order."""
    if ctx.obj.get("verbose"):
        console.print("[bold blue]Loading session list...[/bold blue]")

    parser = OpenCodeDataParser(ctx.obj.get("opencode_dir"))

    # Get all sessions (already sorted by start_time, newest first)
    sessions = parser.parse_all_sessions()
    if not sessions:
        console.print("[bold red]No sessions found![/bold red]")
        return

    # Apply limit
    sessions = sessions[:limit]

    if output_format == "json":
        result = []
        for session in sessions:
            result.append(
                {
                    "id": session.id,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "message_count": len(session.messages),
                    "project_id": session.project_id,
                    "directory": session.directory,
                    "duration_minutes": (session.end_time - session.start_time) / 60000
                    if session.start_time and session.end_time
                    else 0,
                }
            )
        console.print(json.dumps(result, indent=2))
        return

    if output_format == "markdown":
        console.print(_format_session_list_markdown(sessions))
        return

    # Default: Rich table format
    _display_session_list_table(sessions)


@cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def stats(ctx, output_format):
    """Show detailed statistics."""
    if ctx.obj.get("verbose"):
        console.print("[bold blue]Calculating statistics...[/bold blue]")

    parser = OpenCodeDataParser(ctx.obj.get("opencode_dir"))
    analyzer = OpenCodeAnalyzer(parser)

    # Get comprehensive analysis
    sessions = parser.parse_all_sessions()
    if not sessions:
        console.print("[bold red]No sessions found![/bold red]")
        return

    token_usage = parser.get_token_usage()
    tool_usage = analyzer.analyze_tool_usage(sessions)
    error_patterns = analyzer.get_error_patterns(sessions)
    activity_patterns = analyzer.analyze_activity_patterns(sessions)

    if output_format == "json":
        result = {
            "token_usage": token_usage,
            "tool_usage": tool_usage,
            "error_patterns": error_patterns,
            "activity_patterns": activity_patterns,
            "total_sessions": len(sessions),
        }
        console.print(json.dumps(result, indent=2))
        return

    # Default: Rich display
    _display_statistics(
        token_usage, tool_usage, error_patterns, activity_patterns, len(sessions)
    )


def _display_overview_table(analysis, tool_usage, session_count):
    """Display overview in Rich table format."""
    console.print(
        Panel(
            f"[bold green]Opencode Session Overview[/bold green]\\n{session_count} sessions analyzed"
        )
    )

    # Session overview table
    overview_table = Table(title="Session Overview")
    overview_table.add_column("Metric", style="cyan")
    overview_table.add_column("Value", style="green")

    overview_table.add_row("Total Sessions", str(session_count))
    overview_table.add_row(
        "Total Messages", str(analysis["session_overview"]["total_messages"])
    )
    overview_table.add_row(
        "Avg Messages/Session",
        f"{analysis['session_overview']['avg_messages_per_session']:.1f}",
    )
    overview_table.add_row(
        "Avg Duration (min)",
        f"{analysis['session_overview']['avg_duration_minutes']:.1f}",
    )
    overview_table.add_row("Days Active", f"{analysis['time_span']['days_active']:.1f}")

    console.print(overview_table)

    # Tool usage table
    if tool_usage.get("tool_frequency"):
        tool_table = Table(title="Tool Usage")
        tool_table.add_column("Tool", style="cyan")
        tool_table.add_column("Usage", style="green")
        tool_table.add_column("Success Rate", style="yellow")

        for tool, count in tool_usage["tool_frequency"].items():
            success_rate = tool_usage["success_rates"].get(tool, 0)
            tool_table.add_row(tool, str(count), f"{success_rate:.1%}")

        console.print(tool_table)


def _display_session_analysis(session, analysis, tool_usage, content_themes):
    """Display detailed session analysis."""
    from .utils import format_timestamp

    console.print(Panel(f"[bold green]Session Analysis: {session.id}[/bold green]"))

    # Session info
    info_table = Table(title="Session Information")
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="green")

    start_time = format_timestamp(session.start_time, "datetime")
    end_time = format_timestamp(session.end_time, "datetime")
    duration = (session.end_time - session.start_time) / 60000  # minutes

    info_table.add_row("Start Time", start_time)
    info_table.add_row("End Time", end_time)
    info_table.add_row("Duration (min)", f"{duration:.1f}")
    info_table.add_row("Messages", str(len(session.messages)))
    info_table.add_row("Project", session.project_id or "Unknown")

    console.print(info_table)

    # Tool usage if available
    if tool_usage.get("tool_frequency"):
        tool_table = Table(title="Tools Used")
        tool_table.add_column("Tool", style="cyan")
        tool_table.add_column("Count", style="green")

        for tool, count in tool_usage["tool_frequency"].items():
            tool_table.add_row(tool, str(count))

        console.print(tool_table)


def _display_search_results(results, query):
    """Display search results."""
    console.print(
        Panel(
            f"[bold green]Search Results: {query}[/bold green]\\n{len(results)} matches found"
        )
    )

    results_table = Table()
    results_table.add_column("Session ID", style="cyan")
    results_table.add_column("Type", style="green")
    results_table.add_column("Match Type", style="yellow")
    results_table.add_column("Preview", style="white")

    for result in results:
        session_id = result["session_id"][:12] + "..."
        match_type = result.get("part_type", "content")
        preview = (
            result["preview"][:50] + "..."
            if len(result["preview"]) > 50
            else result["preview"]
        )

        results_table.add_row(session_id, result["role"], match_type, preview)

    console.print(results_table)


def _display_report(
    period, session_analysis, tool_usage, activity_patterns, progress_analysis
):
    """Display comprehensive report."""
    console.print(Panel(f"[bold green]{period.title()} Report[/bold green]"))

    # Activity patterns
    activity_table = Table(title="Activity Patterns")
    activity_table.add_column("Metric", style="cyan")
    activity_table.add_column("Value", style="green")

    session_overview = session_analysis["session_overview"]
    activity_table.add_row("Total Sessions", str(session_overview["total_sessions"]))
    activity_table.add_row(
        "Avg Session Length (min)", f"{session_overview['avg_duration_minutes']:.1f}"
    )
    activity_table.add_row(
        "Total Active Time (hours)",
        f"{activity_patterns['session_metrics']['total_active_time_hours']:.1f}",
    )

    console.print(activity_table)

    # Most active periods
    most_active_hour = activity_patterns["activity_patterns"]["most_active_hour"]
    most_active_day = activity_patterns["activity_patterns"]["most_active_weekday"]

    if most_active_hour:
        console.print(
            f"[bold]Most Active Hour:[/bold] {most_active_hour[0]}:00 ({most_active_hour[1]} sessions)"
        )
    if most_active_day:
        console.print(
            f"[bold]Most Active Day:[/bold] {most_active_day[0]} ({most_active_day[1]} sessions)"
        )


def _display_statistics(
    token_usage, tool_usage, error_patterns, activity_patterns, session_count
):
    """Display detailed statistics."""
    console.print(Panel("[bold green]Detailed Statistics[/bold green]"))

    # Token usage
    token_table = Table(title="Token Usage")
    token_table.add_column("Metric", style="cyan")
    token_table.add_column("Value", style="green")

    token_table.add_row("Total Input Tokens", str(token_usage["total_input"]))
    token_table.add_row("Total Output Tokens", str(token_usage["total_output"]))
    token_table.add_row("Total Reasoning Tokens", str(token_usage["total_reasoning"]))
    token_table.add_row("Total Tokens", str(token_usage["total_tokens"]))
    token_table.add_row("Sessions Analyzed", str(token_usage["sessions_analyzed"]))

    console.print(token_table)

    # Error patterns
    if error_patterns.get("tool_errors"):
        error_table = Table(title="Tool Errors")
        error_table.add_column("Tool", style="cyan")
        error_table.add_column("Error Count", style="red")

        for tool, count in error_patterns["tool_errors"].items():
            error_table.add_row(tool, str(count))

        console.print(error_table)


def _filter_sessions_by_period(sessions, period):
    """Filter sessions by time period.

    Session timestamps are in UTC milliseconds. We compare against UTC times.
    """
    if period == "all":
        return sessions

    from datetime import timezone

    # Use UTC-aware datetime for comparison since session timestamps are UTC
    now = datetime.now(tz=timezone.utc)

    if period == "today":
        # Start of today in UTC
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_time = now - timedelta(days=7)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        return sessions

    start_timestamp = int(start_time.timestamp() * 1000)

    return [s for s in sessions if s.start_time >= start_timestamp]


def _format_overview_markdown(analysis, tool_usage, session_count):
    """Format overview as markdown."""
    lines = [
        "# Opencode Session Overview\\n",
        f"**Total Sessions:** {session_count}",
        f"**Total Messages:** {analysis['session_overview']['total_messages']}",
        f"**Average Messages per Session:** {analysis['session_overview']['avg_messages_per_session']:.1f}",
        f"**Average Duration:** {analysis['session_overview']['avg_duration_minutes']:.1f} minutes\\n",
        "## Tool Usage\\n",
    ]

    for tool, count in tool_usage.get("tool_frequency", {}).items():
        success_rate = tool_usage["success_rates"].get(tool, 0)
        lines.append(f"- **{tool}:** {count} uses ({success_rate:.1%} success rate)")

    return "\\n".join(lines)


def _format_session_analysis_markdown(session, analysis, tool_usage, content_themes):
    """Format session analysis as markdown."""
    from .utils import format_timestamp

    start_time = format_timestamp(session.start_time, "datetime")
    duration = (session.end_time - session.start_time) / 60000

    lines = [
        f"# Session Analysis: {session.id}\\n",
        f"**Start Time:** {start_time}",
        f"**Duration:** {duration:.1f} minutes",
        f"**Messages:** {len(session.messages)}",
        f"**Project:** {session.project_id or 'Unknown'}\\n",
    ]

    if tool_usage.get("tool_frequency"):
        lines.append("## Tools Used\\n")
        for tool, count in tool_usage["tool_frequency"].items():
            lines.append(f"- **{tool}:** {count}")

    return "\\n".join(lines)


def _format_report_markdown(
    period,
    session_analysis,
    tool_usage,
    activity_patterns,
    progress_analysis,
    session_count,
):
    """Format report as markdown."""
    lines = [
        f"# {period.title()} Report\\n",
        f"**Total Sessions:** {session_count}",
        f"**Average Session Length:** {session_analysis['session_overview']['avg_duration_minutes']:.1f} minutes",
        f"**Total Active Time:** {activity_patterns['session_metrics']['total_active_time_hours']:.1f} hours\\n",
    ]

    return "\\n".join(lines)


def _display_session_list_table(sessions):
    """Display session list in Rich table format."""
    console.print(
        Panel(
            f"[bold green]Session List[/bold green]\\n{len(sessions)} sessions (newest first)"
        )
    )

    # Import utils for formatting
    from .utils import format_timestamp, format_duration, truncate_text

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Session ID", style="cyan", min_width=35, no_wrap=True)
    table.add_column("Start Time", style="green", min_width=16)
    table.add_column("Duration", style="yellow", min_width=10)
    table.add_column("Messages", style="magenta", min_width=8)
    table.add_column("Project", style="blue", min_width=12)
    table.add_column("Directory", style="white", min_width=20)

    for session in sessions:
        # Show full session ID, not truncated
        session_id = session.id
        start_time = format_timestamp(session.start_time, "datetime")
        duration = format_duration(session.start_time, session.end_time)
        message_count = str(len(session.messages))
        project = session.project_id or "Unknown"
        directory = (
            truncate_text(session.directory or "N/A", 30)
            if session.directory
            else "N/A"
        )

        table.add_row(
            session_id, start_time, duration, message_count, project, directory
        )

    console.print(table)


def _format_session_list_markdown(sessions):
    """Format session list as markdown."""
    from .utils import format_timestamp, format_duration, truncate_text

    lines = [
        "# Session List\\n",
        f"**Total Sessions:** {len(sessions)} (newest first)\\n",
        "| Session ID | Start Time | Duration | Messages | Project | Directory |",
        "|------------|------------|----------|----------|---------|-----------|",
    ]

    for session in sessions:
        # Show full session ID, not truncated
        session_id = session.id
        start_time = format_timestamp(session.start_time, "datetime")
        duration = format_duration(session.start_time, session.end_time)
        message_count = str(len(session.messages))
        project = session.project_id or "Unknown"
        directory = (
            truncate_text(session.directory or "N/A", 30)
            if session.directory
            else "N/A"
        )

        # Escape markdown special characters
        project_escaped = project.replace("|", "\\|").replace("\n", " ")
        directory_escaped = directory.replace("|", "\\|").replace("\n", " ")

        lines.append(
            f"| {session_id} | {start_time} | {duration} | {message_count} | {project_escaped} | {directory_escaped} |"
        )

    return "\\n".join(lines)


def main():
    """Main entry point for the CLI."""
    cli()
