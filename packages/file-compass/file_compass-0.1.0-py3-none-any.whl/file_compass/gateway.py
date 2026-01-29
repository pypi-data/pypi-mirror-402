"""
File Compass Gateway - MCP Server for Semantic File Search

A semantic search gateway for files on your workstation.
Uses HNSW indexing with nomic-embed-text embeddings.

Usage:
    python gateway.py              # Start MCP server
    python gateway.py --index      # Build index for F:/AI
    python gateway.py --test       # Run test queries
"""

import asyncio
import argparse
import logging
import re
import subprocess
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path

# MCP imports
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("FastMCP not installed. Install with: pip install mcp", file=sys.stderr)
    raise

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_compass.indexer import FileIndex, SearchResult, get_index
from file_compass.config import get_config
from file_compass.explainer import ResultExplainer, VisualPreviewGenerator
from file_compass.quick_index import QuickIndex, get_quick_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("file-compass")

# Global state
_index: Optional[FileIndex] = None
_index_lock = asyncio.Lock()

# UX components
_explainer = ResultExplainer()
_preview_generator = VisualPreviewGenerator()


async def get_index_instance() -> FileIndex:
    """Get or initialize the file index."""
    global _index

    if _index is not None:
        return _index

    async with _index_lock:
        if _index is not None:
            return _index

        _index = FileIndex()
        # Load existing index if available
        if _index.index_path.exists():
            _index._get_index()  # Load HNSW
            _index._get_conn()   # Load SQLite

        return _index


# =============================================================================
# MCP TOOLS
# =============================================================================

@mcp.tool()
async def file_search(
    query: str,
    top_k: int = 10,
    file_types: Optional[str] = None,
    directory: Optional[str] = None,
    git_only: bool = False,
    min_relevance: float = 0.3,
    explain: bool = True
) -> Dict[str, Any]:
    """
    Search for files using semantic search.

    Finds files and code chunks that match your query conceptually,
    not just by keywords. Great for finding:
    - Code that implements specific functionality
    - Files related to a topic or concept
    - Functions, classes, or sections by description

    Args:
        query: Natural language description of what you're looking for
               Examples: "training loop", "database connection", "error handling"
        top_k: Maximum number of results (1-50, default 10)
        file_types: Comma-separated file types (e.g., "python,markdown")
        directory: Only search within this directory path
        git_only: Only return git-tracked files
        min_relevance: Minimum relevance score (0-1, default 0.3)
        explain: Include explanation for why each result matched (default True)

    Returns:
        Matching files and chunks with paths, line numbers, previews,
        and explanations of why each result matched
    """
    # Input validation
    if not query or not isinstance(query, str):
        return {"error": "Query must be a non-empty string"}
    if len(query) > 1000:
        return {"error": "Query too long (max 1000 characters)"}

    index = await get_index_instance()

    # Check if index exists
    status = index.get_status()
    if status["files_indexed"] == 0:
        return {
            "error": "No files indexed yet",
            "hint": "Run: python -m file_compass.cli index -d \"F:/AI\""
        }

    # Parse and validate file_types
    types_list = None
    if file_types:
        types_list = [t.strip()[:50] for t in file_types.split(",")[:20]]  # Limit types

    # Clamp parameters
    top_k = max(1, min(50, top_k))
    min_relevance = max(0.0, min(1.0, min_relevance))

    # Search
    results = await index.search(
        query=query,
        top_k=top_k,
        file_types=types_list,
        directory=directory,
        git_only=git_only,
        min_relevance=min_relevance
    )

    # Format results with explanations
    matches = []
    for r in results:
        match_data = {
            "path": r.path,
            "relative_path": r.relative_path,
            "file_type": r.file_type,
            "chunk_type": r.chunk_type,
            "chunk_name": r.chunk_name,
            "lines": f"{r.line_start}-{r.line_end}",
            "relevance": round(r.relevance, 3),
            "preview": r.preview[:200] + "..." if len(r.preview) > 200 else r.preview,
            "git_tracked": r.git_tracked
        }

        # Add explanation if requested
        if explain:
            explanation = _explainer.explain_match(
                query=query,
                result_preview=r.preview,
                result_path=r.path,
                chunk_name=r.chunk_name,
                chunk_type=r.chunk_type,
                relevance=r.relevance
            )
            match_data["why"] = explanation.summary
            match_data["match_reasons"] = [
                {
                    "type": reason.reason_type,
                    "detail": reason.description,
                    "confidence": round(reason.confidence, 2)
                }
                for reason in explanation.reasons[:3]  # Top 3 reasons
            ]

        matches.append(match_data)

    return {
        "query": query,
        "results": matches,
        "count": len(matches),
        "total_indexed": status["files_indexed"],
        "hint": f"Found {len(matches)} results. Use Read tool to view full content."
    }


