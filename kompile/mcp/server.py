"""KOMPILE MCP Server — exposes the knowledge base to Claude via 5 tools.

Tools:
  get_index             — all article/note titles + summaries + concept tags + tier indicators
  get_article           — full content of one article or active note
  get_insights          — cross-domain insights + suggested gaps
  search                — keyword search across all articles, notes, and surface entries
  get_knowledge_profile — knowledge shape: domains/topics with depth indicators and tier classification

IMPORTANT — Article ID uniqueness:
  Article IDs are globally unique across wiki/deep/**/*.md and wiki/active/*.md.
  get_article uses first-match glob across both paths. This relies on the compile step
  enforcing uniqueness (see compile.py). If an ID is not found, a fuzzy match is attempted.

KOMPILE is CONTEXT, not constraint:
  These tools provide Claude with the user's personal research context.
  Claude should use this to build on the user's existing knowledge and frameworks,
  combining it with its own knowledge and web search — not be restricted to only
  answering from the knowledge base.

Run:
  python -m kompile.mcp.server
  python -m kompile.mcp.server --wiki /path/to/wiki
"""
from __future__ import annotations

import re
from pathlib import Path

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from kompile.config import load_config


def _load_wiki_dir() -> Path:
    cfg = load_config()
    wiki = Path(cfg["paths"]["wiki"])
    return wiki


server = Server("kompile")

# Cache index in memory — don't re-read every query
_wiki_dir: Path | None = None
_index_cache: str | None = None


def _get_wiki_dir() -> Path:
    global _wiki_dir
    if _wiki_dir is None:
        _wiki_dir = _load_wiki_dir()
    return _wiki_dir


def _get_index() -> str:
    global _index_cache
    if _index_cache is None:
        p = _get_wiki_dir() / "index.md"
        _index_cache = (
            p.read_text(encoding="utf-8")
            if p.exists()
            else "_Knowledge base not yet compiled. Run `kompile compile`._"
        )
    return _index_cache


def _find_article(article_id: str, wiki_dir: Path) -> Path | None:
    """Search wiki/deep/**/*.md and wiki/active/*.md for a matching article ID.

    Article IDs are globally unique across the wiki — first match wins.
    """
    # Exact match in deep/
    for candidate in (wiki_dir / "deep").glob(f"**/{article_id}.md"):
        return candidate

    # Exact match in active/
    active_candidate = wiki_dir / "active" / f"{article_id}.md"
    if active_candidate.exists():
        return active_candidate

    return None


