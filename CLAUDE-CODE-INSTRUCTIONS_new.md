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
│   │   ├── article.py       # Article URL → auto-fetch body text
│   │   ├── youtube.py       # YouTube URL → auto-fetch transcript
│   │   ├── raw.py           # Raw text / markdown file parser
│   │   └── router.py        # Auto-detect input type → route to correct parser
│   ├── compiler/
│   │   ├── __init__.py
│   │   ├── filter.py        # Haiku: filtering + topic tagging
│   │   ├── classify.py      # Depth classification: deep / active / surface
│   │   ├── summarize.py     # Sonnet: per-source summary extraction
│   │   ├── compile.py       # Sonnet: cross-source synthesis → wiki
│   │   └── prompts.py       # All LLM prompts centralized here
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── server.py        # MCP server with 5 tools
│   └── models.py            # Data models (Article, Concept, Insight, etc.)
├── wiki/                    # Compiled output (git-trackable)
│   ├── index.md             # Master index across all tiers
│   ├── profile.md           # Knowledge shape overview
│   ├── deep/                # Deep Domains (5+ sources) — full articles
│   ├── active/              # Active Topics (2-4 sources) — synthesized notes
│   ├── surface/             # Surface Notes (1 source) — archived summaries
│   ├── concepts.md
│   ├── insights.md
│   └── gaps.md
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
    platform: str              # "claude" | "chatgpt" | "claude_code" | "article" | "youtube" | "manual"
    title: str                 # conversation title, article title, video title, or filename
    date: str                  # ISO date
    content: str               # full text content
    url: str | None            # original URL if applicable
    metadata: dict             # platform-specific metadata
```

**Claude.ai export:** ZIP containing JSON files. Each conversation has `uuid`, `name`, `created_at`, and `chat_messages` array with `sender` ("human"/"assistant") and `text` fields. Parse and extract.

**ChatGPT export:** ZIP containing `conversations.json`. Each conversation has `title`, `create_time`, and `mapping` dict with message nodes. Parse the message tree to reconstruct linear conversation.

**Claude Code:** Read `CLAUDE.md` files and any `.md` files in the project directory. Use the filename and directory as context.

**Article URL:** User provides a web URL. Use `trafilatura` or `readability-lxml` to extract article body text, title, and publish date. Strip navigation, ads, footers. Store extracted text + original URL.

```python
# pip install trafilatura
import trafilatura
downloaded = trafilatura.fetch_url(url)
text = trafilatura.extract(downloaded)
```

**YouTube URL:** User provides a YouTube URL. Extract video ID, fetch transcript using `youtube-transcript-api`. Concatenate transcript segments into full text. Store transcript + video title + URL.

```python
# pip install youtube-transcript-api
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi.get_transcript(video_id)
full_text = " ".join([t['text'] for t in transcript])
```

**Raw text:** Accept `.md` and `.txt` files. Use filename as title, file modified date as date.

**Router (router.py):** Auto-detect input type and route to correct parser:

```python
def route_input(path_or_url: str) -> str:
    if path_or_url.endswith('.zip'):
        # Peek inside ZIP to detect Claude vs ChatGPT format
        return "claude" or "chatgpt"
    elif os.path.isdir(path_or_url):
        return "claude_code"
    elif "youtube.com" in path_or_url or "youtu.be" in path_or_url:
        return "youtube"
    elif path_or_url.startswith("http"):
        return "article"
    else:
        return "raw"
```

This enables the unified CLI:
```bash
kompile ingest <anything>   # auto-detects type
```

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

**Step 4: Depth Classification**

After filtering, group kept sources by topic and classify each topic into a tier:

```python
# Group sources by topic tag
topic_groups = group_by_topic(filtered_sources)

# Classify each topic
for topic, sources in topic_groups.items():
    if len(sources) >= 5:
        topic.tier = "deep"      # Full compilation: articles, cross-refs, insights, gaps
    elif len(sources) >= 2:
        topic.tier = "active"    # Light compilation: one synthesized note
    else:
        topic.tier = "surface"   # No compilation: archive with title + summary only
