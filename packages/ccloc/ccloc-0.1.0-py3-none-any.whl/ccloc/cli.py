"""CLI interface for the ccloc tool."""

import click
from pathlib import Path
from ccloc.counter import count_lines
from ccloc.formatter import format_results


@click.command()
@click.argument(
    'path',
    type=click.Path(exists=True, path_type=Path),
    default='.',
)
@click.option(
    '--extensions', '-e',
    multiple=True,
    help='File extensions to include (e.g., -e .py -e .js). If not specified, all files are included.',
)
@click.option(
    '--exclude', '-x',
    multiple=True,
    help='Directories or files to exclude (e.g., -x node_modules -x .git)',
)
@click.option(
    '--format', '-f',
    type=click.Choice(['table', 'json', 'csv']),
    default='table',
    help='Output format (default: table)',
)
@click.option(
    '--recursive/--no-recursive',
    default=True,
    help='Recursively scan subdirectories (default: enabled)',
)
def cli(path: Path, extensions: tuple, exclude: tuple, format: str, recursive: bool) -> None:
    """Count lines of code in a directory or file.
    
    PATH: Directory or file to analyze (default: current directory)
    
    Examples:
    
        ccloc .
        
        ccloc /path/to/project
        
        ccloc --extensions .py --extensions .js
        
        ccloc -e .py -e .js -x node_modules -x .venv
        
        ccloc --no-recursive
    """
    # Convert extensions to a set for faster lookup
    extensions_set = set(extensions) if extensions else None
    exclude_set = set(exclude) if exclude else {'__pycache__', '.git', '.venv', 'node_modules'}
    
    # Count lines
    results = count_lines(path, extensions_set, exclude_set, recursive)
    
    # Format and display results
    output = format_results(results, format)
    click.echo(output)