def _is_path_safe(path: Path, config) -> bool:
    """Check if path is within allowed indexed directories."""
    try:
        resolved = path.resolve()
        for directory in config.directories:
            dir_resolved = Path(directory).resolve()
            # Check if path is under an allowed directory
            try:
                resolved.relative_to(dir_resolved)
                return True
            except ValueError:
                continue
        return False
    except (OSError, ValueError):
        return False


@mcp.tool()
async def file_preview(
    path: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    query: Optional[str] = None,
    context_lines: int = 3
) -> Dict[str, Any]:
    """
    Get a visual code preview from a specific file.

    Returns formatted content with line numbers, syntax language detection,
    and optional highlighting of lines matching the query.

    Args:
        path: Full path to the file (must be within indexed directories)
        line_start: Starting line number (1-indexed, optional)
        line_end: Ending line number (optional)
        query: Optional search query to highlight matching lines
        context_lines: Lines of context around the range (default 3)

    Returns:
        Visual code preview with:
        - content: Formatted lines with line numbers and markers
        - language: Detected programming language
        - highlight_lines: Line numbers that match the query
        - truncated: Whether the preview was cut off
    """
    config = get_config()

    # Input validation
    if not path or not isinstance(path, str):
        return {"error": "Path must be a non-empty string"}
    if len(path) > 500:
        return {"error": "Path too long"}
    if line_start is not None and (not isinstance(line_start, int) or line_start < 1):
        return {"error": "line_start must be a positive integer"}
    if line_end is not None and (not isinstance(line_end, int) or line_end < 1):
        return {"error": "line_end must be a positive integer"}
    if context_lines < 0 or context_lines > 50:
        context_lines = 3  # Reset to default if invalid

    try:
        file_path = Path(path)

        # Security: Validate path is within allowed directories
        if not _is_path_safe(file_path, config):
            return {
                "error": "Access denied: path is outside allowed directories"
            }

        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        # Use visual preview generator for rich output
        if line_start is not None:
            # Generate visual preview with context
            preview = _preview_generator.generate_preview(
                file_path=path,
                line_start=line_start,
                line_end=line_end or line_start,
                query=query,
                highlight_matches=query is not None
            )

            if preview:
                return {
                    "path": path,
                    "lines": f"{preview.line_start}-{preview.line_end}",
                    "content": preview.content,
                    "language": preview.language,
                    "highlight_lines": preview.highlight_lines,
                    "total_lines": preview.total_lines,
                    "truncated": preview.truncated
                }

        # Fallback: Read full file (limited)
        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")
        total_lines = len(lines)

        # Detect language
        ext_to_lang = _preview_generator.EXT_TO_LANG
        language = ext_to_lang.get(file_path.suffix.lower(), "text")

        # Apply line range
        if line_start is not None:
            start_idx = max(0, line_start - 1)
            end_idx = line_end if line_end else total_lines
            lines = lines[start_idx:end_idx]
            line_offset = start_idx + 1
        else:
            line_offset = 1

        # Format with line numbers and markers
        numbered_lines = []
        max_line_width = len(str(line_offset + min(100, len(lines)) - 1))

        for i, line in enumerate(lines[:100]):  # Limit to 100 lines
            line_num = str(line_offset + i).rjust(max_line_width)
            numbered_lines.append(f"{line_num} │ {line}")

        preview_content = "\n".join(numbered_lines)
        truncated = len(lines) > 100
        if truncated:
            preview_content += f"\n... ({len(lines) - 100} more lines)"

        return {
            "path": path,
            "lines": f"{line_offset}-{line_offset + len(numbered_lines) - 1}",
            "content": preview_content,
            "language": language,
            "highlight_lines": [],
            "total_lines": total_lines,
            "truncated": truncated
        }

    except Exception as e:
        logger.error(f"file_preview error: {e}")
        return {"error": "Failed to read file"}


