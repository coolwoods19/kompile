# KOMPILE

**A personal knowledge base that grows with you.** Ingest anything — AI conversations, YouTube videos, articles, your own notes — and compile it into a structured, cited wiki that lives on your machine and talks to any AI model.

> Raw sources are source code. The LLM is the compiler. The wiki is the executable. — Karpathy

---

## What it does

1. **Ingest** — pull in knowledge from anywhere: Claude/ChatGPT exports, YouTube transcripts, web articles, Claude Code projects, raw notes
2. **Compile** — LLM pipeline filters noise, extracts claims, synthesizes articles by topic depth, flags contradictions, and identifies gaps across your entire knowledge base
3. **Query via MCP** — Claude Desktop reads your wiki in real time via a local MCP server, so your accumulated knowledge becomes part of every conversation

This is not a search engine over your files. It's a compiled knowledge base — sources are synthesized into articles you could have written yourself, with every claim traced back to its origin.

Every compiled article has:
- Source citations on every claim
- `[Source]` / `[Synthesis]` origin markers per paragraph
- `⚠ Conflict` flags where sources disagree (never silently merged)
- Suggested gaps ("may be intentional or an area to explore")

---

## Install

```bash
pip install kompile
```

Or from source:

```bash
git clone https://github.com/yourusername/kompile
cd kompile
pip install -e .
```

Set your API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or add api_key: "..." to kompile.yaml
```

---

## Usage

### 1. Ingest sources

```bash
kompile ingest claude_export.zip              # Claude.ai export (ZIP)
kompile ingest chatgpt_export.zip             # ChatGPT export (ZIP)
kompile ingest /path/to/project/              # Claude Code project directory
kompile ingest my_notes.md                    # Raw markdown / text file
kompile ingest https://youtube.com/watch?v=… # YouTube transcript
kompile ingest https://example.com/article   # Web article
```

Type is auto-detected. Pass `--type` to override if needed.

### 2. Compile

```bash
kompile compile                  # Full compile (first time or after many new sources)
kompile compile --incremental    # Only process new sources since last compile
```

### 3. Check status

```bash
kompile status
```

Output:
```
KOMPILE Status
────────────────────────────────────────
Sources ingested:    23
Sources filtered:    23/23
  → kept:            14
  → discarded:       9
Sources summarized:  14/14
Wiki compiled:       yes
  → articles:        8
```

### 4. Connect to Claude via MCP

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "kompile": {
      "command": "python",
      "args": ["-m", "kompile.mcp.server"],
      "cwd": "/path/to/your/kompile"
    }
  }
}
```

Restart Claude Desktop. Claude will now automatically access your knowledge base when relevant.

**MCP tools exposed:**

| Tool | What it returns | Typical tokens |
|---|---|---|
| `get_index` | All article titles + summaries + concepts | ~400 |
| `get_article(id)` | Full article with citations | ~600 |
| `get_insights` | Cross-source insights + gaps | ~250 |
| `search(query)` | Matching paragraphs | ~300 |
| `get_knowledge_map` | Domain tree | ~200 |

---

## Output structure

```
wiki/
├── index.md          # Master index (lightweight — loaded by MCP on every query)
├── articles/
│   ├── cuda-moat.md
│   ├── inference-cost-curve.md
│   └── ...
├── concepts.md       # Cross-domain concepts
├── insights.md       # Cross-source insights
├── gaps.md           # Suggested gaps
└── domains.md        # Knowledge map
```

All output is plain markdown. Git-friendly. Works in Obsidian, VS Code, any editor.

---

## Cost

- **Filtering** (Haiku): ~$0.001 per conversation
- **Summarization** (Sonnet): ~$0.01–0.03 per source
- **Full compilation** (~50 sources): ~$1.50–2.00 one-time
- **Incremental update** (1 new source): ~$0.05–0.10
- **MCP queries** (day-to-day): ~2,500 tokens per question (~0.2% of context window)

---

## Configuration

`kompile.yaml`:

```yaml
api_key: ""  # or set ANTHROPIC_API_KEY

models:
  filter: "claude-haiku-4-5-20251001"
  summarize: "claude-sonnet-4-20250514"
  compile: "claude-sonnet-4-20250514"
  query: "claude-sonnet-4-20250514"
```

---

## Demo

Live demo (pre-loaded AI infrastructure knowledge base): [kompile-demo.vercel.app](https://kompile-demo.vercel.app)

---

## Design principles

1. Never exceed 50% of context window in any single API call
2. Every compiled claim has a source citation — no citation = hallucination risk
3. Contradictions are flagged, never resolved — the compiler surfaces conflicts, you decide
4. Gaps are suggested, not asserted — always "may be intentional"
5. Index stays lightweight — under 1000 tokens for a typical personal knowledge base
6. All output is local markdown — no database, no cloud, no lock-in
7. Haiku for cheap tasks, Sonnet for smart tasks

---

*Inspired by Andrej Karpathy's "LLM Knowledge Bases" (April 2026). Your knowledge, your machine, your AI.*
