"""Output formatting for results."""

import json
from typing import Dict
from rich.console import Console
from rich.table import Table


def format_results(results: Dict[str, Dict[str, int]], format_type: str) -> str:
    """Format the counting results.
    
    Args:
        results: Dictionary of file extensions and their statistics
        format_type: Output format ('table', 'json', or 'csv')
        
    Returns:
        Formatted string
    """
    if format_type == 'json':
        return _format_json(results)
    elif format_type == 'csv':
        return _format_csv(results)
    else:
        return _format_table(results)


def _format_table(results: Dict[str, Dict[str, int]]) -> str:
    """Format results as a rich table."""
    if not results:
        return "No files found."
    
    console = Console()
    table = Table(title="Lines of Code", show_header=True, header_style="bold magenta")
    
    table.add_column("Language/Extension", style="cyan", no_wrap=True)
    table.add_column("Files", justify="right", style="green")
    table.add_column("Lines", justify="right", style="blue")
    table.add_column("Blank", justify="right", style="yellow")
    table.add_column("Comment", justify="right", style="magenta")
    table.add_column("Code", justify="right", style="bold green")
    
    # Sort by code lines (descending)
    sorted_results = sorted(results.items(), key=lambda x: x[1]['code'], reverse=True)
    
    total_files = 0
    total_lines = 0
    total_blank = 0
    total_comment = 0
    total_code = 0
    
    for ext, stats in sorted_results:
        table.add_row(
            ext,
            str(stats['files']),
            str(stats['lines']),
            str(stats['blank']),
            str(stats['comment']),
            str(stats['code'])
        )
        total_files += stats['files']
        total_lines += stats['lines']
        total_blank += stats['blank']
        total_comment += stats['comment']
        total_code += stats['code']
    
    # Add summary row
    table.add_section()
    table.add_row(
        "TOTAL",
        str(total_files),
        str(total_lines),
        str(total_blank),
        str(total_comment),
        str(total_code),
        style="bold white"
    )
    
    # Render table to string
    with console.capture() as capture:
        console.print(table)
    
    return capture.get()


def _format_json(results: Dict[str, Dict[str, int]]) -> str:
    """Format results as JSON."""
    return json.dumps(results, indent=2)


def _format_csv(results: Dict[str, Dict[str, int]]) -> str:
    """Format results as CSV."""
    lines = ["Language/Extension,Files,Lines,Blank,Comment,Code"]
    
    # Sort by code lines (descending)
    sorted_results = sorted(results.items(), key=lambda x: x[1]['code'], reverse=True)
    
    total_files = 0
    total_lines = 0
    total_blank = 0
    total_comment = 0
    total_code = 0
    
    for ext, stats in sorted_results:
        lines.append(
            f"{ext},{stats['files']},{stats['lines']},{stats['blank']},"
            f"{stats['comment']},{stats['code']}"
        )
        total_files += stats['files']
        total_lines += stats['lines']
        total_blank += stats['blank']
        total_comment += stats['comment']
        total_code += stats['code']
    
    # Add total row
    lines.append(
        f"TOTAL,{total_files},{total_lines},{total_blank},{total_comment},{total_code}"
    )
    
    return "\n".join(lines)
