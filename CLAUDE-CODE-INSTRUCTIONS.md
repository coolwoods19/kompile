# KOMPILE — Claude Code Build Instructions

## Context

Read `kompile-product-doc.md` first. It contains the full product spec including architecture, context window strategy, model routing, and trust design. This file tells you what to build and in what order.

## What You're Building

KOMPILE is a personal knowledge compiler. It takes AI conversation exports (Claude, ChatGPT, Claude Code) and raw notes, compiles them into a structured markdown wiki with source citations and contradiction flags, and exposes the wiki to Claude via MCP.

Two deliverables:
1. **MVP** — CLI tool (Python): ingest → compile → MCP server
2. **Demo** — Web app (React/Vite): pre-loaded knowledge base for LinkedIn/小红书 sharing, deployed to Vercel

## Tech Stack

- Python 3.11+
- Claude API (anthropic SDK) with model routing: Haiku for filtering, Sonnet for compilation
- MCP SDK (Python) for the MCP server
- React + Vite for the demo, Tailwind for styling
- All output as local markdown files

## Build Order (2-day target)

### Day 1: Core Pipeline

**Step 1: Project setup**
```
kompile/
├── kompile/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── claude.py        # Claude.ai JSON export parser
│   │   ├── chatgpt.py       # ChatGPT JSON export parser
│   │   ├── claude_code.py   # Claude Code project file parser
│   │   └── raw.py           # Raw text / markdown file parser
│   ├── compiler/
│   │   ├── __init__.py
│   │   ├── filter.py        # Haiku: conversation filtering & classification
│   │   ├── summarize.py     # Sonnet: per-source summary extraction
│   │   ├── compile.py       # Sonnet: cross-source synthesis → wiki articles
│   │   └── prompts.py       # All LLM prompts centralized here
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── server.py        # MCP server with 5 tools
│   └── models.py            # Data models (Article, Concept, Insight, etc.)
├── wiki/                    # Compiled output (git-trackable)
│   ├── index.md
│   ├── articles/
│   ├── concepts/
│   └── insights.md
├── raw/                     # User's source files
├── kompile.yaml             # Config (API keys, model preferences)
├── pyproject.toml
└── README.md
```

**Step 2: Ingest parsers**

Build parsers for each source type. Each parser outputs a standardized `Source` object:

```python
@dataclass
class Source:
    id: str                    # unique identifier
    platform: str              # "claude" | "chatgpt" | "claude_code" | "manual"
    title: str                 # conversation title or filename
    date: str                  # ISO date
    content: str               # full text content
    metadata: dict             # platform-specific metadata
```

Claude.ai export format: ZIP containing JSON files. Each conversation has `uuid`, `name`, `created_at`, and `chat_messages` array with `sender` ("human"/"assistant") and `text` fields. Parse and extract.

ChatGPT export format: ZIP containing `conversations.json`. Each conversation has `title`, `create_time`, and `mapping` dict with message nodes. Parse the message tree to reconstruct linear conversation.

Claude Code: Read `CLAUDE.md` files and any `.md` files in the project directory. Use the filename and directory as context.

Raw text: Accept `.md` and `.txt` files. Use filename as title, file modified date as date.

**Step 3: Filtering (Haiku)**

For each parsed source, call Haiku to determine:
- Keep or discard (is this substantive research/analysis, or trivial Q&A?)
- Topic tags (what domains does this conversation cover?)
- One-line summary

Process sources one at a time — each is well within context window.

Prompt structure (see Section 4.6 of product doc for context window rules):
```
You are a conversation filter. Evaluate whether this AI conversation contains 
substantive knowledge worth compiling into a knowledge base.

Output JSON:
{"keep": true/false, "topics": ["topic1", "topic2"], "summary": "one line summary"}

Discard: casual chat, simple Q&A, debugging help, one-off tasks.
Keep: research discussions, analysis, framework development, strategic reasoning, 
deep explanations, multi-turn knowledge building.

CONVERSATION:
{source.content}
```

Model: Haiku. Budget: ~5K tokens per call.

**Step 4: Summarization (Sonnet)**

For each kept source, call Sonnet to extract a structured summary:

```
You are a knowledge extractor. Extract the key knowledge from this AI conversation.

Output JSON:
{
  "claims": [
    {
      "text": "the specific claim or insight",
      "type": "fact" | "analysis" | "framework" | "opinion",
      "confidence": "stated" | "inferred"
    }
  ],
  "frameworks": ["any frameworks, models, or taxonomies developed"],
  "key_terms": ["important concepts or entities discussed"]
}

Important: preserve the specificity of claims. "CUDA switching cost is 6-12 months" 
is better than "CUDA has high switching costs."

SOURCE ({source.platform}, {source.date}):
{source.content}
```

