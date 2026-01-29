# Ward

MCP server for AI-powered code quality analysis. Detects security issues, bugs, code smells, and performance problems.

## Features

- **Security scanning**: SQL injection, XSS, command injection, hardcoded secrets
- **Bug detection**: Null references, off-by-one errors, race conditions
- **Code quality**: Unused variables, duplicate code, complexity violations
- **Performance**: N+1 queries, inefficient loops, memory leaks
- **Supply chain**: Dependency vulnerability scanning
- **Multi-language**: Python, JavaScript/TypeScript, Go, Java, Ruby, Rust, C/C++, and more

## Installation

### Prerequisites

```bash
# Python 3.10+
python --version

# Install the analysis engine
pip install semgrep
semgrep --version
```

### Install Ward

```bash
# Clone the repository
git clone https://github.com/nechhuu/ward-mcp.git
cd ward-mcp

# Install in editable mode
pip install -e .

# Optional: Install with all features
pip install -e ".[dev,llm,graph,analyzer]"
```

### Verify Installation

```bash
python -m ward mcp
# Server should start without errors
```

## IDE Setup

### Claude Code (CLI)

Add to your `~/.claude/mcp_servers.json`:

```json
{
  "ward": {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "ward", "mcp"]
  }
}
```

Or configure per-project in `.claude/mcp_servers.json`:

```json
{
  "ward": {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "ward", "mcp"],
    "cwd": "/path/to/ward"
  }
}
```

### Claude Desktop

Edit your `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ward": {
      "command": "python",
      "args": ["-m", "ward", "mcp"],
      "cwd": "/path/to/ward"
    }
  }
}
```

### Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json` in project root or global settings):

```json
{
  "mcpServers": {
    "ward": {
      "command": "python",
      "args": ["-m", "ward", "mcp"],
      "cwd": "/path/to/ward"
    }
  }
}
```

### VS Code + Continue.dev

Add to your Continue configuration (`~/.continue/config.json`):

```json
{
  "experimental": {
    "mcpServers": {
      "ward": {
        "transport": {
          "type": "stdio",
          "command": "python",
          "args": ["-m", "ward", "mcp"]
        }
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `scan` | Scan local files by absolute path |
| `scan_remote` | Scan code content directly (no file system access needed) |
| `scan_with_custom_rule` | Scan with custom YAML rules |
| `scan_supply_chain` | Dependency/SCA vulnerability scanning |
| `get_supported_languages` | List all supported programming languages |
| `get_abstract_syntax_tree` | Parse code and return AST in JSON format |
| `get_rule_schema` | Get JSON schema for writing rules |
| `explain_issue` | Get detailed explanation for an issue (placeholder) |
| `suggest_fix` | Get suggested fix for an issue (placeholder) |
| `analyze_cross_file` | Cross-file taint analysis (placeholder) |

## Usage

### Manual Scanning

Ask the AI to scan code in your prompt:

```
Scan this code for issues:
[your code here]
```

Or explicitly request the tool:

```
Use scan_remote to check this Python code:
import os
os.system(user_input)
```

### Automatic Scanning (Recommended)

To make AI agents automatically scan code after generating it, add instructions to your project:

**Claude Code** - Add to `CLAUDE.md` in project root:

```markdown
## Coding Rules
After generating code, use ward's scan_remote tool to check for issues.
Format: scan_remote(code_files=[{"path": "filename.py", "content": "code"}])
If issues found: fix and scan again.
```

**Cursor** - Add to `.cursorrules` in project root:

```
After generating code, use ward's scan_remote tool to check for issues.
Format: scan_remote(code_files=[{"path": "filename.py", "content": "code"}])
If issues found: fix and scan again.
```

**Other MCP clients** - Add similar instructions to your system prompt or project rules file.

### Scan Existing Files

```
Use scan to analyze /path/to/file.py with category="security"
```

### Custom Rules

```
Use scan_with_custom_rule with this rule to find print statements:

rules:
  - id: no-print
    pattern: print(...)
    message: "Remove print statement"
    languages: [python]
    severity: WARNING
```

## Analysis Categories

| Category | Description |
|----------|-------------|
| `all` | Comprehensive analysis |
| `security` | Security vulnerabilities only |
| `quality` | Language-specific code quality |
| `bugs` | Bug detection |
| `performance` | Performance issues |

## Project Structure

```
src/ward/
├── __init__.py          # Package version
├── __main__.py          # CLI entry point
├── server.py            # MCP server implementation
├── models.py            # Pydantic data models
├── scanner.py           # Analysis engine wrapper
├── services/
│   ├── llm.py           # LLM integration (placeholder)
│   ├── graph.py         # Graph analysis (placeholder)
│   └── cache.py         # Caching layer (placeholder)
├── utilities/
│   ├── utils.py         # Path validation, temp files
│   └── tracing.py       # Local logging
└── analyzer/
    ├── engine.py        # Tree-sitter analysis engine
    └── adapters/        # Language-specific adapters
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Check logs
tail -f ~/.ward/debug.log  # Unix/macOS
type %USERPROFILE%\.ward\debug.log  # Windows
```

## Troubleshooting

### Analysis Engine Not Found

```bash
pip install semgrep
semgrep --version
```

### Server Won't Start

Check the debug log:

```bash
cat ~/.ward/debug.log
```

### MCP Connection Issues

1. Verify the server starts manually: `python -m ward mcp`
2. Check your MCP config paths are absolute
3. Ensure Python is in your PATH

## License

LGPL 2.1

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Submit a pull request