@mcp.tool()
async def file_index_status() -> Dict[str, Any]:
    """
    Get the current status of the file index.

    Returns:
        Index statistics including file counts, types, and last build time
    """
    index = await get_index_instance()
    status = index.get_status()

    return {
        "files_indexed": status["files_indexed"],
        "chunks_indexed": status["chunks_indexed"],
        "index_size_mb": round(status["index_size_mb"], 2),
        "last_build": status["last_build"],
        "file_types": status["file_types"],
        "hint": "Use file_search() to find files, or file_index_scan() to rebuild"
    }


@mcp.tool()
async def file_index_scan(
    directories: Optional[str] = None,
    force_rebuild: bool = False
) -> Dict[str, Any]:
    """
    Scan directories and build/rebuild the file index.

    This is a long-running operation that:
    1. Scans directories for code files
    2. Chunks files into semantic pieces
    3. Generates embeddings via Ollama
    4. Builds HNSW search index

    Args:
        directories: Comma-separated directory paths (default: F:/AI)
        force_rebuild: If True, rebuilds entire index even if files haven't changed

    Returns:
        Statistics about the indexing process
    """
    index = await get_index_instance()
    config = get_config()

    # Parse and validate directories
    if directories:
        dir_list = [d.strip() for d in directories.split(",")[:10]]  # Limit to 10 dirs

        # Validate each directory exists and is accessible
        validated_dirs = []
        for d in dir_list:
            if len(d) > 500:
                continue  # Skip overly long paths
            dir_path = Path(d)
            try:
                if dir_path.exists() and dir_path.is_dir():
                    validated_dirs.append(str(dir_path.resolve()))
            except (OSError, ValueError):
                continue  # Skip invalid paths

        if not validated_dirs:
            return {
                "success": False,
                "error": "No valid directories provided"
            }
        dir_list = validated_dirs
    else:
        dir_list = config.directories

    try:
        stats = await index.build_index(
            directories=dir_list,
            show_progress=False  # Can't show progress over MCP
        )

        return {
            "success": True,
            "files_indexed": stats["files_indexed"],
            "chunks_indexed": stats["chunks_indexed"],
            "duration_seconds": round(stats["duration_seconds"], 1),
            "directories": dir_list,
            "hint": "Index built! Use file_search() to find files."
        }

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        return {
            "success": False,
            "error": "Indexing failed",
            "hint": "Make sure Ollama is running with nomic-embed-text model"
        }


