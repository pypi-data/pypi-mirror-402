"""
File Compass - Result Explainer Module
Provides explanations for why search results matched and visual code previews.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class MatchReason:
    """A single reason why a result matched."""
    reason_type: str  # "exact", "semantic", "filename", "structure"
    description: str
    confidence: float  # 0-1
    matched_text: Optional[str] = None
    location: Optional[str] = None  # e.g., "line 42", "function name"


@dataclass
class ExplainedResult:
    """Search result with explanation of why it matched."""
    relevance: float
    reasons: List[MatchReason]
    summary: str  # Human-readable summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relevance": round(self.relevance, 3),
            "summary": self.summary,
            "reasons": [
                {
                    "type": r.reason_type,
                    "description": r.description,
                    "confidence": round(r.confidence, 2),
                    "matched_text": r.matched_text,
                    "location": r.location
                }
                for r in self.reasons
            ]
        }


@dataclass
class VisualPreview:
    """Rich visual preview of a code match."""
    content: str
    line_start: int
    line_end: int
    highlight_lines: List[int] = field(default_factory=list)
    language: str = "text"
    truncated: bool = False
    total_lines: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "highlight_lines": self.highlight_lines,
            "language": self.language,
            "truncated": self.truncated,
            "total_lines": self.total_lines
        }


class ResultExplainer:
    """
    Analyzes search results to explain why they matched.
    """

    # File type to display language mapping
    LANGUAGE_MAP = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "markdown": "markdown",
        "json": "json",
        "yaml": "yaml",
        "toml": "toml",
        "shell": "bash",
        "rust": "rust",
        "go": "go",
        "sql": "sql",
        "html": "html",
        "css": "css",
    }

    def __init__(self):
        pass

    def explain_match(
        self,
        query: str,
        result_preview: str,
        result_path: str,
        chunk_name: Optional[str],
        chunk_type: str,
        relevance: float
    ) -> ExplainedResult:
        """
        Generate explanation for why a result matched a query.

        Args:
            query: The original search query
            result_preview: The content preview of the matched chunk
            result_path: Path to the matched file
            chunk_name: Name of the chunk (function/class name)
            chunk_type: Type of chunk (function, class, etc.)
            relevance: The relevance score (0-1)

        Returns:
            ExplainedResult with reasons and summary
        """
        reasons = []
        query_lower = query.lower()
        query_words = set(self._tokenize(query))

        # Check for exact matches in preview
        exact_matches = self._find_exact_matches(query_words, result_preview)
        for match, count in exact_matches:
            reasons.append(MatchReason(
                reason_type="exact",
                description=f"Contains \"{match}\"" + (f" ({count}x)" if count > 1 else ""),
                confidence=min(0.9, 0.5 + count * 0.1),
                matched_text=match,
                location="content"
            ))

        # Check for matches in filename/path
        filename = Path(result_path).name
        path_matches = self._find_exact_matches(query_words, filename)
        for match, count in path_matches:
            reasons.append(MatchReason(
                reason_type="filename",
                description=f"Filename contains \"{match}\"",
                confidence=0.85,
                matched_text=match,
                location="filename"
            ))

        # Check for matches in chunk name (function/class name)
        if chunk_name:
            name_matches = self._find_exact_matches(query_words, chunk_name)
            for match, count in name_matches:
                reasons.append(MatchReason(
                    reason_type="structure",
                    description=f"{chunk_type.title()} name contains \"{match}\"",
                    confidence=0.9,
                    matched_text=match,
                    location=f"{chunk_type} name"
                ))

        # Semantic match (when no exact matches explain the high relevance)
        exact_confidence = max([r.confidence for r in reasons]) if reasons else 0
        if relevance > 0.5 and (not reasons or exact_confidence < relevance - 0.1):
            reasons.append(MatchReason(
                reason_type="semantic",
                description="Semantically related to query",
                confidence=relevance,
                location="content"
            ))

        # Sort by confidence
        reasons.sort(key=lambda r: r.confidence, reverse=True)

        # Generate summary
        summary = self._generate_summary(reasons, relevance)

        return ExplainedResult(
            relevance=relevance,
            reasons=reasons[:5],  # Top 5 reasons
            summary=summary
        )

    def _tokenize(self, text: str) -> List[str]:
        """Extract meaningful tokens from text."""
        # Split on non-alphanumeric, filter short tokens
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text.lower())
        return [t for t in tokens if len(t) >= 2]

    def _find_exact_matches(
        self,
        query_words: set,
        text: str
    ) -> List[Tuple[str, int]]:
        """Find query words that appear in text."""
        matches = []
        text_lower = text.lower()

        for word in query_words:
            # Count occurrences (case-insensitive)
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            count = len(pattern.findall(text_lower))
            if count > 0:
                # Find original case version
                match = pattern.search(text)
                original = match.group(0) if match else word
                matches.append((original, count))

        return matches

    def _generate_summary(self, reasons: List[MatchReason], relevance: float) -> str:
        """Generate human-readable summary of match reasons."""
        if not reasons:
            return f"Matched with {relevance:.0%} relevance"

        # Categorize reasons
        exact = [r for r in reasons if r.reason_type == "exact"]
        filename = [r for r in reasons if r.reason_type == "filename"]
        structure = [r for r in reasons if r.reason_type == "structure"]
        semantic = [r for r in reasons if r.reason_type == "semantic"]

        parts = []

        if structure:
            parts.append(f"{structure[0].description}")
        elif filename:
            parts.append(f"{filename[0].description}")

        if exact:
            if len(exact) == 1:
                parts.append(f"contains \"{exact[0].matched_text}\"")
            else:
                words = [f"\"{r.matched_text}\"" for r in exact[:3]]
                parts.append(f"contains {', '.join(words)}")

        if semantic and not exact:
            parts.append("semantically related")

        if parts:
            return "; ".join(parts)
        return f"Matched with {relevance:.0%} relevance"


class VisualPreviewGenerator:
    """
    Generates rich visual code previews with highlighting.
    """

    # File extension to language mapping
    EXT_TO_LANG = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".sh": "bash",
        ".bash": "bash",
        ".rs": "rust",
        ".go": "go",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".ini": "ini",
        ".cfg": "ini",
    }

    def __init__(self, context_lines: int = 3, max_preview_lines: int = 20):
        self.context_lines = context_lines
        self.max_preview_lines = max_preview_lines

    def generate_preview(
        self,
        file_path: str,
        line_start: int,
        line_end: int,
        query: Optional[str] = None,
        highlight_matches: bool = True
    ) -> Optional[VisualPreview]:
        """
        Generate a visual preview of code with context and highlighting.

        Args:
            file_path: Path to the file
            line_start: Start line of the match (1-indexed)
            line_end: End line of the match (1-indexed)
            query: Optional query for highlighting matches
            highlight_matches: Whether to mark matched lines

        Returns:
            VisualPreview object or None if file can't be read
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            total_lines = len(lines)

            # Determine language
            language = self.EXT_TO_LANG.get(path.suffix.lower(), "text")

            # Calculate preview range with context
            preview_start = max(1, line_start - self.context_lines)
            preview_end = min(total_lines, line_end + self.context_lines)

            # Limit total lines
            if preview_end - preview_start + 1 > self.max_preview_lines:
                # Center on the match
                center = (line_start + line_end) // 2
                half = self.max_preview_lines // 2
                preview_start = max(1, center - half)
                preview_end = min(total_lines, preview_start + self.max_preview_lines - 1)

            # Extract lines (convert to 0-indexed)
            preview_lines = lines[preview_start - 1:preview_end]

            # Find lines to highlight (the actual match, not context)
            highlight_lines = list(range(line_start, line_end + 1))

            # If query provided, also highlight lines containing query terms
            if query and highlight_matches:
                query_words = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+', query.lower()))
                for i, line in enumerate(preview_lines, start=preview_start):
                    if i not in highlight_lines:
                        line_lower = line.lower()
                        if any(word in line_lower for word in query_words):
                            highlight_lines.append(i)

            # Format with line numbers
            formatted_lines = []
            max_line_num_width = len(str(preview_end))

            for i, line in enumerate(preview_lines, start=preview_start):
                line_num = str(i).rjust(max_line_num_width)
                marker = "→" if i in highlight_lines else " "
                formatted_lines.append(f"{line_num} {marker}│ {line}")

            # Check if truncated
            truncated = (
                preview_start > 1 or
                preview_end < total_lines
            )

            return VisualPreview(
                content="\n".join(formatted_lines),
                line_start=preview_start,
                line_end=preview_end,
                highlight_lines=sorted(set(highlight_lines)),
                language=language,
                truncated=truncated,
                total_lines=total_lines
            )

        except Exception as e:
            logger.warning(f"Failed to generate preview for {file_path}: {e}")
            return None

    def generate_compact_preview(
        self,
        content_preview: str,
        file_path: str,
        line_start: int,
        line_end: int
    ) -> Dict[str, Any]:
        """
        Generate a compact preview from pre-stored content preview.
        Used when full file access isn't needed.

        Args:
            content_preview: Pre-stored preview text
            file_path: Path to file (for language detection)
            line_start: Start line number
            line_end: End line number

        Returns:
            Dict with preview information
        """
        path = Path(file_path)
        language = self.EXT_TO_LANG.get(path.suffix.lower(), "text")

        # Format with line numbers
        lines = content_preview.split("\n")
        max_line_num_width = len(str(line_end))

        formatted_lines = []
        for i, line in enumerate(lines, start=line_start):
            line_num = str(i).rjust(max_line_num_width)
            formatted_lines.append(f"{line_num} │ {line}")

        return {
            "content": "\n".join(formatted_lines),
            "line_start": line_start,
            "line_end": line_start + len(lines) - 1,
            "language": language,
            "truncated": content_preview.endswith("...")
        }
