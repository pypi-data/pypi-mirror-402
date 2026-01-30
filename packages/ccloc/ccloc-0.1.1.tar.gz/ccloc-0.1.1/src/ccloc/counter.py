"""Line counting logic."""

from pathlib import Path
from typing import Dict, Set, Optional
from collections import defaultdict


def count_lines(
    path: Path,
    extensions: Optional[Set[str]] = None,
    exclude: Optional[Set[str]] = None,
    recursive: bool = True
) -> Dict[str, Dict[str, int]]:
    """Count lines of code in files.
    
    Args:
        path: Path to file or directory to analyze
        extensions: Set of file extensions to include (e.g., {'.py', '.js'})
        exclude: Set of directory/file names to exclude
        recursive: Whether to scan subdirectories recursively (default: True)
        
    Returns:
        Dictionary mapping file extensions to statistics:
        {
            '.py': {'files': 5, 'lines': 1234, 'blank': 123, 'code': 1000, 'comment': 111},
            '.js': {'files': 3, 'lines': 567, 'blank': 45, 'code': 456, 'comment': 66}
        }
    """
    if exclude is None:
        exclude = set()
    
    results = defaultdict(lambda: {'files': 0, 'lines': 0, 'blank': 0, 'code': 0, 'comment': 0})
    
    if path.is_file():
        _count_file(path, extensions, results)
    else:
        _count_directory(path, extensions, exclude, results, recursive)
    
    return dict(results)


def _count_directory(
    directory: Path,
    extensions: Optional[Set[str]],
    exclude: Set[str],
    results: Dict,
    recursive: bool = True
) -> None:
    """Count lines in a directory (optionally recursive)."""
    # Use rglob for recursive, glob for non-recursive
    pattern = '**/*' if recursive else '*'
    
    for item in directory.glob(pattern):
        # Skip excluded directories and files
        if any(part in exclude for part in item.parts):
            continue
            
        if item.is_file():
            _count_file(item, extensions, results)


def _count_file(
    file_path: Path,
    extensions: Optional[Set[str]],
    results: Dict
) -> None:
    """Count lines in a single file."""
    # Get file extension
    ext = file_path.suffix if file_path.suffix else 'no_extension'
    
    # Skip if extensions filter is set and this file doesn't match
    if extensions and ext not in extensions:
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if line.strip() == '')
        comment_lines = _count_comments(lines, ext)
        code_lines = total_lines - blank_lines - comment_lines
        
        results[ext]['files'] += 1
        results[ext]['lines'] += total_lines
        results[ext]['blank'] += blank_lines
        results[ext]['comment'] += comment_lines
        results[ext]['code'] += code_lines
        
    except (UnicodeDecodeError, PermissionError, OSError):
        # Skip files that can't be read
        pass


def _count_comments(lines: list, extension: str) -> int:
    """Count comment lines based on file extension.
    
    This is a simplified comment counter that handles common cases.
    """
    comment_count = 0
    in_block_comment = False
    
    # Define comment patterns for different languages
    single_line_patterns = {
        '.py': '#',
        '.js': '//',
        '.ts': '//',
        '.java': '//',
        '.c': '//',
        '.cpp': '//',
        '.cs': '//',
        '.go': '//',
        '.rs': '//',
        '.php': '//',
        '.rb': '#',
        '.sh': '#',
        '.yaml': '#',
        '.yml': '#',
    }
    
    block_comment_patterns = {
        '.py': ('"""', '"""', "'''", "'''"),
        '.js': ('/*', '*/'),
        '.ts': ('/*', '*/'),
        '.java': ('/*', '*/'),
        '.c': ('/*', '*/'),
        '.cpp': ('/*', '*/'),
        '.cs': ('/*', '*/'),
        '.go': ('/*', '*/'),
        '.rs': ('/*', '*/'),
        '.php': ('/*', '*/'),
    }
    
    single_pattern = single_line_patterns.get(extension)
    block_patterns = block_comment_patterns.get(extension)
    
    for line in lines:
        stripped = line.strip()
        
        # Check for single-line comments
        if single_pattern and stripped.startswith(single_pattern):
            comment_count += 1
            continue
        
        # Check for block comments
        if block_patterns:
            if extension == '.py':
                # Python docstrings
                if '"""' in stripped or "'''" in stripped:
                    if in_block_comment:
                        comment_count += 1
                        if '"""' in stripped or "'''" in stripped:
                            in_block_comment = False
                    else:
                        comment_count += 1
                        # Check if it's a single-line docstring
                        quote_count = stripped.count('"""') + stripped.count("'''")
                        if quote_count < 2:
                            in_block_comment = True
                elif in_block_comment:
                    comment_count += 1
            else:
                # C-style block comments
                if '/*' in stripped:
                    in_block_comment = True
                    comment_count += 1
                    if '*/' in stripped:
                        in_block_comment = False
                elif '*/' in stripped:
                    comment_count += 1
                    in_block_comment = False
                elif in_block_comment:
                    comment_count += 1
    
    return comment_count