Model: Sonnet. Budget: ~10K tokens input, ~500 tokens output per source.

**Step 5: Compilation (Sonnet)**

This is the core. Feed ALL summaries into one Sonnet call to generate the wiki.

Hard rule from product doc: never exceed 50% of context window. If total summaries exceed 80K tokens, chunk by topic and compile in groups, then merge.

```
You are a knowledge compiler. Compile these source summaries into a structured 
knowledge base.

CRITICAL RULES:
1. SOURCE CITATION: Every claim must reference which source(s) it comes from, 
   using the format [Source: {platform} — "{title}" ({date})].
2. ORIGIN MARKERS: Mark each paragraph as either:
   - [Source] if it directly paraphrases a single source
   - [Synthesis] if it combines information from multiple sources
3. CONTRADICTION FLAGS: If two sources disagree on a claim, do NOT resolve it. 
   Flag it as: ⚠ Conflict: {source A says X} vs {source B says Y}.
4. SUGGESTED GAPS: Identify areas where source coverage is thin. Phrase as: 
   "Sources contain limited information about X. This may be intentional or 
   an area to explore."

Output JSON:
{
  "title": "Knowledge Base Title",
  "domains": [
    {
      "name": "Domain Name",
      "subtopics": [
        {"name": "Subtopic", "article_ids": ["id1", "id2"]}
      ]
    }
  ],
  "articles": [
    {
      "id": "slug-id",
      "title": "Article Title",
      "sources": [
        {"platform": "claude", "title": "conv title", "date": "2026-03-15"}
      ],
      "content": "Full article with [Source]/[Synthesis] markers and inline citations...",
      "concepts": ["concept1", "concept2"],
      "backlinks": ["other-article-id"]
    }
  ],
  "cross_topic_concepts": [
    {"concept": "Name", "appears_in": ["Domain1", "Domain2"], "note": "why it matters"}
  ],
  "insights": [
    {"text": "Cross-source insight with citations", "sources": ["source1", "source2"]}
  ],
  "suggested_gaps": [
    {"gap": "Topic", "detail": "Description. This may be intentional or an area to explore."}
  ]
}

SOURCE SUMMARIES:
{all_summaries_json}
```

Model: Sonnet. Budget: summaries input (~25K) + prompt (~1K) + output (~8K) = ~34K tokens.

**Step 6: Write wiki files**

Take the compilation output and write to the `wiki/` directory:

- `wiki/index.md` — master index with all article titles, one-line summaries, concept tags
- `wiki/articles/{id}.md` — one file per article, with full content, source citations, origin markers
- `wiki/concepts.md` — all concepts with descriptions and cross-domain appearances
- `wiki/insights.md` — cross-source insights with citations
- `wiki/gaps.md` — suggested gaps
- `wiki/domains.md` — knowledge map (domains → subtopics → articles)

Each article's markdown should include YAML frontmatter:
```yaml
---
title: "Article Title"
sources:
  - platform: claude
    title: "CUDA ecosystem analysis"
    date: 2026-03-15
  - platform: chatgpt
    title: "Platform lock-in strategies"
    date: 2026-02-28
concepts: [CUDA, Switching Costs]
backlinks: [tpu-competition, nvidia-strategy]
---
```

**Step 7: CLI interface**

```bash
kompile ingest <path>          # Parse source files, save to raw/
kompile filter                  # Run Haiku filter on all unfiltered sources
kompile compile                 # Run full compilation pipeline
kompile compile --incremental   # Only process new sources since last compile
kompile status                  # Show: X sources ingested, Y filtered, Z compiled
```

### Day 2: MCP Server + Demo

**Step 8: MCP Server**

Build using Python MCP SDK. Expose 5 tools:

```python
# Tool 1: get_index
# Returns: all article titles + one-line summaries + concept tags
# Token cost: 300-500 tokens
# Implementation: read wiki/index.md, return as structured text

# Tool 2: get_article(article_id: str)
# Returns: full content of one article including source citations
# Token cost: 500-800 tokens
# Implementation: read wiki/articles/{article_id}.md

# Tool 3: get_insights
# Returns: cross-source insights + suggested gaps
# Token cost: 200-300 tokens
# Implementation: read wiki/insights.md + wiki/gaps.md

# Tool 4: search(query: str)
# Returns: matching paragraphs across all articles
# Token cost: 200-500 tokens
# Implementation: simple keyword/fuzzy search over article content

# Tool 5: get_knowledge_map
# Returns: domains → subtopics → article list
# Token cost: 200-400 tokens
# Implementation: read wiki/domains.md
```

