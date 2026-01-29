# Dir2Clip

A command-line tool that recursively scans a directory, formats text files into a single string, and copies them to the clipboard. Useful for quickly pasting code context into LLMs.

## Features

- **Smart Scanning**: By default, scans only the current directory. Use `-r` for recursive scanning.
- **Filters** binary files and common ignores (e.g., `.git`, `venv`, `__pycache__`).
- **Formats** output with Markdown headers (`### FILE: path/to/file`) and code blocks.
- **Truncates** output (default: 100k chars) to prevent exceeding clipboard or context limits.
- **Cross-platform** clipboard support (Linux/macOS/Windows).

## Installation

Install via pip:

```bash
pip install dir2clip
```

*Note: Linux users may need `xclip` or `xsel` installed (`sudo apt install xclip`).*

## Usage

Run `dir2clip` in your terminal:

```bash
# Scan current directory (files only)
dir2clip

# Scan with recursion (include subdirectories)
dir2clip -r

# Scan specific path recursively
dir2clip ./src -r

# Set character limit (default: 100000)
dir2clip --max-len 50000
```

### Output Format

The tool copies content in this format:

```text
### FILE: src/main.py
```
import os
...
```

### FILE: README.md
```
# Documentation
...
```
```

## Configuration

To exclude additional directories, you can modify the `IGNORE_DIRS` set in the source code or file an issue to make it configurable via args.

## License

MIT