# File Compass

Semantic file search for AI workstations using HNSW vector indexing and local embeddings.

[![Tests](https://img.shields.io/badge/tests-298%20passed-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## Features

- **Semantic Search**: Find files by describing what you're looking for, not just keywords
- **Quick Search**: Instant filename and symbol search (no embedding required)
- **Multi-Language AST Parsing**: Tree-sitter support for Python, JavaScript, TypeScript, Rust, Go
- **Result Explanations**: Understand why each result matched your query
- **Local Embeddings**: Uses Ollama with nomic-embed-text (no API keys needed)
- **Fast Search**: HNSW indexing for sub-second queries across thousands of files
- **Git-Aware**: Optionally filter to only git-tracked files
- **MCP Server**: Integrates with Claude Code and other MCP clients
- **Security Hardened**: Input validation, path traversal protection, sanitized errors

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) with `nomic-embed-text` model

## Installation

```bash
# Clone the repository
git clone https://github.com/mikeyfrilot/file-compass.git
cd file-compass

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e .

# Pull the embedding model
ollama pull nomic-embed-text
```

## Quick Start

### 1. Build the Index

```bash
# Index a directory
file-compass index -d "C:/Projects"

# Index multiple directories
file-compass index -d "C:/Projects" "D:/Code"
```

### 2. Search Files

```bash
# Semantic search
file-compass search "database connection handling"

# Filter by file type
file-compass search "training loop" --types python

# Git-tracked files only
file-compass search "API endpoints" --git-only
```

### 3. Quick Search (No Embeddings Required)

```bash
# Search by filename or symbol name
file-compass scan -d "C:/Projects"  # Build quick index
```

### 4. Check Status

```bash
file-compass status
```

## MCP Server

File Compass includes an MCP server for integration with Claude Code and other AI assistants.

### Available Tools

| Tool | Description |
|------|-------------|
| `file_search` | Semantic search with explanations for why results matched |
| `file_preview` | Get visual code preview with syntax highlighting |
| `file_quick_search` | Fast filename/symbol search (no embedding required) |
| `file_quick_index_build` | Build the quick search index |
| `file_actions` | Perform actions: context, usages, related, history, symbols |
| `file_index_status` | Check index statistics |
| `file_index_scan` | Build or rebuild the full semantic index |

### Claude Code Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "file-compass": {
      "command": "python",
      "args": ["-m", "file_compass.gateway"],
      "cwd": "C:/path/to/file-compass"
    }
  }
}
```

## Configuration

Configuration is managed via environment variables or the `FileCompassConfig` class:

| Variable | Default | Description |
|----------|---------|-------------|
| `FILE_COMPASS_DIRECTORIES` | `F:/AI` | Comma-separated directories to index |
| `FILE_COMPASS_OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `FILE_COMPASS_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |

## How It Works

1. **Scanning**: Discovers files matching configured extensions, respecting `.gitignore`
2. **Chunking**: Splits files into semantic pieces:
   - Python/JS/TS/Rust/Go: AST-aware via tree-sitter (functions, classes, methods)
   - Markdown: Heading-based sections
   - JSON/YAML: Top-level keys
   - Other: Sliding window with overlap
3. **Embedding**: Generates 768-dim vectors via Ollama's nomic-embed-text
4. **Indexing**: Stores vectors in HNSW index, metadata in SQLite
5. **Search**: Embeds query, finds nearest neighbors, returns ranked results with explanations

## Project Structure

```
file-compass/
├── file_compass/
│   ├── __init__.py      # Package init, default paths
│   ├── config.py        # Configuration management
│   ├── embedder.py      # Ollama embedding client with retry logic
│   ├── scanner.py       # File discovery with gitignore support
│   ├── chunker.py       # Multi-language AST chunking (tree-sitter)
│   ├── indexer.py       # HNSW + SQLite index
│   ├── quick_index.py   # Fast filename/symbol search
│   ├── explainer.py     # Result explanation generation
│   ├── merkle.py        # Incremental update tracking
│   ├── gateway.py       # MCP server with security hardening
│   └── cli.py           # Command-line interface
├── tests/               # 298 tests, 91% coverage
├── pyproject.toml
├── README.md
└── LICENSE
```

## Security

File Compass includes several security measures:

- **Input Validation**: All MCP tool inputs are validated (length limits, type checks)
- **Path Traversal Protection**: Files outside allowed directories cannot be accessed
- **SQL Injection Prevention**: All database queries use parameterized statements
- **Error Sanitization**: Internal errors are not exposed to clients

## Performance

- **Index Size**: ~1KB per chunk (embedding + metadata)
- **Search Latency**: <100ms for 10K+ chunks
- **Quick Search**: <10ms for filename/symbol search
- **Embedding Speed**: ~3-4 seconds per chunk (sequential, local)

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=file_compass --cov-report=term-missing

# Type checking (optional)
mypy file_compass/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Ollama](https://ollama.com/) for local LLM inference
- [hnswlib](https://github.com/nmslib/hnswlib) for fast vector search
- [nomic-embed-text](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) for embeddings
- [tree-sitter](https://tree-sitter.github.io/) for multi-language AST parsing
