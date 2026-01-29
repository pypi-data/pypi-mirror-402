"""RepoMap tags module - Tree-sitter based AST tag extraction.

Extracts definitions (class, function, method) and references from source code
using tree-sitter for language-agnostic parsing.

Based on aider's repomap.py get_tags implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from red9.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


@dataclass
class Tag:
    """Represents a code symbol (definition or reference).

    Attributes:
        name: Symbol name (e.g., function name, class name).
        kind: Tag kind - "def" for definition, "ref" for reference.
        line: Line number (1-indexed).
        rel_fname: Relative filename from project root.
        category: Optional category (e.g., "class", "function", "method").
    """

    name: str
    kind: str  # "def" or "ref"
    line: int
    rel_fname: str
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "kind": self.kind,
            "line": self.line,
            "rel_fname": self.rel_fname,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tag:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            kind=data["kind"],
            line=data["line"],
            rel_fname=data["rel_fname"],
            category=data.get("category", ""),
        )


class TagExtractor:
    """Extracts AST tags from source files using tree-sitter.

    Uses grep_ast library for tree-sitter integration and TreeContext rendering.
    Falls back to pygments-based token extraction when tree-sitter doesn't find
    references.
    """

    # Supported file extensions mapped to languages
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".rs": "rust",
        ".go": "go",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "c_sharp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".R": "r",
        ".lua": "lua",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".md": "markdown",
    }

    def __init__(self, project_root: Path) -> None:
        """Initialize tag extractor.

        Args:
            project_root: Project root directory.
        """
        self.project_root = project_root
        self._grep_ast_available = self._check_grep_ast()

    def _check_grep_ast(self) -> bool:
        """Check if grep_ast is available."""
        try:
            from grep_ast import filename_to_lang

            return True
        except ImportError:
            logger.warning("grep_ast not available, using fallback extraction")
            return False

    def get_language(self, filepath: Path) -> str | None:
        """Get language for a file based on extension.

        Args:
            filepath: Path to the file.

        Returns:
            Language string or None if unsupported.
        """
        if self._grep_ast_available:
            try:
                from grep_ast import filename_to_lang

                lang = filename_to_lang(str(filepath))
                if lang:
                    return lang
            except Exception:
                pass

        # Fallback to extension map
        suffix = filepath.suffix.lower()
        return self.LANGUAGE_MAP.get(suffix)

    def extract_tags(self, filepath: Path) -> list[Tag]:
        """Extract tags from a source file.

        Args:
            filepath: Path to the source file.

        Returns:
            List of Tag objects (definitions and references).
        """
        if not filepath.exists():
            return []

        # Get relative path
        try:
            rel_fname = str(filepath.relative_to(self.project_root))
        except ValueError:
            rel_fname = str(filepath)

        # Determine language
        lang = self.get_language(filepath)
        if not lang:
            return []

        # Try tree-sitter extraction
        if self._grep_ast_available:
            try:
                tags = self._extract_with_tree_sitter(filepath, rel_fname, lang)
                if tags:
                    return tags
            except Exception as e:
                logger.debug(f"Tree-sitter extraction failed for {filepath}: {e}")

        # Fallback to simple extraction
        return self._extract_fallback(filepath, rel_fname, lang)

    def _extract_with_tree_sitter(self, filepath: Path, rel_fname: str, lang: str) -> list[Tag]:
        """Extract tags using tree-sitter via grep_ast.

        Args:
            filepath: Path to the source file.
            rel_fname: Relative filename.
            lang: Language identifier.

        Returns:
            List of Tag objects.
        """
        from grep_ast.parsers import get_parser, get_scm_fname

        # Read file content
        try:
            code = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.debug(f"Failed to read {filepath}: {e}")
            return []

        # Get parser and query
        try:
            parser = get_parser(lang)
            scm_fname = get_scm_fname(lang)
            if not scm_fname:
                return []
        except Exception as e:
            logger.debug(f"No parser/query for {lang}: {e}")
            return []

        # Parse the code
        try:
            tree = parser.parse(bytes(code, "utf-8"))
        except Exception as e:
            logger.debug(f"Parse failed for {filepath}: {e}")
            return []

        # Load and run query
        try:
            # Get query text
            try:
                query_text = Path(scm_fname).read_text(encoding="utf-8")
            except Exception:
                return []

            # Try to get language from the parser
            query = parser.language.query(query_text)
            captures = query.captures(tree.root_node)
        except Exception as e:
            logger.debug(f"Query failed for {filepath}: {e}")
            return []

        # Process captures into tags
        tags: list[Tag] = []
        saw_defs: set[str] = set()
        saw_refs: set[str] = set()

        for node, capture_name in captures:
            # Parse capture name: name.definition.class, name.reference.call, etc.
            parts = capture_name.split(".")
            if len(parts) < 2:
                continue

            # Get the identifier name
            name = node.text.decode("utf-8") if node.text else ""
            if not name:
                continue

            # Determine if definition or reference
            if "definition" in capture_name or capture_name.startswith("name.definition"):
                kind = "def"
                key = (name, node.start_point[0])
                if key in saw_defs:
                    continue
                saw_defs.add(key)

                # Get category from capture name
                category = ""
                if len(parts) >= 3:
                    category = parts[2]  # e.g., "class", "function", "method"

                tags.append(
                    Tag(
                        name=name,
                        kind=kind,
                        line=node.start_point[0] + 1,  # 1-indexed
                        rel_fname=rel_fname,
                        category=category,
                    )
                )

            elif "reference" in capture_name or capture_name.startswith("name.reference"):
                kind = "ref"
                key = (name, node.start_point[0])
                if key in saw_refs:
                    continue
                saw_refs.add(key)

                tags.append(
                    Tag(
                        name=name,
                        kind=kind,
                        line=node.start_point[0] + 1,
                        rel_fname=rel_fname,
                        category="",
                    )
                )

        # If no references found, use pygments fallback for references
        if not any(t.kind == "ref" for t in tags):
            ref_tags = self._extract_refs_with_pygments(filepath, rel_fname, lang, saw_defs)
            tags.extend(ref_tags)

        return tags

    def _extract_refs_with_pygments(
        self,
        filepath: Path,
        rel_fname: str,
        lang: str,
        known_defs: set[tuple[str, int]],
    ) -> list[Tag]:
        """Extract references using pygments lexer as fallback.

        Args:
            filepath: Path to the source file.
            rel_fname: Relative filename.
            lang: Language identifier.
            known_defs: Set of known definitions to exclude.

        Returns:
            List of reference Tag objects.
        """
        try:
            from pygments import lex
            from pygments.lexers import get_lexer_for_filename
            from pygments.token import Token
        except ImportError:
            return []

        try:
            code = filepath.read_text(encoding="utf-8", errors="replace")
            lexer = get_lexer_for_filename(str(filepath))
        except Exception:
            return []

        tags: list[Tag] = []
        seen: set[str] = set()
        line_num = 1

        for token_type, token_value in lex(code, lexer):
            # Count newlines in token
            if "\n" in token_value:
                line_num += token_value.count("\n")
                continue

            # Check if this is a name token
            if token_type in (Token.Name, Token.Name.Other, Token.Name.Function):
                # Skip if it's a known definition at this line
                if (token_value, line_num - 1) in known_defs:
                    continue

                # Skip if we've seen this name as a reference
                if token_value in seen:
                    continue

                seen.add(token_value)
                tags.append(
                    Tag(
                        name=token_value,
                        kind="ref",
                        line=line_num,
                        rel_fname=rel_fname,
                        category="",
                    )
                )

        return tags

    def _extract_fallback(self, filepath: Path, rel_fname: str, lang: str) -> list[Tag]:
        """Simple fallback extraction using regex patterns.

        Args:
            filepath: Path to the source file.
            rel_fname: Relative filename.
            lang: Language identifier.

        Returns:
            List of Tag objects.
        """
        import re

        try:
            code = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        tags: list[Tag] = []

        # Language-specific patterns for definitions
        patterns: dict[str, list[tuple[str, str]]] = {
            "python": [
                (r"^\s*class\s+(\w+)", "class"),
                (r"^\s*def\s+(\w+)", "function"),
                (r"^\s*async\s+def\s+(\w+)", "function"),
            ],
            "javascript": [
                (r"^\s*class\s+(\w+)", "class"),
                (r"^\s*function\s+(\w+)", "function"),
                (r"^\s*const\s+(\w+)\s*=\s*(?:async\s*)?\(", "function"),
                (r"^\s*let\s+(\w+)\s*=\s*(?:async\s*)?\(", "function"),
            ],
            "typescript": [
                (r"^\s*class\s+(\w+)", "class"),
                (r"^\s*interface\s+(\w+)", "interface"),
                (r"^\s*type\s+(\w+)", "type"),
                (r"^\s*function\s+(\w+)", "function"),
                (r"^\s*const\s+(\w+)\s*=\s*(?:async\s*)?\(", "function"),
            ],
            "go": [
                (r"^\s*func\s+(\w+)", "function"),
                (r"^\s*func\s+\([^)]+\)\s+(\w+)", "method"),
                (r"^\s*type\s+(\w+)\s+struct", "struct"),
                (r"^\s*type\s+(\w+)\s+interface", "interface"),
            ],
            "rust": [
                (r"^\s*fn\s+(\w+)", "function"),
                (r"^\s*struct\s+(\w+)", "struct"),
                (r"^\s*enum\s+(\w+)", "enum"),
                (r"^\s*trait\s+(\w+)", "trait"),
                (r"^\s*impl\s+(\w+)", "impl"),
            ],
        }

        # Get patterns for language (or use generic)
        lang_patterns = patterns.get(lang, patterns.get("python", []))

        lines = code.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pattern, category in lang_patterns:
                match = re.match(pattern, line)
                if match:
                    name = match.group(1)
                    tags.append(
                        Tag(
                            name=name,
                            kind="def",
                            line=line_num,
                            rel_fname=rel_fname,
                            category=category,
                        )
                    )

        return tags


def get_tree_context(filepath: Path, lines_of_interest: set[int]) -> str | None:
    """Get formatted code context using grep_ast TreeContext.

    Args:
        filepath: Path to the source file.
        lines_of_interest: Set of line numbers to highlight.

    Returns:
        Formatted code string with context, or None on error.
    """
    try:
        from grep_ast import TreeContext

        code = filepath.read_text(encoding="utf-8", errors="replace")
        tc = TreeContext(
            filename=str(filepath),
            code=code,
            color=False,
            line_number=True,
            child_context=True,
            last_line=True,
            margin=0,
            mark_lois=False,
            header_max=10,
            show_top_of_file_parent_scope=True,
        )

        # Add lines of interest
        for line in lines_of_interest:
            tc.add_lines_of_interest([line])

        # Format output
        output = tc.format()
        return output if output else None

    except ImportError:
        logger.debug("grep_ast not available for TreeContext")
        return None
    except Exception as e:
        logger.debug(f"TreeContext failed for {filepath}: {e}")
        return None