```

Surface notes skip Steps 5-6 entirely — they already have their Haiku-generated summary from Step 3.

**Step 5: Summarization (Sonnet)**

For each kept source in **deep** and **active** topics, call Sonnet to extract a structured summary:

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

**Step 6: Compilation (Sonnet, tier-dependent)**

This is the core. Compilation runs differently for each tier.

**For Deep Domains:** Feed all summaries for that domain into one Sonnet call. This produces full articles with cross-references.

Hard rule from product doc: never exceed 50% of context window. If total summaries exceed 80K tokens, chunk by subtopic and compile in groups, then merge.

```
You are a knowledge compiler. Compile these source summaries into a structured 
knowledge domain.

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
  "domain": "Domain Name",
  "subtopics": [
    {"name": "Subtopic", "article_ids": ["id1", "id2"]}
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
  ]
}

SOURCE SUMMARIES FOR THIS DOMAIN:
{domain_summaries_json}
```

**For Active Topics:** Feed all summaries for that topic into one Sonnet call. Produces a single synthesized note, not multiple articles.

```
You are a knowledge compiler. Synthesize these sources into ONE comprehensive note.
Include source citations for every claim. Flag any contradictions.

Output JSON:
{
  "topic": "Topic Name",
  "note": "Synthesized note with [Source: ...] citations throughout...",
  "concepts": ["key concepts"],
  "related_domains": ["domains this topic connects to, if any"]
}

SOURCE SUMMARIES:
{topic_summaries_json}
```

**For Surface Notes:** No compilation needed. Already have Haiku summary from Step 3.

**Cross-domain pass (after all tiers compiled):** One final Sonnet call across ALL compiled content to find cross-domain connections:

```
You are a knowledge analyst. Given this compiled knowledge profile, identify:
1. Cross-domain concepts (concepts appearing in multiple domains/topics)
2. Cross-domain insights (connections the user might not have noticed, especially 
   between Deep Domains and Active Topics, or across different AI platforms)
3. Suggested gaps in overall coverage

Include cross-platform insights like: "Your Claude conversation about X and your 
GPT conversation about Y are applying the same framework."

KNOWLEDGE PROFILE INDEX:
{all_domains_and_topics_index}
```

Model: Sonnet. Budget: ~25-40K tokens per deep domain, ~5K per active topic, ~10K for cross-domain pass.

**Step 7: Write wiki files**

Take the compilation output and write to the `wiki/` directory:

- `wiki/index.md` — master index across all tiers: deep articles + active notes + surface titles
- `wiki/profile.md` — knowledge shape overview with depth indicators per domain/topic
- `wiki/deep/{domain}/{id}.md` — one file per deep article, with full content, citations, markers
- `wiki/active/{topic}.md` — one file per active topic, synthesized note with citations
- `wiki/surface/` — one file per surface note, title + summary + tags only
- `wiki/concepts.md` — cross-domain concepts with descriptions
- `wiki/insights.md` — cross-source and cross-domain insights with citations
- `wiki/gaps.md` — suggested gaps

Profile.md should look like:
```markdown
# Knowledge Profile

## Deep Domains
- ⚡ AI Infrastructure — 20 sources, 7 articles ████████████
- 📊 Investment Analysis — 8 sources, 3 articles ██████

## Active Topics  
- 🎯 Career Planning — 3 sources, 1 note
- 🏗️ Product Strategy — 2 sources, 1 note

## Surface Notes
- ✈️ Travel (1 source) | 🍳 Cooking (1 source) | ...
```

Each deep article's markdown should include YAML frontmatter:
```yaml
---
title: "Article Title"
tier: deep
domain: "AI Infrastructure"
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

**Step 8: CLI interface**

```bash
kompile ingest <path>          # Parse source files, save to raw/
kompile filter                  # Run Haiku filter + depth classification
kompile compile                 # Run full compilation pipeline (all tiers)
kompile compile --incremental   # Only process new sources since last compile
kompile status                  # Show: X sources, Y deep domains, Z active topics, W surface notes
```

### Day 2: MCP Server + Demo

**Step 9: MCP Server**

Build using Python MCP SDK. Expose 5 tools.

