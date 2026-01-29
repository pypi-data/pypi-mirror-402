"""
File Compass - Chunker Module
Splits files into semantic chunks for embedding.
Supports AST-aware chunking via tree-sitter for multiple languages.
"""

import ast
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import logging

from .config import get_config

# Tree-sitter imports (optional - falls back to Python AST if unavailable)
try:
    import tree_sitter
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    import tree_sitter_rust
    import tree_sitter_go
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a chunk of file content for embedding."""
    content: str
    chunk_type: str  # 'whole_file', 'function', 'class', 'method', 'section', 'window'
    name: Optional[str]  # Function/class name if applicable
    line_start: int
    line_end: int
    preview: str  # First ~200 chars for display
    # Scope context (parent class/module info)
    parent_class: Optional[str] = None  # Enclosing class name for methods
    parent_module: Optional[str] = None  # Module/namespace
    language: Optional[str] = None  # Detected language

    @property
    def token_estimate(self) -> int:
        """Rough token count estimate (words * 1.3)."""
        return int(len(self.content.split()) * 1.3)

    @property
    def qualified_name(self) -> Optional[str]:
        """Get fully qualified name (e.g., 'ClassName.method_name')."""
        if self.name:
            if self.parent_class:
                return f"{self.parent_class}.{self.name}"
            return self.name
        return None


class FileChunker:
    """
    Chunks files into semantic pieces for embedding.
    Uses tree-sitter for multi-language AST parsing, heading-based for Markdown,
    sliding window for others.
    """

    # Language mapping: extension -> (tree-sitter language module, language name)
    LANGUAGE_MAP: Dict[str, Tuple[Any, str]] = {}

    def __init__(
        self,
        max_chunk_tokens: Optional[int] = None,
        chunk_overlap_tokens: Optional[int] = None,
        min_chunk_tokens: Optional[int] = None,
        use_tree_sitter: bool = True
    ):
        config = get_config()
        self.max_tokens = max_chunk_tokens or config.max_chunk_tokens
        self.overlap_tokens = chunk_overlap_tokens or config.chunk_overlap_tokens
        self.min_tokens = min_chunk_tokens or config.min_chunk_tokens
        self.use_tree_sitter = use_tree_sitter and TREE_SITTER_AVAILABLE

        # Initialize tree-sitter parsers
        self._parsers: Dict[str, Any] = {}
        if self.use_tree_sitter:
            self._init_tree_sitter_parsers()

    def _init_tree_sitter_parsers(self):
        """Initialize tree-sitter language parsers."""
        if not TREE_SITTER_AVAILABLE:
            return

        # Map extensions to language modules
        lang_configs = [
            ([".py"], tree_sitter_python, "python"),
            ([".js", ".jsx", ".mjs"], tree_sitter_javascript, "javascript"),
            ([".ts"], tree_sitter_typescript.language_typescript, "typescript"),
            ([".tsx"], tree_sitter_typescript.language_tsx, "tsx"),
            ([".rs"], tree_sitter_rust, "rust"),
            ([".go"], tree_sitter_go, "go"),
        ]

        for extensions, lang_module, lang_name in lang_configs:
            try:
                # Get language from module
                if hasattr(lang_module, 'language'):
                    language = tree_sitter.Language(lang_module.language())
                else:
                    # For typescript which returns language directly
                    language = tree_sitter.Language(lang_module())

                parser = tree_sitter.Parser(language)

                for ext in extensions:
                    self._parsers[ext] = (parser, lang_name)

                logger.debug(f"Initialized tree-sitter parser for {lang_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize tree-sitter for {lang_name}: {e}")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        return int(len(text.split()) * 1.3)

    def _make_preview(self, content: str, max_len: int = 200) -> str:
        """Create preview string from content."""
        preview = content[:max_len].strip()
        if len(content) > max_len:
            preview += "..."
        return preview

    # Maximum file size (10MB) - matches scanner limit
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def chunk_file(self, path: Path, content: Optional[str] = None) -> List[Chunk]:
        """
        Chunk a file based on its type.

        Args:
            path: Path to the file
            content: Optional pre-read content

        Returns:
            List of Chunk objects
        """
        if content is None:
            try:
                # Security: Check file size before reading
                if path.exists():
                    file_size = path.stat().st_size
                    if file_size > self.MAX_FILE_SIZE:
                        logger.warning(f"Skipping large file ({file_size} bytes): {path}")
                        return []

                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.error(f"Failed to read {path}: {e}")
                return []

        # Choose chunking strategy based on file type
        suffix = path.suffix.lower()

        # Try tree-sitter for supported languages
        if self.use_tree_sitter and suffix in self._parsers:
            parser, lang_name = self._parsers[suffix]
            chunks = self._chunk_with_tree_sitter(content, parser, lang_name)
            if chunks:  # Only use if parsing succeeded
                # Set language on all chunks
                for chunk in chunks:
                    chunk.language = lang_name
                return self._finalize_chunks(chunks, content)

        # Fall back to language-specific handlers
        if suffix == ".py":
            chunks = self._chunk_python(content)
        elif suffix == ".md":
            chunks = self._chunk_markdown(content)
        elif suffix in (".json", ".yaml", ".yml"):
            chunks = self._chunk_structured(content, suffix)
        else:
            chunks = self._chunk_sliding_window(content)

        return self._finalize_chunks(chunks, content)

    def _finalize_chunks(self, chunks: List[Chunk], content: str) -> List[Chunk]:
        """
        Finalize chunks by filtering tiny ones and splitting oversized ones.

        Args:
            chunks: Raw chunks from parsing
            content: Original file content

        Returns:
            Finalized list of chunks
        """
        # Filter out empty/tiny chunks
        chunks = [c for c in chunks if self._estimate_tokens(c.content) >= self.min_tokens]

        # If no chunks or all filtered, return whole file as single chunk (or sliding window if too large)
        if not chunks:
            if len(content) > 6000:  # Too large for single chunk, use sliding window
                return self._chunk_sliding_window(content)
            return [Chunk(
                content=content,
                chunk_type="whole_file",
                name=None,
                line_start=1,
                line_end=content.count("\n") + 1,
                preview=self._make_preview(content)
            )]

        # Split any oversized chunks using sliding window (nomic-embed-text limit ~8192 tokens)
        final_chunks = []
        for chunk in chunks:
            if len(chunk.content) > 6000:
                # Re-chunk this oversized chunk
                sub_chunks = self._chunk_sliding_window(chunk.content)
                # Adjust line numbers relative to original chunk
                for sc in sub_chunks:
                    sc.line_start += chunk.line_start - 1
                    sc.line_end += chunk.line_start - 1
                    sc.name = chunk.name  # Preserve original name
                    sc.parent_class = chunk.parent_class  # Preserve scope context
                    sc.language = chunk.language
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _chunk_with_tree_sitter(self, content: str, parser: Any, lang_name: str) -> List[Chunk]:
        """
        Chunk code using tree-sitter AST parsing.
        Supports multiple languages with consistent semantic boundaries.

        Args:
            content: File content
            parser: Tree-sitter parser instance
            lang_name: Language name

        Returns:
            List of Chunk objects
        """
        if not TREE_SITTER_AVAILABLE:
            return []

        try:
            tree = parser.parse(bytes(content, 'utf-8'))
        except Exception as e:
            logger.warning(f"Tree-sitter parse failed for {lang_name}: {e}")
            return []

        chunks = []
        lines = content.split("\n")

        # Define node types to extract for each language
        # Maps: lang_name -> (function_types, class_types, method_parent_type)
        lang_definitions = {
            "python": (
                ["function_definition"],
                ["class_definition"],
                "class_definition"
            ),
            "javascript": (
                ["function_declaration", "arrow_function", "function_expression"],
                ["class_declaration"],
                "class_declaration"
            ),
            "typescript": (
                ["function_declaration", "arrow_function", "function_expression"],
                ["class_declaration", "interface_declaration", "type_alias_declaration"],
                "class_declaration"
            ),
            "tsx": (
                ["function_declaration", "arrow_function", "function_expression"],
                ["class_declaration", "interface_declaration", "type_alias_declaration"],
                "class_declaration"
            ),
            "rust": (
                ["function_item"],
                ["struct_item", "enum_item", "impl_item", "trait_item"],
                "impl_item"
            ),
            "go": (
                ["function_declaration", "method_declaration"],
                ["type_declaration"],
                "type_declaration"
            ),
        }

        func_types, class_types, method_parent = lang_definitions.get(
            lang_name, ([], [], None)
        )

        # Track what's been extracted
        extracted_ranges = set()

        def get_node_text(node) -> str:
            """Get text for a node."""
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            return "\n".join(lines[start_line:end_line + 1])

        def get_node_name(node) -> Optional[str]:
            """Extract name from node (language-specific)."""
            # Look for identifier child
            for child in node.children:
                if child.type == "identifier":
                    return child.text.decode('utf-8')
                if child.type == "name":  # Python
                    return child.text.decode('utf-8')
                if child.type == "property_identifier":  # JS methods
                    return child.text.decode('utf-8')
            return None

        def find_parent_class(node) -> Optional[str]:
            """Find enclosing class name."""
            parent = node.parent
            while parent:
                if parent.type in class_types:
                    return get_node_name(parent)
                parent = parent.parent
            return None

        def extract_node(node, chunk_type: str, parent_class: Optional[str] = None):
            """Extract a node as a chunk."""
            start_line = node.start_point[0]
            end_line = node.end_point[0]

            # Skip if already extracted
            range_key = (start_line, end_line)
            if range_key in extracted_ranges:
                return
            extracted_ranges.add(range_key)

            text = get_node_text(node)
            name = get_node_name(node)

            # Skip tiny nodes
            if self._estimate_tokens(text) < self.min_tokens:
                return

            chunks.append(Chunk(
                content=text,
                chunk_type=chunk_type,
                name=name,
                line_start=start_line + 1,  # 1-indexed
                line_end=end_line + 1,
                preview=self._make_preview(text),
                parent_class=parent_class,
                language=lang_name
            ))

        def walk_tree(node):
            """Recursively walk tree and extract semantic nodes."""
            # Check for functions
            if node.type in func_types:
                parent_class = find_parent_class(node)
                chunk_type = "method" if parent_class else "function"
                extract_node(node, chunk_type, parent_class)

            # Check for classes
            elif node.type in class_types:
                extract_node(node, "class")

            # Recurse to children
            for child in node.children:
                walk_tree(child)

        walk_tree(tree.root_node)

        # Sort by line number
        chunks.sort(key=lambda c: c.line_start)

        return chunks

    def _chunk_python(self, content: str) -> List[Chunk]:
        """
        Chunk Python file using AST.
        Extracts functions, classes, and module-level code.
        """
        chunks = []
        lines = content.split("\n")

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to sliding window for invalid Python
            return self._chunk_sliding_window(content)

        # Track what lines are covered by functions/classes
        covered_lines = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = node.end_lineno or start

                # Include decorators
                if node.decorator_list:
                    start = min(d.lineno for d in node.decorator_list)

                chunk_lines = lines[start - 1:end]
                chunk_content = "\n".join(chunk_lines)

                # Skip if too large (will be handled by sliding window)
                if self._estimate_tokens(chunk_content) <= self.max_tokens * 2:
                    chunks.append(Chunk(
                        content=chunk_content,
                        chunk_type="function",
                        name=node.name,
                        line_start=start,
                        line_end=end,
                        preview=self._make_preview(chunk_content)
                    ))
                    covered_lines.update(range(start, end + 1))

            elif isinstance(node, ast.ClassDef):
                start = node.lineno
                end = node.end_lineno or start

                # Include decorators
                if node.decorator_list:
                    start = min(d.lineno for d in node.decorator_list)

                chunk_lines = lines[start - 1:end]
                chunk_content = "\n".join(chunk_lines)

                # For large classes, just take the signature and docstring
                if self._estimate_tokens(chunk_content) > self.max_tokens * 2:
                    # Get class definition + first method or docstring
                    preview_end = min(start + 30, end)
                    chunk_content = "\n".join(lines[start - 1:preview_end])
                    chunk_content += "\n    # ... (class continues)"
                    end = preview_end

                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_type="class",
                    name=node.name,
                    line_start=start,
                    line_end=end,
                    preview=self._make_preview(chunk_content)
                ))
                covered_lines.update(range(start, end + 1))

        # Get module-level code (imports, constants, etc.) if significant
        module_lines = []
        for i, line in enumerate(lines, 1):
            if i not in covered_lines:
                module_lines.append((i, line))

        if module_lines:
            # Group consecutive uncovered lines
            groups = []
            current_group = []

            for i, line in module_lines:
                if current_group and i > current_group[-1][0] + 1:
                    groups.append(current_group)
                    current_group = []
                current_group.append((i, line))

            if current_group:
                groups.append(current_group)

            # Create chunks for significant groups
            for group in groups:
                content = "\n".join(line for _, line in group)
                if self._estimate_tokens(content) >= self.min_tokens:
                    chunks.append(Chunk(
                        content=content,
                        chunk_type="module",
                        name=None,
                        line_start=group[0][0],
                        line_end=group[-1][0],
                        preview=self._make_preview(content)
                    ))

        # Sort by line number
        chunks.sort(key=lambda c: c.line_start)

        return chunks

    def _chunk_markdown(self, content: str) -> List[Chunk]:
        """
        Chunk Markdown file by headings.
        Each heading starts a new chunk.
        """
        chunks = []
        lines = content.split("\n")

        # Find heading positions
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
        headings = []

        for i, line in enumerate(lines):
            match = heading_pattern.match(line)
            if match:
                level = len(match.group(1))
                title = match.group(2)
                headings.append((i, level, title))

        if not headings:
            # No headings, return whole file
            return self._chunk_sliding_window(content)

        # Create chunks between headings
        for idx, (line_idx, level, title) in enumerate(headings):
            # Find end (next heading of same or higher level, or EOF)
            end_idx = len(lines)
            for next_line_idx, next_level, _ in headings[idx + 1:]:
                if next_level <= level:
                    end_idx = next_line_idx
                    break

            chunk_lines = lines[line_idx:end_idx]
            chunk_content = "\n".join(chunk_lines).strip()

            if chunk_content:
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_type="section",
                    name=title,
                    line_start=line_idx + 1,
                    line_end=end_idx,
                    preview=self._make_preview(chunk_content)
                ))

        return chunks

    def _chunk_structured(self, content: str, suffix: str) -> List[Chunk]:
        """
        Chunk JSON/YAML by top-level keys.
        Falls back to sliding window if too complex.
        """
        # For now, use sliding window
        # TODO: Parse and chunk by top-level keys
        return self._chunk_sliding_window(content)

    def _chunk_sliding_window(self, content: str) -> List[Chunk]:
        """
        Chunk using sliding window with overlap.
        Used as fallback for unstructured content.
        """
        chunks = []
        lines = content.split("\n")

        # Estimate chars per token
        total_tokens = self._estimate_tokens(content)
        if total_tokens == 0:
            return []

        chars_per_token = len(content) / max(total_tokens, 1)
        max_chars = int(self.max_tokens * chars_per_token)
        overlap_chars = int(self.overlap_tokens * chars_per_token)

        # Build chunks
        current_chunk = []
        current_chars = 0
        chunk_start_line = 1

        for i, line in enumerate(lines, 1):
            line_chars = len(line) + 1  # +1 for newline

            if current_chars + line_chars > max_chars and current_chunk:
                # Save current chunk
                chunk_content = "\n".join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_content,
                    chunk_type="window",
                    name=None,
                    line_start=chunk_start_line,
                    line_end=i - 1,
                    preview=self._make_preview(chunk_content)
                ))

                # Start new chunk with overlap
                overlap_lines = []
                overlap_size = 0
                for prev_line in reversed(current_chunk):
                    if overlap_size + len(prev_line) > overlap_chars:
                        break
                    overlap_lines.insert(0, prev_line)
                    overlap_size += len(prev_line) + 1

                current_chunk = overlap_lines
                current_chars = overlap_size
                chunk_start_line = i - len(overlap_lines)

            current_chunk.append(line)
            current_chars += line_chars

        # Save final chunk
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            chunks.append(Chunk(
                content=chunk_content,
                chunk_type="window",
                name=None,
                line_start=chunk_start_line,
                line_end=len(lines),
                preview=self._make_preview(chunk_content)
            ))

        return chunks


if __name__ == "__main__":
    # Test chunking
    chunker = FileChunker()

    # Test Python file
    test_py = Path("F:/AI/mcp-tool-shop/file_compass/scanner.py")
    if test_py.exists():
        chunks = chunker.chunk_file(test_py)
        print(f"Python file: {len(chunks)} chunks")
        for c in chunks[:5]:
            print(f"  {c.chunk_type}: {c.name or 'unnamed'} (lines {c.line_start}-{c.line_end})")

    # Test Markdown file
    test_md = Path("F:/AI/.claude/CLAUDE.md")
    if test_md.exists():
        chunks = chunker.chunk_file(test_md)
        print(f"\nMarkdown file: {len(chunks)} chunks")
        for c in chunks[:5]:
            print(f"  {c.chunk_type}: {c.name or 'unnamed'} (lines {c.line_start}-{c.line_end})")
