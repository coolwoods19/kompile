from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Source:
    id: str
    platform: Literal["claude", "chatgpt", "claude_code", "article", "youtube", "manual"]
    title: str
    date: str          # ISO date string e.g. "2026-03-15"
    content: str       # full raw text
    url: str | None = None  # original URL for article/youtube sources
    metadata: dict = field(default_factory=dict)


@dataclass
class FilterResult:
    source_id: str
    keep: bool
    topics: list[str]
    summary: str


@dataclass
class Claim:
    text: str
    type: Literal["fact", "analysis", "framework", "opinion"]
    confidence: Literal["stated", "inferred"]


@dataclass
class SourceSummary:
    source_id: str
    platform: str
    title: str
    date: str
    claims: list[Claim]
    frameworks: list[str]
    key_terms: list[str]


@dataclass
class ArticleSource:
    platform: str
    title: str
    date: str


@dataclass
class Article:
    id: str
    title: str
    sources: list[ArticleSource]
    content: str       # markdown with [Source]/[Synthesis] markers and citations
    concepts: list[str]
    backlinks: list[str]


@dataclass
class Concept:
    name: str
    appears_in: list[str]   # domain names
    note: str


@dataclass
class Insight:
    text: str
    sources: list[str]   # source ids or titles


@dataclass
class Gap:
    gap: str
    detail: str


@dataclass
class Subtopic:
    name: str
    article_ids: list[str]


@dataclass
class Domain:
    name: str
    subtopics: list[Subtopic]


@dataclass
class WikiCompilation:
    """Result of compiling one Deep Domain."""
    title: str
    domain_name: str = ""  # the domain this compilation is scoped to
    domains: list[Domain] = field(default_factory=list)
    articles: list[Article] = field(default_factory=list)
    cross_topic_concepts: list[Concept] = field(default_factory=list)
    insights: list[Insight] = field(default_factory=list)
    suggested_gaps: list[Gap] = field(default_factory=list)


@dataclass
class ActiveNote:
    """Result of compiling one Active Topic (2-4 sources → single synthesized note)."""
    topic: str
    sources: list[ArticleSource]
    note: str           # markdown with [Source]/[Synthesis] markers, ⚠ Conflict flags
    concepts: list[str]
    related_domains: list[str] = field(default_factory=list)  # populated by cross-domain pass


@dataclass
class SurfaceNote:
    """Archive entry for Surface topics (1 source) — Haiku summary only, no compilation."""
    source_id: str
    title: str
    platform: str
    date: str
    summary: str        # one-line Haiku summary from filter step
    topics: list[str]


@dataclass
class TieredWiki:
    """Top-level container for the full tiered knowledge profile."""
    deep_domains: list[WikiCompilation]
    active_notes: list[ActiveNote]
    surface_notes: list[SurfaceNote]
    cross_topic_concepts: list[Concept] = field(default_factory=list)
    insights: list[Insight] = field(default_factory=list)
    suggested_gaps: list[Gap] = field(default_factory=list)