**CRITICAL DESIGN DECISION: KOMPILE is context, not constraint.**

The MCP tools provide Claude with the user's personal knowledge context. Claude should use this to:
- Understand what the user already knows and at what depth
- Build on the user's existing frameworks and terminology
- Combine the user's prior analysis with Claude's own knowledge and web search
- Identify where new information confirms, extends, or contradicts the user's existing understanding

Claude should NOT be restricted to only answering from the knowledge base. The knowledge base is a reference layer, not a cage.

```python
# Tool 1: get_index
# Description: "Returns the user's personal knowledge profile index — their 
#   researched topics, depth of knowledge, and analytical frameworks. Use this 
#   to understand the user's context and build on their existing knowledge. 
#   This is CONTEXT for richer answers, not the only source of truth."
# Returns: all article titles + one-line summaries + concept tags + tier indicators
# Token cost: 300-500 tokens
# Implementation: read wiki/index.md

# Tool 2: get_article(article_id: str)
# Description: "Returns a compiled article from the user's knowledge base, 
#   including source citations. Use this to understand the user's existing 
#   analysis on a topic before adding new information or perspectives."
# Returns: full content of one article including source citations
# Token cost: 500-800 tokens
# Implementation: read wiki/deep/{domain}/{article_id}.md or wiki/active/{topic}.md

# Tool 3: get_insights
# Description: "Returns cross-source insights and suggested knowledge gaps 
#   the user may want to explore. Use to understand connections the user has 
#   already identified and areas where their research is thin."
# Returns: cross-source insights + suggested gaps
# Token cost: 200-300 tokens
# Implementation: read wiki/insights.md + wiki/gaps.md

# Tool 4: search(query: str)
# Description: "Search the user's knowledge base for specific topics or claims. 
#   Use to check if the user has existing knowledge on a subject before 
#   providing new information."
# Returns: matching paragraphs across all articles
# Token cost: 200-500 tokens
# Implementation: simple keyword/fuzzy search over article content

# Tool 5: get_knowledge_profile
# Description: "Returns the user's overall knowledge shape — which domains 
#   are deep, which are active, which are surface-level. Use to calibrate 
#   response depth: go deeper on topics the user knows well, provide more 
#   foundations on topics they've barely explored."
# Returns: all domains/topics with depth indicators + tier classification
# Token cost: 200-400 tokens
# Implementation: read wiki/profile.md
```

**Example: how Claude should behave with MCP connected:**

User asks: "What's the latest on NVIDIA's inference strategy?"

Without KOMPILE: Claude gives a generic answer about NVIDIA.

With KOMPILE: Claude calls `get_index` → sees user has deep AI Infrastructure domain with articles on CUDA moat, Groq LPU, NVIDIA two-pronged strategy. Calls `get_article("nvidia-strategy")` → reads user's existing analysis about "acquire inference chips + expand to Agent Layer." Then uses web search for latest news. Responds: "Based on your two-pronged strategy framework, the latest developments are... This aligns with your prediction about NemoClaw, but there's a new development you haven't covered yet..."

This is the magic: Claude doesn't just answer — it answers **in the context of what you already know**.

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

Test: start MCP server, open Claude Desktop, ask a question that touches a topic in the knowledge base. Claude should call get_index, read relevant articles, then combine KB context with its own knowledge to give a richer answer than it would without KOMPILE.

**Step 10: Web Demo**

React + Vite app with pre-loaded knowledge profile (hardcoded JSON, not API-dependent for initial load).

**NOTE: Demo Q&A vs MCP Q&A behave differently.**
- **Demo Q&A:** answers based primarily on the pre-loaded knowledge base (to showcase what compilation produces). Prompt: "Answer based on this knowledge base. Reference specific articles."
- **MCP Q&A (real usage):** knowledge base is context, not constraint. Claude freely combines KB + own knowledge + web search.

The demo is showcasing the knowledge base artifact. The real product experience is Claude becoming smarter because it has your context.