MCP server config for Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "kompile": {
      "command": "python",
      "args": ["-m", "kompile.mcp.server"],
      "cwd": "/path/to/kompile"
    }
  }
}
```

Test: start MCP server, open Claude Desktop, ask a question that requires knowledge base access. Claude should call get_index first, then get_article for relevant articles.

**Step 9: Web Demo**

React + Vite app with pre-loaded knowledge base (hardcoded JSON, not API-dependent for initial load).

Use the AI infrastructure knowledge base from our conversations as the pre-loaded data. The data should be embedded in the app as a JSON constant — no backend needed for browsing.

Pages/tabs:
1. **Overview** — knowledge map (expandable domain tree), cross-topic concepts, insights (with source citations visible), suggested gaps
2. **Articles** — sidebar list + article reader. Show source citations, [Source]/[Synthesis] markers, contradiction flags, backlinks
3. **Q&A** — input box, 2-3 pre-loaded example questions. Calls Claude API (Sonnet) with knowledge base as context to answer. This is the only part that needs API calls.
4. Bottom: "Built with KOMPILE" + GitHub link + one-line explanation

Design direction: dark theme, monospace headings (JetBrains Mono), clean/technical aesthetic. Not flashy — this is a tool for power users.

Deploy to Vercel.

## Model Configuration

```yaml
models:
  filter: claude-haiku-4-5-20251001      # Cheap, fast. For filtering and tagging.
  summarize: claude-sonnet-4-20250514    # Mid-range. For per-source extraction.
  compile: claude-sonnet-4-20250514      # Mid-range. For cross-source synthesis.
  query: claude-sonnet-4-20250514        # Mid-range. For MCP Q&A and demo Q&A.
```

All model strings should be configurable in `kompile.yaml` so users can swap models.

## Key Design Principles

1. **Never exceed 50% of context window in any single API call.** Split into batches if needed.
2. **Every compiled claim must have a source citation.** No citation = hallucination risk.
3. **Contradictions are flagged, never resolved.** The compiler surfaces conflicts; the user decides.
4. **Gaps are suggested, not asserted.** Always include "This may be intentional."
5. **Index must stay lightweight.** Under 1000 tokens for a typical personal knowledge base.
6. **All output is local markdown.** No database, no cloud, no lock-in. Git-friendly.
7. **Haiku for cheap tasks, Sonnet for smart tasks.** Never use Opus in MVP. Cost matters.

## Pre-loaded Demo Data

Use the AI infrastructure knowledge base that was developed through Erica's conversations:
- AI Stack six-layer framework
- CUDA as NVIDIA's moat (15-year software ecosystem, switching costs)
- Training vs inference distinction (forward pass + backprop vs forward only)
- Google TPU competition (Trillium 4.7x improvement, Anthropic contract, Midjourney 80% cost cut)
- Groq LPU (tensor streaming, 10x latency, NVIDIA acquisition exploration)
- Inference cost curve (halving every 8 weeks, three drivers)
- NVIDIA two-pronged strategy (acquire inference chips + expand to Agent Layer via NemoClaw)

Sources should be labeled as: Claude conversations, GPT conversations, YouTube videos, articles, personal notes. Include realistic dates from early-mid 2026.

## Testing

1. Parse a real Claude.ai export JSON → verify Source objects are correct
2. Parse a real ChatGPT export JSON → verify Source objects are correct
3. Run filter on 10+ conversations → verify keep/discard decisions make sense
4. Run full compile → verify articles have source citations, contradiction flags where appropriate
5. Start MCP server → verify Claude Desktop can call all 5 tools
6. Deploy demo → verify pre-loaded KB renders correctly, Q&A works

## Done When

- [ ] `kompile ingest` successfully parses Claude and ChatGPT exports
- [ ] `kompile compile` produces a wiki/ directory with cited, structured articles
- [ ] MCP server runs and Claude Desktop can query the knowledge base
- [ ] Demo is deployed to Vercel with pre-loaded AI infra knowledge base
- [ ] README.md explains setup in under 5 minutes of reading
