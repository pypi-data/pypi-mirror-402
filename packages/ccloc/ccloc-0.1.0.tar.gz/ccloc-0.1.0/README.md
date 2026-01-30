# ccloc - Count Lines of Code

A simple and fast CLI tool to count lines of code in your projects, built with Python and managed by `uv`.

## Features

- 📊 Count lines of code by file extension/language
- 🎯 Filter by specific file extensions
- 🚫 Exclude directories and files
- 📈 Beautiful table output with Rich
- 📄 Multiple output formats (table, JSON, CSV)
- ⚡ Fast and efficient
- 🎨 Automatic comment and blank line detection

## Installation

### Using uv (recommended)

```bash
uv pip install ccloc
```

### Using pip

```bash
pip install ccloc
```

### From source

```bash
git clone https://github.com/yourusername/cloc.git
cd cloc
uv sync
```

## Usage

### Basic usage

Count lines in the current directory:
```bash
ccloc
```

Count lines in a specific directory:
```bash
ccloc /path/to/project
```

### Filter by file extensions

Count only Python files:
```bash
ccloc --extensions .py
# or
ccloc -e .py
```

Count Python and JavaScript files:
```bash
ccloc -e .py -e .js -e .ts
```

### Exclude directories

Exclude specific directories (by default excludes: `.git`, `.venv`, `node_modules`, `__pycache__`):
```bash
ccloc -x build -x dist
```

### Output formats

Table format (default):
```bash
ccloc
```

JSON format:
```bash
ccloc --format json
# or
ccloc -f json
```

CSV format:
```bash
ccloc -f csv > output.csv
```

### Recursive scanning

By default, the tool recursively scans all subdirectories. You can disable this:

```bash
# Scan only top-level directory
ccloc --no-recursive

# Scan only top-level Python files
ccloc --no-recursive -e .py
```

### Combined examples

Count Python and JavaScript files, excluding tests:
```bash
ccloc -e .py -e .js -x tests -x __tests__
```

Scan only current directory without recursion:
```bash
ccloc . --no-recursive
```

Count all code in a project with JSON output:
```bash
ccloc /path/to/project -f json
```

## Output

The tool provides detailed statistics:
- **Files**: Number of files for each language/extension
- **Lines**: Total lines in files
- **Blank**: Blank lines
- **Comment**: Comment lines
- **Code**: Actual code lines (Lines - Blank - Comment)

Example output:
```
                       Lines of Code                        
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ Language/Extension ┃ Files ┃ Lines ┃ Blank ┃ Comment ┃  Code ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ .py                │     5 │  1234 │   123 │     111 │  1000 │
│ .js                │     3 │   567 │    45 │      66 │   456 │
├────────────────────┼───────┼───────┼───────┼─────────┼───────┤
│ TOTAL              │     8 │  1801 │   168 │     177 │  1456 │
└────────────────────┴───────┴───────┴───────┴─────────┴───────┘
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Setup development environment

```bash
# Clone the repository
git clone https://github.com/chuongmep/cloc.git
cd cloc

# Install dependencies
uv sync

# Run the tool in development mode
uv run ccloc
```

### Run tests

```bash
uv run pytest
```

### Build package

```bash
uv build
```

## Supported Languages

The tool automatically detects comments for:
- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`)
- C# (`.cs`)
- Go (`.go`)
- Rust (`.rs`)
- PHP (`.php`)
- Ruby (`.rb`)
- Shell scripts (`.sh`)
- YAML (`.yaml`, `.yml`)

And many more! Files with any extension can be counted.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Author

Chuong Ho - chuongpqvn@gmail.com