Pages/tabs:
1. **Overview** — Knowledge Profile showing all domains with depth indicators (deep ████ / active ██ / surface ▪), cross-domain concepts, insights (with source citations visible, including cross-platform insights), suggested gaps
2. **Articles** — sidebar grouped by tier (Deep Domains expandable into articles, Active Topics as single notes, Surface Notes as simple list). Article reader shows source citations, [Source]/[Synthesis] markers, contradiction flags, backlinks
3. **Q&A** — input box, 2-3 pre-loaded example questions including at least one cross-domain question. Calls Claude API (Sonnet) with knowledge base as context to answer.
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

The demo should show a realistic multi-topic personal knowledge profile, not a single research project. Use this structure:

**Deep Domain: AI Infrastructure** (20 sources → 7 articles)
From Erica's actual research conversations:
- AI Stack six-layer framework (sources: Claude chat, personal notes)
- CUDA as NVIDIA's moat — 15-year ecosystem, switching costs (sources: Claude chat, article)
- Training vs inference distinction (sources: Claude chat, personal notes)
- Google TPU competition — Trillium, Anthropic contract, Midjourney 80% cost cut (sources: article, YouTube)
- Groq LPU — tensor streaming, 10x latency, NVIDIA acquisition (sources: YouTube, personal notes)
- Inference cost curve — halving every 8 weeks (sources: article, a16z report)
- NVIDIA two-pronged strategy — acquire inference chips + NemoClaw Agent Layer (sources: GTC YouTube, Claude chat, personal analysis)

**Active Topic: Product Strategy** (3 sources → 1 synthesized note)
- Karpathy's LLM Knowledge Base concept and productization direction (sources: Claude chat, GPT chat)

**Active Topic: Personal Finance** (2 sources → 1 synthesized note)
- Investment framework discussions (sources: GPT chat, article)

**Surface Notes** (1 source each, archived only):
- Travel planning (1 GPT conversation)
- Cooking recipe (1 Claude conversation)
- Fitness routine (1 Claude conversation)

**Cross-domain insight example:**
"Your Claude conversations about CUDA switching costs (AI Infrastructure) and your GPT conversations about platform lock-in in investment analysis (Personal Finance) are applying the same mental model — lock-in economics. You may be using this framework across domains without realizing it."

**Suggested gap example:**
"Your AI Infrastructure research extensively covers inference costs but contains limited information about training cost trends. This may be intentional or an area to explore."

Sources should be labeled with realistic platforms and dates from early-mid 2026. Include a mix of Claude, GPT, YouTube, articles, and personal notes to demonstrate cross-platform aggregation.

## Testing

1. Parse a real Claude.ai export JSON → verify Source objects are correct
2. Parse a real ChatGPT export JSON → verify Source objects are correct
3. Ingest an article URL → verify body text extracted, title and date captured
4. Ingest a YouTube URL → verify transcript fetched, video title captured
5. Verify router auto-detects: ZIP, directory, YouTube URL, article URL, markdown file
6. Run filter on 10+ sources → verify keep/discard and topic classification
7. Verify depth classification: topics with 5+ sources → deep, 2-4 → active, 1 → surface
8. Run full compile → verify deep articles have source citations, origin markers, contradiction flags
9. Verify active topics produce single synthesized notes, not full article sets
10. Verify surface notes are archived with summary only, not compiled
11. Start MCP server → verify Claude Desktop can call all 5 tools
12. Deploy demo → verify multi-topic knowledge profile renders correctly, Q&A works

## Done When

- [ ] `kompile ingest` successfully parses Claude exports, ChatGPT exports, article URLs, YouTube URLs, and raw files
- [ ] Router auto-detects input type correctly
- [ ] `kompile filter` classifies sources into deep/active/surface tiers
- [ ] `kompile compile` produces a wiki/ directory with tiered structure (deep articles + active notes + surface archive)
- [ ] Deep articles have source citations, [Source]/[Synthesis] markers, contradiction flags
- [ ] Cross-domain insights identify connections across topics and platforms
- [ ] MCP server runs and Claude Desktop can query the knowledge base
- [ ] Demo is deployed to Vercel with multi-topic knowledge profile
- [ ] README.md explains setup in under 5 minutes of reading
