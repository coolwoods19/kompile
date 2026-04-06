from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Source:
    id: str
    platform: Literal["claude", "chatgpt", "claude_code", "manual"]
    title: str
    date: str          # ISO date string e.g. "2026-03-15"
    content: str       # full raw text
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
    title: str
    domains: list[Domain]
    articles: list[Article]
    cross_topic_concepts: list[Concept]
    insights: list[Insight]
    suggested_gaps: list[Gap]
