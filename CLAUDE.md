# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

KOMPILE is a personal knowledge compiler. It ingests AI conversation exports (Claude, ChatGPT), Claude Code project files, web articles, YouTube transcripts, and raw notes, then runs an LLM pipeline to produce a tiered structured markdown wiki with source citations and contradiction flags. The wiki is exposed to Claude Desktop via a local MCP server.

## Commands

```bash
# Install for development
pip install -e .

# CLI usage
kompile ingest <path>          # Parse files, URLs, or directories into raw/ (auto-detects type)
kompile ingest <path> --type claude|chatgpt|claude_code|article|youtube|raw
kompile filter                 # Run Haiku filter + classify topics into depth tiers
kompile compile                # Full tiered pipeline → wiki/
kompile compile --incremental  # Only process new sources since last compile
kompile status                 # Show pipeline progress

# MCP server
python -m kompile.mcp.server
python -m kompile.mcp.server --wiki /path/to/wiki
```

There is no test suite. Manual testing steps are in `CLAUDE-CODE-INSTRUCTIONS.md`.

## Architecture

The pipeline has five stages:

1. **Ingest** ([kompile/ingest/](kompile/ingest/)) — parsers for each source type produce `Source` dataclass objects. `router.py` auto-detects type from path/URL. Claude.ai exports are ZIPs with JSON conversations; ChatGPT exports are ZIPs with `conversations.json`; Claude Code dirs read `.md` files; `article.py` fetches URLs via trafilatura; `youtube.py` fetches transcripts via youtube-transcript-api; raw accepts `.md`/`.txt`.

2. **Filter** ([kompile/compiler/filter.py](kompile/compiler/filter.py)) — calls Haiku per source to decide keep/discard and extract topic tags (~5K tokens/call).

3. **Classify** ([kompile/compiler/classify.py](kompile/compiler/classify.py)) — groups kept sources by topic and assigns depth tiers (no API calls):
   - **deep** — 5+ sources on a topic → full article compilation
   - **active** — 2–4 sources → single synthesized note
   - **surface** — 1 source → archived with Haiku filter summary only

4. **Summarize** ([kompile/compiler/summarize.py](kompile/compiler/summarize.py)) — calls Sonnet per deep/active source to extract structured claims, frameworks, and key terms as `SourceSummary`. Surface sources are skipped.

5. **Compile** ([kompile/compiler/compile.py](kompile/compiler/compile.py)) — three compilation passes:
   - `compile_wiki_domain()` — one Sonnet call per deep domain → `WikiCompilation` with full articles
   - `compile_active_topic()` — one Sonnet call per active topic → `ActiveNote`
   - `compile_cross_domain()` — one Sonnet call on a lightweight index (<10K tokens) to find cross-topic concepts, insights, and gaps
   - Writer ([kompile/compiler/writer.py](kompile/compiler/writer.py)) renders everything to `wiki/deep/`, `wiki/active/`, `wiki/surface/`

**State persistence**: `.kompile_state.json` in the working directory tracks sources, filter results, tier classifications, and summaries. This is how `--incremental` knows what's new.

**MCP server** ([kompile/mcp/server.py](kompile/mcp/server.py)) — reads from `wiki/` at runtime. Exposes 5 tools: `get_index`, `get_article`, `get_insights`, `search`, `get_knowledge_map`. The index is cached in memory; articles are read from disk on demand.

**Config** ([kompile/config.py](kompile/config.py)) — loads `kompile.yaml` merged over defaults. API key comes from `api_key:` in the YAML or `ANTHROPIC_API_KEY` env var.

## Data Models ([kompile/models.py](kompile/models.py))

```
Source
  → FilterResult                         (filter step)
  → SourceSummary (claims, frameworks)   (summarize step — deep/active only)
  → WikiCompilation (articles, domains)  (deep compile)
  → ActiveNote (note, concepts)          (active compile)
  → SurfaceNote (summary only)           (no compile)

TieredWiki                               (top-level output container)
  deep_domains: list[WikiCompilation]
  active_notes: list[ActiveNote]
  surface_notes: list[SurfaceNote]
  cross_topic_concepts, insights, suggested_gaps
```

Article IDs must be globally unique across `wiki/deep/**/*.md` and `wiki/active/*.md` — the MCP `get_article` tool uses first-match glob and relies on this invariant. `compile_wiki_domain()` enforces uniqueness by appending `-{domain_slug}` on collision.

## Design Constraints

- Never exceed 50% of context window in any single API call (chunk if summaries exceed ~80K tokens / 320K chars).
- Every article claim must have a source citation — no citation = hallucination risk.
- Contradictions are flagged with `⚠ Conflict:`, never silently resolved.
- Gaps are phrased as "may be intentional or an area to explore."
- Model routing: Haiku for filtering/tagging (cheap), Sonnet for summarization and compilation (smart). All model strings are configurable in `kompile.yaml`.
- All output is local markdown in `wiki/` — no database, no cloud.

## Demo

[demo/](demo/) is a React/Vite app with a hardcoded AI infrastructure knowledge base (no backend). It has Overview, Articles, and Q&A tabs. The Q&A tab calls the Claude API directly with the KB as context.