def _fuzzy_find_articles(article_id: str, wiki_dir: Path) -> list[str]:
    """Return article IDs (stems) that contain the query as a substring."""
    matches = []
    query = article_id.lower()
    for candidate in (wiki_dir / "deep").glob("**/*.md"):
        if query in candidate.stem.lower():
            matches.append(candidate.stem)
    for candidate in (wiki_dir / "active").glob("*.md"):
        if query in candidate.stem.lower():
            matches.append(candidate.stem)
    return matches


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_index",
            description=(
                "Returns the index of the user's personal knowledge base: "
                "article and note titles, one-line summaries, concept tags, and tier indicators "
                "(⚡ Deep Domain | 🎯 Active Topic | ▪ Surface Note). "
                "Call this first to understand the user's knowledge landscape and decide which "
                "articles are relevant to the question. "
                "This is CONTEXT for richer, more personalised answers — not the only source of truth. "
                "Typical token cost: 300-500 tokens."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_article",
            description=(
                "Returns the full content of one article or active note from the knowledge base, "
                "including source citations ([Source: platform — 'title' (date)]), "
                "[Source]/[Synthesis] origin markers, "
                "and ⚠ Conflict flags where sources disagreed. "
                "Use this to understand the user's existing analysis on a topic before "
                "adding new information or perspectives. "
                "Typical token cost: 500-800 tokens."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "The article slug ID from the index (e.g. 'cuda-moat', 'product-strategy')",
                    }
                },
                "required": ["article_id"],
            },
        ),
        types.Tool(
            name="get_insights",
            description=(
                "Returns cross-domain insights (connections discovered across multiple sources and topics) "
                "and suggested knowledge gaps. Especially useful for questions about relationships between "
                "topics, or to understand what the user may be missing. "
                "Typical token cost: 200-300 tokens."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="search",
            description=(
                "Keyword search across all articles, active notes, and surface entries in the knowledge base. "
                "Returns matching paragraphs with their article titles. "
                "Use when you need to find specific claims or terms rather than loading whole articles. "
                "Typical token cost: 200-500 tokens."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search terms to look for across the knowledge base",
                    }
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_knowledge_profile",
            description=(
                "Returns the user's overall knowledge shape — which domains are Deep (5+ sources, "
                "full articles), which are Active (2-4 sources, synthesised note), and which are "
                "Surface (1 source, archived). "
                "Use to calibrate response depth: go deeper on topics the user knows well, provide "
                "more foundations on topics they've barely explored. "
                "Typical token cost: 200-400 tokens."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    wiki_dir = _get_wiki_dir()

    if name == "get_index":
        content = _get_index()
        return [types.TextContent(type="text", text=content)]

    elif name == "get_article":
        article_id = arguments.get("article_id", "").strip()
        if not article_id:
            return [types.TextContent(type="text", text="Error: article_id is required.")]

        art_file = _find_article(article_id, wiki_dir)
        if art_file is None:
            matches = _fuzzy_find_articles(article_id, wiki_dir)
            if matches:
                return [types.TextContent(
                    type="text",
                    text=f"Article '{article_id}' not found. Did you mean one of: {', '.join(matches[:5])}?"
                )]
            return [types.TextContent(type="text", text=f"Article '{article_id}' not found.")]
        return [types.TextContent(type="text", text=art_file.read_text(encoding="utf-8"))]

    elif name == "get_insights":
        parts = []
        insights_file = wiki_dir / "insights.md"
        gaps_file = wiki_dir / "gaps.md"
        if insights_file.exists():
            parts.append(insights_file.read_text(encoding="utf-8"))
        if gaps_file.exists():
            parts.append(gaps_file.read_text(encoding="utf-8"))
        if not parts:
            return [types.TextContent(type="text", text="_No insights or gaps compiled yet._")]
        return [types.TextContent(type="text", text="\n\n---\n\n".join(parts))]

    elif name == "search":
        query = arguments.get("query", "").strip().lower()
        if not query:
            return [types.TextContent(type="text", text="Error: query is required.")]

        results = []
        terms = query.split()

        # Search all markdown files across deep/, active/, surface/
        search_dirs = ["deep", "active", "surface"]
        all_files: list[Path] = []
        for d in search_dirs:
            dpath = wiki_dir / d
            if dpath.exists():
                all_files.extend(sorted(dpath.glob("**/*.md")))

        for art_file in all_files:
            content = art_file.read_text(encoding="utf-8")
            # Strip YAML frontmatter
            body = content
            if content.startswith("---"):
                parts = content.split("---", 2)
                body = parts[2] if len(parts) >= 3 else content

            matching_paras = []
            for para in body.split("\n\n"):
                para_lower = para.lower()
                if all(t in para_lower for t in terms):
                    clean = para.strip()
                    if len(clean) > 30:
                        matching_paras.append(clean[:400])

            if matching_paras:
                title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
                title = title_match.group(1) if title_match else art_file.stem
                results.append(f"### {title}\n\n" + "\n\n".join(matching_paras[:3]))

        if not results:
            return [types.TextContent(type="text", text=f"No matches found for '{query}'.")]
        return [types.TextContent(type="text", text="\n\n---\n\n".join(results[:10]))]

    elif name == "get_knowledge_profile":
        profile_file = wiki_dir / "profile.md"
        if not profile_file.exists():
            return [types.TextContent(type="text", text="_Knowledge profile not compiled yet._")]
        return [types.TextContent(type="text", text=profile_file.read_text(encoding="utf-8"))]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="KOMPILE MCP Server")
    parser.add_argument("--wiki", default=None, help="Path to wiki directory")
    args, _ = parser.parse_known_args()

    global _wiki_dir
    if args.wiki:
        _wiki_dir = Path(args.wiki)

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
