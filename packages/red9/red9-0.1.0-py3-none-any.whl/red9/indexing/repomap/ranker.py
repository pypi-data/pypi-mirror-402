"""RepoMap ranker module - PageRank-based file ranking.

Uses NetworkX PageRank algorithm to rank files based on their importance
in the codebase. Files that are referenced more frequently are ranked higher.

Based on aider's get_ranked_tags implementation.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from red9.logging import get_logger

if TYPE_CHECKING:
    from .tags import Tag

logger = get_logger(__name__)


@dataclass
class RankedTag:
    """A tag with its PageRank score.

    Attributes:
        name: Symbol name.
        rel_fname: Relative filename.
        line: Line number.
        score: PageRank score.
        kind: Tag kind (def/ref).
        category: Symbol category.
    """

    name: str
    rel_fname: str
    line: int
    score: float
    kind: str = "def"
    category: str = ""


class TagRanker:
    """Ranks files and symbols using PageRank algorithm.

    Builds a graph where:
    - Nodes are (file, identifier) pairs
    - Edges represent "uses" relationships (referencer -> definition)
    - Edge weights are adjusted based on importance heuristics:
      - Higher weight for mentioned identifiers
      - Higher weight for long descriptive names
      - Lower weight for private symbols (starting with _)
      - Lower weight for common/generic names
    """

    def __init__(
        self,
        chat_fnames: set[str] | None = None,
        mentioned_fnames: set[str] | None = None,
        mentioned_idents: set[str] | None = None,
    ) -> None:
        """Initialize tag ranker.

        Args:
            chat_fnames: Files currently in the chat context.
            mentioned_fnames: Files mentioned by user.
            mentioned_idents: Identifiers mentioned by user.
        """
        self.chat_fnames = chat_fnames or set()
        self.mentioned_fnames = mentioned_fnames or set()
        self.mentioned_idents = mentioned_idents or set()

    def rank_tags(
        self,
        tags: list[Tag],
    ) -> list[RankedTag]:
        """Rank tags using PageRank algorithm.

        Args:
            tags: List of Tag objects from all files.

        Returns:
            List of RankedTag objects sorted by score (descending).
        """
        try:
            import networkx as nx
        except ImportError:
            logger.warning("networkx not available, using simple ranking")
            return self._rank_simple(tags)

        # Build defines and references maps
        defines: dict[str, set[str]] = defaultdict(set)  # name -> {files}
        references: dict[str, list[str]] = defaultdict(list)  # name -> [files]

        for tag in tags:
            if tag.kind == "def":
                defines[tag.name].add(tag.rel_fname)
            elif tag.kind == "ref":
                references[tag.name].append(tag.rel_fname)

        # Build personalization vector for PageRank
        personalization: dict[tuple[str, str], float] = {}

        # Boost files in chat context
        for fname in self.chat_fnames:
            for tag in tags:
                if tag.rel_fname == fname and tag.kind == "def":
                    personalization[(fname, tag.name)] = 100.0

        # Boost files with mentioned identifiers
        for ident in self.mentioned_idents:
            if ident in defines:
                for fname in defines[ident]:
                    personalization[(fname, ident)] = personalization.get((fname, ident), 0) + 100.0

        # Boost mentioned files
        for fname in self.mentioned_fnames:
            for tag in tags:
                if tag.rel_fname == fname and tag.kind == "def":
                    key = (fname, tag.name)
                    personalization[key] = personalization.get(key, 0) + 100.0

        # Build the graph
        G = nx.MultiDiGraph()

        # Add edges from referencer files to definition files
        for name, ref_files in references.items():
            if name not in defines:
                continue

            def_files = defines[name]
            num_refs = len(ref_files)

            for ref_file in ref_files:
                for def_file in def_files:
                    # Skip self-references
                    if ref_file == def_file:
                        continue

                    # Calculate edge weight
                    mul = 1.0

                    # Boost mentioned identifiers
                    if name in self.mentioned_idents:
                        mul *= 10.0

                    # Boost long descriptive names (likely meaningful)
                    if len(name) >= 8 and any(c.isupper() for c in name[1:]):
                        mul *= 10.0

                    # Reduce private symbols
                    if name.startswith("_"):
                        mul *= 0.1

                    # Reduce common/generic names (5+ definitions)
                    if len(def_files) >= 5:
                        mul *= 0.1

                    # Boost if referencer is in chat
                    if ref_file in self.chat_fnames:
                        mul *= 50.0

                    # Final weight
                    weight = mul * math.sqrt(num_refs)

                    # Add edge
                    G.add_edge(
                        (ref_file, name),
                        (def_file, name),
                        weight=weight,
                    )

        # Run PageRank
        if not G.nodes():
            return self._rank_simple(tags)

        try:
            # Normalize personalization
            if personalization:
                total = sum(personalization.values())
                personalization = {k: v / total for k, v in personalization.items()}
                # Only use nodes that exist in the graph
                personalization = {k: v for k, v in personalization.items() if k in G.nodes()}
                if not personalization:
                    personalization = None

            ranked = nx.pagerank(
                G,
                weight="weight",
                personalization=personalization,
            )
        except Exception as e:
            logger.warning(f"PageRank failed: {e}")
            return self._rank_simple(tags)

        # Distribute rank to definitions
        ranked_tags: dict[tuple[str, str, int], float] = {}  # (fname, name, line) -> score

        for (fname, name), score in ranked.items():
            # Find the definition tag
            for tag in tags:
                if tag.rel_fname == fname and tag.name == name and tag.kind == "def":
                    key = (fname, name, tag.line)
                    ranked_tags[key] = ranked_tags.get(key, 0) + score

        # Convert to RankedTag objects
        result: list[RankedTag] = []
        for (fname, name, line), score in ranked_tags.items():
            # Find the original tag for category
            category = ""
            for tag in tags:
                if (
                    tag.rel_fname == fname
                    and tag.name == name
                    and tag.line == line
                    and tag.kind == "def"
                ):
                    category = tag.category
                    break

            result.append(
                RankedTag(
                    name=name,
                    rel_fname=fname,
                    line=line,
                    score=score,
                    kind="def",
                    category=category,
                )
            )

        # Sort by score descending
        result.sort(key=lambda t: t.score, reverse=True)

        return result

    def _rank_simple(self, tags: list[Tag]) -> list[RankedTag]:
        """Simple ranking fallback (by reference count).

        Args:
            tags: List of Tag objects.

        Returns:
            List of RankedTag objects.
        """
        # Count references to each definition
        ref_counts: dict[str, int] = defaultdict(int)
        for tag in tags:
            if tag.kind == "ref":
                ref_counts[tag.name] += 1

        # Rank definitions by reference count
        result: list[RankedTag] = []
        for tag in tags:
            if tag.kind == "def":
                score = ref_counts.get(tag.name, 0)

                # Boost mentioned identifiers
                if tag.name in self.mentioned_idents:
                    score += 100

                # Boost chat files
                if tag.rel_fname in self.chat_fnames:
                    score += 50

                # Boost mentioned files
                if tag.rel_fname in self.mentioned_fnames:
                    score += 50

                result.append(
                    RankedTag(
                        name=tag.name,
                        rel_fname=tag.rel_fname,
                        line=tag.line,
                        score=float(score),
                        kind=tag.kind,
                        category=tag.category,
                    )
                )

        # Sort by score descending
        result.sort(key=lambda t: t.score, reverse=True)

        return result


def select_tags_for_budget(
    ranked_tags: list[RankedTag],
    max_tokens: int,
    token_counter: Any = None,
) -> list[RankedTag]:
    """Select tags that fit within a token budget using binary search.

    Args:
        ranked_tags: List of RankedTag objects sorted by score.
        max_tokens: Maximum tokens allowed.
        token_counter: Optional callable to count tokens (default: estimate).

    Returns:
        List of RankedTag objects that fit within budget.
    """
    if not ranked_tags:
        return []

    def estimate_tokens(text: str) -> int:
        """Estimate token count (rough approximation)."""
        if token_counter:
            return token_counter(text)
        # Rough estimate: 4 characters per token
        return len(text) // 4

    def render_tags(tags: list[RankedTag]) -> str:
        """Render tags as text for token counting."""
        lines = []
        current_file = ""
        for tag in tags:
            if tag.rel_fname != current_file:
                current_file = tag.rel_fname
                lines.append(f"\n{current_file}:")
            category_str = f"[{tag.category}] " if tag.category else ""
            lines.append(f"  {tag.line}: {category_str}{tag.name}")
        return "\n".join(lines)

    # Binary search for optimal subset
    lo = 0
    hi = len(ranked_tags)
    best_count = 0

    while lo < hi:
        mid = (lo + hi + 1) // 2
        subset = ranked_tags[:mid]
        text = render_tags(subset)
        tokens = estimate_tokens(text)

        if tokens <= max_tokens:
            best_count = mid
            lo = mid
        else:
            hi = mid - 1

    return ranked_tags[:best_count]