@mcp.tool()
async def file_quick_search(
    query: str,
    top_k: int = 15,
    file_types: Optional[str] = None,
    recent_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fast search by filename and symbol names (instant, no AI embeddings).

    Use this for:
    - Finding files by name when you know roughly what it's called
    - Finding functions/classes by name
    - Quick navigation when semantic search is overkill
    - Searching while full index is building

    Args:
        query: Search terms (filename, function name, class name)
        top_k: Max results (default 15)
        file_types: Filter by type (e.g., "python,javascript")
        recent_days: Only search files modified in last N days

    Returns:
        Matching files and symbols with paths and line numbers
    """
    # Input validation
    if not query or not isinstance(query, str):
        return {"error": "Query must be a non-empty string"}
    if len(query) > 500:
        return {"error": "Query too long (max 500 characters)"}

    # Clamp parameters
    top_k = max(1, min(100, top_k))
    if recent_days is not None:
        recent_days = max(1, min(365, recent_days))

    quick_index = get_quick_index()

    # Check if quick index exists
    status = quick_index.get_status()
    if status["files_indexed"] == 0:
        # Build it on-demand (fast)
        await quick_index.build_quick_index(show_progress=False)
        status = quick_index.get_status()

    # Parse and validate file types
    types_list = None
    if file_types:
        types_list = [t.strip()[:50] for t in file_types.split(",")[:20]]

    # Search
    results = quick_index.search(
        query=query,
        top_k=top_k,
        file_types=types_list,
        recent_days=recent_days
    )

    # Format results
    matches = []
    for r in results:
        match_data = {
            "path": r.path,
            "relative_path": r.relative_path,
            "file_type": r.file_type,
            "match_type": r.match_type,
            "match_text": r.match_text,
            "score": round(r.score, 2)
        }
        if r.line_number:
            match_data["line"] = r.line_number
            match_data["hint"] = f"Use file_preview(path, line_start={r.line_number}) to view"

        matches.append(match_data)

    return {
        "query": query,
        "results": matches,
        "count": len(matches),
        "index_stats": {
            "files": status["files_indexed"],
            "symbols": status["symbols_indexed"]
        },
        "hint": "For semantic search, use file_search() instead"
    }


@mcp.tool()
async def file_quick_index_build() -> Dict[str, Any]:
    """
    Build the quick index (fast filename + symbol index).

    This is INSTANT (2-10 seconds) and provides basic search while
    the full semantic index builds. Run this first for immediate utility.

    Returns:
        Statistics about the quick indexing
    """
    quick_index = get_quick_index()
    config = get_config()

    try:
        stats = await quick_index.build_quick_index(
            directories=config.directories,
            extract_symbols=True,
            show_progress=False
        )

        return {
            "success": True,
            "files_indexed": stats["files_indexed"],
            "symbols_extracted": stats["symbols_extracted"],
            "duration_seconds": round(stats["duration_seconds"], 2),
            "hint": "Quick index built! Use file_quick_search() for instant results."
        }

    except Exception as e:
        logger.error(f"Quick indexing failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def file_actions(
    path: str,
    action: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform follow-up actions on a search result.

    After finding a file with file_search(), use this tool to:
    - Get more context around a match
    - Find other usages of a function/class
    - See the file's git history
    - Find related files

    Args:
        path: Path to the file (from search result)
        action: One of:
            - "context": Get surrounding code context
            - "usages": Find where this file/symbol is used
            - "related": Find files that import or are imported by this file
            - "history": Get recent git changes to this file
            - "symbols": List all functions/classes defined in this file
        line_start: For context action, center around this line
        line_end: For context action, include up to this line

    Returns:
        Action-specific results
    """
    # Input validation
    if not path or not isinstance(path, str):
        return {"error": "Path must be a non-empty string"}
    if len(path) > 500:
        return {"error": "Path too long"}
    if not action or not isinstance(action, str):
        return {"error": "Action must be a non-empty string"}

    valid_actions = ["context", "usages", "related", "history", "symbols"]
    if action not in valid_actions:
        return {
            "error": "Invalid action",
            "available_actions": valid_actions
        }

    if line_start is not None and (not isinstance(line_start, int) or line_start < 1):
        return {"error": "line_start must be a positive integer"}
    if line_end is not None and (not isinstance(line_end, int) or line_end < 1):
        return {"error": "line_end must be a positive integer"}

    config = get_config()
    file_path = Path(path)

    # Security check
    if not _is_path_safe(file_path, config):
        return {
            "error": "Access denied: path is outside allowed directories"
        }

    if not file_path.exists():
        return {"error": "File not found"}

    try:
        if action == "context":
            return await _action_context(file_path, line_start, line_end)
        elif action == "usages":
            return await _action_usages(file_path)
        elif action == "related":
            return await _action_related(file_path)
        elif action == "history":
            return await _action_history(file_path)
        elif action == "symbols":
            return await _action_symbols(file_path)
    except Exception as e:
        logger.error(f"Action {action} failed for {path}: {e}")
        return {"error": "Action failed"}


async def _action_context(file_path: Path, line_start: Optional[int], line_end: Optional[int]) -> Dict[str, Any]:
    """Get surrounding code context."""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    total_lines = len(lines)

    # Default to showing middle of file
    if line_start is None:
        line_start = 1
    if line_end is None:
        line_end = min(line_start + 50, total_lines)

    # Expand context
    context_start = max(1, line_start - 10)
    context_end = min(total_lines, line_end + 10)

    # Format with line numbers
    preview_lines = []
    for i in range(context_start - 1, context_end):
        line_num = i + 1
        marker = "→" if line_start <= line_num <= line_end else " "
        preview_lines.append(f"{line_num:4d} {marker}│ {lines[i]}")

    return {
        "path": str(file_path),
        "context_range": f"{context_start}-{context_end}",
        "focus_range": f"{line_start}-{line_end}",
        "content": "\n".join(preview_lines),
        "total_lines": total_lines
    }


async def _action_usages(file_path: Path) -> Dict[str, Any]:
    """Find where this file or its exports are used."""
    index = await get_index_instance()

    # Search for imports/usages of this file
    filename = file_path.stem  # e.g., "embedder" from "embedder.py"
    relative_path = file_path.name

    # Search for import patterns
    import_patterns = [
        f"import {filename}",
        f"from {filename}",
        f"from .{filename}",
        f"require('{filename}')",
        f"import {{ .* }} from './{filename}'",
    ]

    usages = []
    for pattern in import_patterns[:2]:  # Limit searches
        results = await index.search(
            query=pattern,
            top_k=10,
            min_relevance=0.4
        )
        for r in results:
            if r.path != str(file_path):  # Don't include self
                usages.append({
                    "path": r.relative_path,
                    "lines": f"{r.line_start}-{r.line_end}",
                    "preview": r.preview[:100]
                })

    # Deduplicate by path
    seen = set()
    unique_usages = []
    for u in usages:
        if u["path"] not in seen:
            seen.add(u["path"])
            unique_usages.append(u)

    return {
        "file": str(file_path),
        "usages": unique_usages[:15],  # Limit results
        "count": len(unique_usages),
        "hint": "Files that import or reference this module"
    }


async def _action_related(file_path: Path) -> Dict[str, Any]:
    """Find files related to this one (imports and importers)."""
    content = file_path.read_text(encoding="utf-8", errors="replace")

    # Extract imports from this file
    import_pattern = r'^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)'
    imports = []
    for line in content.split("\n"):
        match = re.match(import_pattern, line.strip())
        if match:
            imports.append(match.group(1).split(".")[0])

    # Search for files that might be the imports
    index = await get_index_instance()
    related = []

    for imp in set(imports[:10]):  # Limit to avoid too many searches
        results = await index.search(
            query=f"module {imp}",
            top_k=3,
            min_relevance=0.5
        )
        for r in results:
            if imp in r.relative_path.lower():
                related.append({
                    "path": r.relative_path,
                    "relationship": "imported_by_this_file",
                    "module": imp
                })

    # Also get usages (files that import this)
    usages_result = await _action_usages(file_path)

    return {
        "file": str(file_path),
        "imports": list(set(imports))[:20],
        "imported_modules": related[:10],
        "imported_by": usages_result.get("usages", [])[:10],
        "hint": "Shows both what this file imports and what imports this file"
    }


async def _action_history(file_path: Path) -> Dict[str, Any]:
    """Get recent git history for the file."""
    try:
        # Get git log for the file
        result = subprocess.run(
            ["git", "log", "--oneline", "-10", "--", str(file_path)],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return {
                "file": str(file_path),
                "error": "Not a git repository or git not available",
                "hint": "Git history requires the file to be in a git repository"
            }

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(" ", 1)
                commits.append({
                    "hash": parts[0],
                    "message": parts[1] if len(parts) > 1 else ""
                })

        # Get last modified info
        stat_result = subprocess.run(
            ["git", "log", "-1", "--format=%ci %an", "--", str(file_path)],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        last_modified = stat_result.stdout.strip() if stat_result.returncode == 0 else "unknown"

        return {
            "file": str(file_path),
            "last_modified": last_modified,
            "recent_commits": commits,
            "hint": "Recent git commits affecting this file"
        }

    except subprocess.TimeoutExpired:
        return {"file": str(file_path), "error": "Git command timed out"}
    except FileNotFoundError:
        return {"file": str(file_path), "error": "Git not found in PATH"}


async def _action_symbols(file_path: Path) -> Dict[str, Any]:
    """List all functions/classes defined in the file."""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    symbols = []
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        # Python: find def/class
        for i, line in enumerate(lines, 1):
            # Function definitions
            match = re.match(r'^(\s*)(async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                indent = len(match.group(1))
                symbols.append({
                    "type": "function",
                    "name": match.group(3),
                    "line": i,
                    "indent": indent,
                    "async": bool(match.group(2))
                })
            # Class definitions
            match = re.match(r'^(\s*)class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                indent = len(match.group(1))
                symbols.append({
                    "type": "class",
                    "name": match.group(2),
                    "line": i,
                    "indent": indent
                })

    elif suffix in (".js", ".ts", ".jsx", ".tsx"):
        # JavaScript/TypeScript: find function/class/const
        for i, line in enumerate(lines, 1):
            # Functions
            match = re.match(r'^\s*(export\s+)?(async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                symbols.append({
                    "type": "function",
                    "name": match.group(3),
                    "line": i,
                    "exported": bool(match.group(1))
                })
            # Classes
            match = re.match(r'^\s*(export\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                symbols.append({
                    "type": "class",
                    "name": match.group(2),
                    "line": i,
                    "exported": bool(match.group(1))
                })
            # Arrow functions assigned to const
            match = re.match(r'^\s*(export\s+)?const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(async\s+)?\(', line)
            if match:
                symbols.append({
                    "type": "function",
                    "name": match.group(2),
                    "line": i,
                    "exported": bool(match.group(1)),
                    "arrow": True
                })

    else:
        # Generic: look for common patterns
        for i, line in enumerate(lines, 1):
            # Generic function pattern
            match = re.match(r'^\s*(?:pub\s+)?(?:async\s+)?(?:fn|func|def|function)\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                symbols.append({
                    "type": "function",
                    "name": match.group(1),
                    "line": i
                })

    # Group by type
    functions = [s for s in symbols if s["type"] == "function"]
    classes = [s for s in symbols if s["type"] == "class"]

    return {
        "file": str(file_path),
        "language": suffix.lstrip("."),
        "functions": functions,
        "classes": classes,
        "total_symbols": len(symbols),
        "hint": "Jump to any symbol with file_preview(path, line_start=<line>)"
    }


# =============================================================================
# CLI COMMANDS
# =============================================================================

async def build_index_cli(directories: List[str]):
    """Build index from CLI."""
    print("Building File Compass index...")
    print("=" * 50)

    index = FileIndex()

    stats = await index.build_index(
        directories=directories,
        show_progress=True
    )

    print("\nIndex built successfully!")
    print(f"  Files: {stats['files_indexed']}")
    print(f"  Chunks: {stats['chunks_indexed']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")

    await index.close()


async def run_tests():
    """Run test queries."""
    print("\n" + "=" * 60)
    print("FILE COMPASS - TEST SUITE")
    print("=" * 60)

    index = FileIndex()
    status = index.get_status()

    print(f"\nIndex: {status['files_indexed']} files, {status['chunks_indexed']} chunks")

    test_queries = [
        "embedding generation",
        "file scanner",
        "HNSW index",
        "configuration settings",
        "async function",
    ]

    print("\n" + "-" * 60)
    print("Semantic Search Tests")
    print("-" * 60)

    for query in test_queries:
        results = await index.search(query, top_k=3)

        print(f"\nQuery: '{query}'")
        if results:
            for r in results:
                print(f"  [{r.relevance:.1%}] {r.relative_path}")
                print(f"         {r.chunk_type}: {r.chunk_name or 'unnamed'} (L{r.line_start}-{r.line_end})")
        else:
            print("  No results")

    await index.close()


def main():
    parser = argparse.ArgumentParser(
        description="File Compass - Semantic File Search MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gateway.py              Start MCP server
  python gateway.py --index      Build index for F:/AI
  python gateway.py --test       Run test queries
        """
    )
    parser.add_argument("--index", action="store_true", help="Build search index")
    parser.add_argument("--test", action="store_true", help="Run test queries")
    parser.add_argument("-d", "--directories", nargs="+", help="Directories to index")

    args = parser.parse_args()

    if args.index:
        dirs = args.directories or ["F:/AI"]
        asyncio.run(build_index_cli(dirs))
    elif args.test:
        asyncio.run(run_tests())
    else:
        # Start MCP server
        print("Starting File Compass MCP Server...", file=sys.stderr)
        print("Tools: file_search, file_preview, file_index_status, file_index_scan", file=sys.stderr)
        mcp.run()


if __name__ == "__main__":
    main()
