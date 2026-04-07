# KOMPILE — Product Concept Document

**Status:** Final — ready for build
**Date:** April 2026
**Purpose:** Product spec for Claude Code build

---

## 1. Problem

Knowledge workers who heavily use AI tools face a compounding problem: their knowledge gets fragmented across platforms and formats.

**Where knowledge lives today:**
- Claude.ai conversations (insights, analysis, frameworks developed through dialogue)
- ChatGPT conversations (different topics, different threads)
- Claude Code projects (architecture decisions, technical reasoning in CLAUDE.md and session logs)
- Apple Notes (scattered fragments from YouTube videos, articles)
- Google Drive (documents, saved research)
- Browser bookmarks (articles read and forgotten)

**What goes wrong:**
- No AI platform has a complete picture. Claude knows what you discussed with Claude. GPT knows what you discussed with GPT. Neither knows the full picture.
- Cross-session memory is weak. Claude Memory stores fragments ("user researches AI infrastructure") but loses the reasoning chain — how you arrived at a conclusion across multiple conversations.
- Knowledge doesn't accumulate. Every new conversation starts with partial context. You spend tokens reconstructing what you already established.
- Nothing is browsable. You can't look at your knowledge and say "what do I know about X? What am I missing?"

**The question this product answers:** Why can't I have a single, structured, persistent knowledge base compiled from all my AI conversations and research — one that any AI model can access?

---

## 2. Product Positioning

**One-liner:** KOMPILE compiles your entire AI conversation history into a personal knowledge profile — deep where it matters, light where it doesn't. Owned by you, accessible to any AI model.

**Core metaphor (from Karpathy):** Raw sources are source code. The LLM is the compiler. The wiki is the executable.

**Key insight: real users don't have one research project — they have an entire knowledge life.** 20 deep AI infrastructure discussions, 8 investment chats, 5 career planning sessions, 2 travel queries, 1 recipe question. The product must handle the full spectrum, not just deep research. It compiles deeply where you've invested time, and stays light where you haven't.

**The real enemy is not "no memory" — it's opaque platform memory.** ChatGPT and Claude are both getting better at remembering, but their memory is platform-bound, opaque (you can't browse or edit the structure), and not portable. KOMPILE's wedge is: user-owned, inspectable, cross-model, depth-aware compiled knowledge — not just "better memory."

**Key differentiators:**

| | Notion/Notes | NotebookLM | Claude Memory | KOMPILE |
|---|---|---|---|---|
| What it does | Stores | Searches | Remembers fragments | Compiles (depth-aware) |
| Knowledge structure | Flat files | None (RAG) | Implicit, opaque | Tiered: deep domains, active topics, surface notes |
| Inspectable | Files only | No | No | Full knowledge profile + provenance |
| Cross-platform | N/A | Google only | Claude only | Any AI via MCP |
| Flags contradictions | No | No | No | Yes |
| Shows knowledge shape | No | No | No | Yes (which areas deep vs shallow) |
| Ownership | User's files | Google's cloud | Anthropic's system | User's local markdown |

**What KOMPILE is NOT:**
- Not another note-taking app
- Not a RAG pipeline
- Not a single-topic research tool — it's your entire knowledge profile
- Not "better memory" — it's a knowledge compiler
- Not a constraint on AI — it's context that makes AI answers richer, not a cage that limits them
- Not competing with Claude/GPT — it's a layer underneath that makes them better

---

## 3. Core Product Judgments

Three decisions that define the product. Everything else follows from these.

### 3.1 Minimum Irreplaceable Capability

KOMPILE's defensibility is not markdown, not MCP, not cross-platform import. Each of those can be replicated in a weekend. The irreplaceable capability is the combination of three things:

1. **Knowledge topology** — not a flat list of articles, but a hierarchical structure (domains → subtopics → concepts → articles) that shows the shape of what you know. NotebookLM doesn't have this. Claude Memory doesn't have this.

2. **Source provenance on every claim** — every statement in the compiled wiki traces back to its origin: which Claude conversation, which GPT conversation, which personal note, on which date. Without this, the wiki is indistinguishable from hallucination. No existing tool does this for AI conversation exports.

3. **Topological meta-information** — cross-domain concepts, contradictions between sources, and suggested gaps. This is the layer that tells you not just "what you know" but "what shape your knowledge is, where it's strong, where it's weak, and where it contradicts itself."

Any one of these alone can be replicated. The combination cannot — not by NotebookLM (no topology, no provenance), not by Claude Memory (opaque, no structure), not by DIY scripts (no standardized provenance or meta-information).

### 3.2 Usage Frequency

Two distinct frequencies, both required for the product to be a persistent tool rather than a one-time novelty:

**Low-frequency, heavy operation: Compilation**
- Triggered manually (MVP). Roughly every 1-2 weeks, or at the end of a research phase.
- Example: user spent two weeks researching NVIDIA's inference strategy, had 8 Claude conversations, 3 GPT conversations, watched 4 YouTube videos. Phase ends → user runs `kompile compile` → knowledge crystallizes.
- This is the "value creation" moment.

**High-frequency, light operation: Query via MCP**
- Happens passively, multiple times per day. User chats with Claude normally; MCP makes Claude aware of the knowledge base in the background.
- User may not even notice MCP is working — they just experience "Claude knows my research."
- This is the "value delivery" moment.

If only compilation exists without ongoing queries, it's a one-time tool. If only queries exist without growing compilation, there's no compounding. Both are needed.

**MVP: manual compilation trigger. V2: smart reminders ("5 new conversations since last compile").**

### 3.3 Trust as Product Design

Trust is not a feature. It's the entire UX of the compiled output. Every article the compiler produces must answer: "Why should I believe this?"

**Article-level: Source attribution**

Every article header shows exactly which sources contributed:

```
Sources:
  💬 Claude — "CUDA ecosystem analysis" (Mar 15, 2026)
  💬 GPT — "Platform lock-in strategies" (Feb 28, 2026)
  📝 Personal note — "NVIDIA两条路策略" (Mar 20, 2026)
```

**Paragraph-level: Origin markers**

Each paragraph is marked as one of two types:
- **[Source]** — content directly extracted/paraphrased from a specific source. Hover/click reveals the original conversation snippet.
- **[Synthesis]** — content generated by the compiler by combining multiple sources. Lists which sources were synthesized.

Not every sentence needs a marker — paragraph-level granularity is sufficient. Most paragraphs will be [Synthesis].

**Inline: Contradiction flags**

When sources disagree, the compiler does NOT resolve the contradiction. It flags it inline, next to the relevant paragraph:

```
⚠ Conflict: Your Claude conversation (Mar 15) concluded that CUDA's
switching cost is 6-12 months. Your GPT conversation (Feb 28) cited a
case study where migration took only 3 months. Both claims are retained.
```

Design principle: the compiler surfaces conflicts, the user resolves them.

**Blind spots as suggestions, not assertions**

Gaps are phrased as observations, not accusations:

```
📋 Suggested gap: Your sources extensively cover inference cost trends
but contain limited information about training cost trends. This may be
intentional (outside your research scope) or an area to explore.
```

The phrase "This may be intentional" is critical — the system should not assume the user's knowledge is incomplete, only that its source coverage is.

**V2 (not MVP): Confidence indicators**
- 🟢 Well-supported (3+ sources corroborate)
- 🟡 Single-source (unverified)
- 🔴 Conflicted (sources disagree)

---

## 4. How It Works

### 4.1 Data Ingest

Sources supported in MVP:

**AI Conversation Exports**
- Claude.ai: Export via Settings > Privacy > Export Data (JSON). Parse conversation threads, extract substantive exchanges, discard trivial Q&A.
- ChatGPT: Export via Settings > Data controls > Export (JSON). Same parsing logic.
- Claude Code: Read CLAUDE.md project files, session logs, and code comments from local project directories.

**Article URLs**
- User pastes a web article URL → system auto-fetches and extracts article body text (using readability/trafilatura).
- Stores extracted text + URL + title + date as a source.

**YouTube URLs**
- User pastes a YouTube URL → system auto-fetches transcript/subtitles (via youtube-transcript-api or similar).
- Stores transcript + video title + URL + date as a source.
- No need for user to manually take notes from videos anymore.

**Manual Input**
- Upload markdown or text files (personal notes, excerpts, etc.)

**Unified CLI interface:**
```bash
kompile ingest claude-export.zip                    # Claude conversations
kompile ingest chatgpt-export.zip                   # GPT conversations
kompile ingest ./my-project/                        # Claude Code project
kompile ingest https://example.com/article          # Article → auto-fetch
kompile ingest https://youtube.com/watch?v=xxx      # YouTube → auto-transcript
kompile ingest notes.md                             # Manual notes
```

System auto-detects input type (ZIP, directory, URL, file) and routes to the correct parser.

**Not in MVP (future):**
- Direct API connectors to Google Drive, Apple Notes
- Browser extension for real-time capture
- Automatic sync with AI platforms
- Podcast transcript ingestion

### 4.2 Depth Classification & Compilation

Before compilation, sources are grouped by topic and classified by depth. This determines how much compilation effort each topic receives.

**Step 1: Topic grouping (Haiku)**

After filtering, the kept sources are grouped by topic. Multiple conversations about the same subject get clustered. Haiku assigns topic labels during filtering (see 4.1).

**Step 2: Depth classification**

Topics are automatically classified into three tiers based on source count:

| Tier | Source count | What gets compiled | Example |
|---|---|---|---|
| **Deep Domain** | 5+ sources | Full compilation: interlinked articles, cross-references, insights, suggested gaps, contradiction flags | AI Infrastructure (20 sources) |
| **Active Topic** | 2-4 sources | Light compilation: one synthesized note with source citations | Investment Analysis (3 sources) |
| **Surface Note** | 1 source | No compilation: archived with title, summary, tags. Searchable but not compiled. | Recipe question (1 source) |

This ensures the knowledge profile is deep where the user has invested time, and doesn't waste tokens or clutter the wiki with over-compiled one-off queries.

**Step 3: Compilation (tier-dependent)**

For **Deep Domains** — full compilation via Sonnet. Multiple articles, knowledge map subtopics, cross-references, insights, gaps. Same as described below.

For **Active Topics** — light compilation via Sonnet. One comprehensive note synthesizing all sources, with source citations. No sub-articles, no cross-references within the topic. But cross-domain connections to Deep Domains ARE tracked (e.g., "this investment analysis references the same switching cost concept as your AI Infrastructure research").

For **Surface Notes** — Haiku summary only. Title, one-line summary, topic tag, date. Stored in wiki/surface/ for searchability via MCP but not compiled into articles.

**What the compiler produces (for Deep Domains):**

1. **Articles** — Synthesized pieces that combine information from multiple sources. Not summaries of individual sources, but new articles that cross-reference and connect ideas. Each article tracks which sources it drew from.

2. **Knowledge Profile Map** — The shape of the user's entire knowledge: all domains with depth indicators, subtopics within Deep Domains, and a flat list for Active Topics and Surface Notes. Shows where knowledge is concentrated and where it's thin.

3. **Cross-references & Backlinks** — Every article links to related articles. Concepts that appear across multiple domains are flagged — including connections between Deep Domains and Active Topics.

4. **Cross-source Insights** — Connections the user might not have noticed, including cross-domain insights. "Your Claude conversation about CUDA (AI Infrastructure) and your GPT conversation about portfolio switching costs (Investment Analysis) are applying the same framework — lock-in economics."

5. **Suggested Gaps** — Gaps in knowledge coverage, phrased as suggestions. "Sources contain limited information about training cost trends. This may be intentional or an area to explore."

6. **Index file** — Lightweight summary of all content across all tiers (Deep articles + Active notes + Surface titles). This is what gets loaded into AI context for navigation — typically < 1000 tokens for the entire knowledge profile.

**Incremental compilation:** When new sources are added, the compiler doesn't rebuild from scratch. It checks: does this new source change a topic's tier? (e.g., 4th source on Investment Analysis → still Active. 5th source → promote to Deep Domain, trigger full compilation.) Otherwise, update within the current tier.

**Compilation is the most token-intensive step.** Initial compilation of ~50 conversation exports might cost $2-5 in API calls. Most of that cost goes to Deep Domains. Active Topics and Surface Notes are cheap. This is a one-time cost, not per-query.

### 4.3 Storage

All knowledge is stored as local markdown files in a standard directory structure:

```
kompile/
├── raw/                  # Original source files
│   ├── claude-export/
│   ├── gpt-export/
│   ├── claude-code/
│   └── manual/
├── wiki/                 # Compiled knowledge profile
│   ├── index.md          # Master index across all tiers (lightweight)
│   ├── profile.md        # Knowledge shape overview (domains + depth indicators)
│   ├── deep/             # Deep Domains — full articles
│   │   ├── ai-infrastructure/
│   │   └── ...
│   ├── active/           # Active Topics — synthesized notes
│   ├── surface/          # Surface Notes — title + summary only
│   ├── concepts.md       # Cross-domain concepts
│   ├── insights.md       # Cross-source and cross-domain insights
│   └── gaps.md           # Suggested gaps
└── kompile.yaml          # Configuration
```

**Why markdown, not a database:**
- Universal format — works with Obsidian, VS Code, any text editor
- Git-friendly — version control, collaboration, history
- No vendor lock-in — your knowledge is just files
- LLM-native — models read markdown natively, no conversion needed
- Aligns with Karpathy's "file over app" philosophy

### 4.4 AI Access via MCP

The MCP server exposes the knowledge base to Claude (and future: any MCP-compatible model).

**Core principle: KOMPILE is context, not constraint.** The knowledge base gives Claude the user's research history, analytical frameworks, and existing conclusions. Claude then combines this context with its own knowledge and web search to give richer, more personalized answers. Claude is NOT restricted to only answering from the knowledge base — that would make it weaker, not stronger.

The experience should be: "Claude suddenly understands my research background and builds on it" — not "Claude can only repeat what I already know."

**MCP Tools exposed:**

| Tool | What it returns | Typical token cost |
|---|---|---|
| `get_index` | All article titles + summaries + concept tags + tier indicators | 300-500 tokens |
| `get_article(id)` | Full content of one article with source citations | 500-800 tokens |
| `get_insights` | Cross-source insights + suggested gaps | 200-300 tokens |
| `search(query)` | Matching paragraphs across articles | 200-500 tokens |
| `get_knowledge_profile` | All domains/topics with depth indicators | 200-400 tokens |

**How a typical query flows:**

1. User asks Claude a question
2. Claude calls `get_index` (~400 tokens) — understands the user's knowledge landscape
3. Claude decides which 2-3 articles are relevant to the question
4. Claude calls `get_article` for each (~2000 tokens total) — reads the user's existing analysis
5. Claude combines: **user's knowledge base** (what the user already knows and how they think about it) + **Claude's own knowledge** (broad training data) + **web search** (latest information if needed)
6. Claude responds in the context of the user's frameworks — e.g., "Based on your two-pronged strategy analysis, the latest development suggests..."
7. Total knowledge base cost per query: ~2500 tokens out of 200K context window

**This solves the token/context window problem:** The full knowledge base might be 400K+ tokens, but each query only loads 1-2% of it. The index acts as a routing table.

### 4.5 Model Routing & Cost Optimization

Not every task needs the same model. The system should balance cost and intelligence:

**Tier 1 — Cheap & fast (Haiku-class):**
- Conversation filtering: "Is this conversation substantive or trivial?"
- Source classification: "Is this about AI infrastructure or something else?"
- Index generation: extracting titles and one-line summaries
- Keyword/concept tagging
- Estimated cost: ~$0.001 per conversation filtered

**Tier 2 — Mid-range (Sonnet-class):**
- Article compilation: synthesizing multiple sources into a structured article
- Cross-reference detection: finding links between articles
- Insight generation: discovering cross-source patterns
- Blind spot analysis
- Incremental updates: integrating new sources into existing wiki
- Estimated cost: ~$0.01-0.03 per article compiled

**Tier 3 — High intelligence (Opus-class), used sparingly:**
- Complex Q&A that requires deep reasoning across many articles
- Resolving contradictions between sources
- Generating high-level strategic insights
- Quality "lint" pass over the entire knowledge base
- Estimated cost: ~$0.05-0.10 per query

**Routing logic:** The system defaults to the cheapest model that can handle the task. User can override for quality-critical operations. For MVP, this can be a simple config flag per operation rather than dynamic routing.

**Token budget principles:**
- Compilation is the expensive step — but it's one-time per source
- Day-to-day usage (MCP queries) should be cheap: index lookup + 2-3 article reads
- Never load the full knowledge base into context. Always: index first → selective article loading
- Cache the index in MCP server memory — don't re-read it every query

### 4.6 Context Window Management

Context window limits affect every stage of the pipeline. The build must be designed around these constraints from the start, not patched later.

**Stage 1: Ingestion & Filtering**

Problem: A user exports 200 Claude conversations. That could be 500K+ tokens of raw dialogue. Can't feed it all to a model at once, even for filtering.

Solution: Process conversations individually. Each conversation is typically 2K-20K tokens — well within any model's context window. The filtering step (Haiku) reads one conversation at a time and outputs a verdict: keep/discard + topic tags + one-line summary.

```
For each conversation in export:
  → Haiku: "Is this substantive? What topic? One-line summary." (~5K tokens per call)
  → Output: filtered_conversations.json with keep/discard flags
```

Token budget: 200 conversations × ~5K tokens avg = ~1M total tokens for Haiku filtering. At Haiku pricing, this costs roughly $0.25. Fast and cheap.

**Stage 2: Compilation**

Problem: After filtering, you might have 50 substantive conversations totaling 200K tokens. Still too much for a single compilation call.

Solution: Two-pass compilation.

Pass 1 — Per-source summaries (Sonnet): Read each filtered conversation individually. Extract key claims, insights, frameworks, decisions. Output a structured summary per source (~500 tokens each). This step can process sources in parallel.

```
For each kept conversation:
  → Sonnet: "Extract key insights, claims, frameworks from this conversation." (~10K tokens input → ~500 tokens output)
```

Pass 2 — Cross-source synthesis (Sonnet): Feed ALL per-source summaries into one call. 50 summaries × 500 tokens = 25K tokens input — comfortably within Sonnet's 200K window. This is where the compiler generates articles, discovers cross-references, identifies insights and blind spots.

```
All 50 summaries (25K tokens) + compilation prompt:
  → Sonnet: "Compile these into a structured wiki with articles, cross-references, insights, blind spots." (~25K input → ~8K output)
```

If the summaries exceed context window (unlikely for personal use, possible for heavy users): chunk the summaries into groups by topic, compile each group, then do a final merge pass.

Token budget for full compilation: Pass 1 (~50 × 10K = 500K tokens Sonnet) + Pass 2 (~30K tokens Sonnet). Roughly $1.50-2.00 total. One-time cost.

**Stage 3: MCP Queries (day-to-day usage)**

This is the cheapest stage, already covered in 4.4. Key constraints:

| Component | Typical size | % of 200K context window |
|---|---|---|
| Index (always loaded) | 300-500 tokens | 0.25% |
| 2-3 articles (per query) | 1,500-2,400 tokens | ~1.2% |
| Insights + blind spots | 200-300 tokens | 0.15% |
| **Total per query** | **~2,500 tokens** | **~1.6%** |

The rest of the context window (~195K tokens) is available for the user's actual conversation with Claude. Knowledge base access is virtually invisible in terms of context consumption.

**Stage 4: Incremental Updates**

When user adds new sources later, the system should NOT recompile everything. Instead:

```
New source → Haiku filters → Sonnet extracts summary
→ Load existing index + new summary
→ Sonnet: "Here's the existing wiki index. Here's a new source summary. 
   Which existing articles need updating? Any new articles needed? 
   Any new cross-references or insights?"
→ Update only affected articles
```

Token budget for incremental update: ~15K-25K tokens per new source. Roughly $0.05-0.10. Cheap enough to run frequently.

**Scaling thresholds:**

| Knowledge base size | Articles | Index size | Compilation approach |
|---|---|---|---|
| Small (< 30 sources) | 5-8 | ~300 tokens | Single-pass compilation works |
| Medium (30-100 sources) | 8-20 | ~800 tokens | Two-pass required |
| Large (100-500 sources) | 20-50 | ~2,000 tokens | Topic-chunked compilation + merge |
| Very large (500+ sources) | 50+ | ~5,000 tokens | Need lightweight RAG over index, or hierarchical index (domain → subtopic → article) |

For MVP targeting power users, "Medium" is the realistic starting point. The architecture should be designed for Medium but tested against Large.

**Hard rule for the build: no operation should ever attempt to load more than 50% of the model's context window.** This leaves room for the system prompt, the user's query, and the model's response. If an operation would exceed this, it must be split into smaller batches.

---

## 5. MVP Scope

**MVP and Demo are separate things with different purposes.**

- **MVP** = the actual product. Import → Compile → Query via MCP. This is what users install and use.
- **Demo** = a marketing asset. A web page with pre-loaded knowledge base for LinkedIn/小红书 sharing. Not the product itself.

### MVP (the product):

1. **Ingest parser**
   - Claude.ai JSON export → extract conversations, filter for substantive content
   - ChatGPT JSON export → same
   - Claude Code project directory → read CLAUDE.md, session files
   - Raw text paste

2. **Compiler** — the core of the product
   - Takes parsed sources, calls Claude API to generate structured wiki
   - Outputs: articles, index, concepts, insights, blind spots
   - **Source citations (MUST HAVE):** every claim in every compiled article must trace back to its origin — which Claude conversation, which GPT conversation, which note. Without provenance, the wiki is "elegant hallucination." This is not optional.
   - **Contradiction flags (MUST HAVE):** when sources disagree (e.g., Claude conversation says X, GPT conversation says Y about the same topic), the compiler must flag the contradiction explicitly, not silently merge. Implementation: add a "⚠ Contradiction" section to affected articles, showing both claims and their sources.
   - Incremental compilation support

3. **MCP Server**
   - Local server exposing the 5 tools (get_index, get_article, get_insights, search, get_concepts)
   - Connects to Claude Desktop / Claude.ai
   - Read-only (knowledge base is not modified during conversations)

### Demo (marketing asset, separate from MVP):

- Pre-loaded example knowledge base (Erica's AI infra research)
- Browse knowledge map, articles (with source citations visible), insights, blind spots
- Interactive Q&A against the pre-loaded KB
- Deployed on Vercel for link sharing
- No "try your own" — LinkedIn visitors won't paste content, they just want to see the result
- Purpose: generate interest, drive to GitHub repo

### What NOT to build:

- No Google Drive / Apple Notes / YouTube API connectors (manual input for now)
- No user accounts or authentication
- No cloud hosting of knowledge bases (all local)
- No real-time sync with AI platforms
- No mobile app
- No paid tier
- No diff view on recompilation (v2)
- No dynamic model routing (hardcoded per operation for MVP)

### Tech stack (proposed):

- Python for ingest parser + compiler (CLI tool)
- Python MCP server (using Anthropic's MCP SDK)
- React (Vite) for web demo, deployed on Vercel
- Claude API with model routing: Haiku for filtering/tagging, Sonnet for compilation, Opus for complex reasoning
- All open source on GitHub

---

## 6. Competitive Landscape

### The real enemy: opaque platform memory

The sharpest competitive contrast is not "we are not RAG." It is: **platform memory is opaque, fragmented, and not yours. KOMPILE is inspectable, cross-platform, and owned by you.**

ChatGPT and Claude are both getting better at remembering. But their memory is:
- **Opaque:** you can't browse what they "know" about you, can't see the structure, can't audit claims
- **Platform-bound:** Claude doesn't know what you told GPT. GPT doesn't know what you told Claude.
- **Not compiled:** they remember fragments, not synthesized knowledge with cross-references and contradiction flags
- **Not portable:** you can't take it with you or share it

KOMPILE fights on: **ownership, inspectability, cross-model portability, and compilation of reasoning traces into durable artifacts.**

### Adjacent products (not direct competitors, but in the same space):

**NotebookLM (Google)**
- Strengths: Free, simple, expanded outputs (reports, slides, quizzes, audio/video). Growing fast.
- Weaknesses: Still RAG-based (searches, doesn't compile), Google ecosystem lock-in, no cross-referencing, can't connect to other AI models, no contradiction detection
- Key difference: NotebookLM searches your documents and generates outputs from them. KOMPILE compiles knowledge into persistent, interlinked articles with provenance. Different core operation.

**Mem.ai**
- Strengths: AI-native note-taking, auto-organization, positions as "AI thought partner"
- Weaknesses: Proprietary format, single AI model, no cross-platform ingestion, no compilation
- Key difference: Mem organizes notes. KOMPILE compiles reasoning from AI conversations — a different input source and a different output artifact.

**Obsidian + Plugins**
- Strengths: Local-first, markdown, huge plugin ecosystem, graph view
- Weaknesses: Manual knowledge management, no AI compilation, steep learning curve
- Key difference: Obsidian is the IDE. KOMPILE is the compiler. They're complementary (KOMPILE outputs can be viewed in Obsidian).

**Glean**
- Strengths: 100+ enterprise connectors, permission-aware, $200M ARR, mature product
- Weaknesses: Enterprise only ($50+/user/month, $60K+ annual), RAG not compilation, no personal use case
- Key difference: Glean searches enterprise docs. KOMPILE compiles personal knowledge across AI platforms. Completely different market.

### Risks:

1. **Platform memory gets good enough:** Claude/GPT could build structured, inspectable, cross-session memory. Mitigation: they will never aggregate across competitors — Anthropic won't import your GPT history. Only a third party can be the neutral knowledge layer.

2. **Context window expansion:** If context windows reach 10M+ tokens, raw ingestion might seem "good enough." But even with unlimited context, you still need structure — dumping 100 raw conversations into a context window doesn't produce a knowledge map, cross-references, or blind spot detection. A library with infinite shelves still needs a catalog.

3. **Adoption friction:** Power users are the most likely to adopt but also the most likely to build their own solution (Karpathy literally did this). Mitigation: open source, zero lock-in, better than DIY scripts. The product should feel like "the polished version of what I was going to build myself."

---

## 7. Go-to-Market

### Phase 1: Build + Thought Leadership (Week 1, ideally Day 1-2 for build)

**Day 1-2: Build MVP with Claude Code**
- Ingest parser (Claude + GPT JSON, Claude Code files, raw text)
- Compiler (model-routed: Haiku for filtering, Sonnet for compilation)
- MCP server (5 tools, local)
- Web demo (pre-loaded KB, deploy to Vercel)

**Day 3-7: Content + Distribution**
- Erica creates content showing the concept in action:
  - LinkedIn post: "I compiled 3 months of Claude & GPT conversations into a personal knowledge base. Here's what happened."
  - 小红书: Demo video showing the before/after — scattered conversations vs structured knowledge base
  - Record screencast: asking Claude a question, watching it pull from personal knowledge base via MCP
- Share in relevant communities: Karpathy's tweet replies, MCP community, Obsidian community

### Phase 2: Open Source Launch (Week 2-3)

- Publish to GitHub with clear README
- Submit to Claude Code plugin marketplace
- List on mcp.so (19K+ MCP servers already listed)
- Collect user feedback, iterate on ingest parsers

### Phase 3: Community & Direction (Month 2+)

- Based on feedback, decide:
  - If demand is strong → explore co-founder partnership, move to Phase 4
  - If specific use case emerges (e.g., researchers, content creators) → narrow focus
  - If enterprise interest → explore team knowledge bases (Karpathy's "Company Bible" concept)

---

## 8. Future Roadmap

Beyond MVP, the product can expand in three directions:

### 8.1 Product Website

- Landing page explaining the concept (the "before/after" narrative)
- Interactive demo embedded (the web demo from MVP, refined)
- Documentation for setup and usage
- Blog / changelog for community updates

### 8.2 Claude Code Plugin / Marketplace

- Package KOMPILE as a Claude Code plugin for one-command installation
- Submit to Anthropic's official plugin marketplace
- Commands like `/kompile ingest`, `/kompile compile`, `/kompile search`
- Potential path into Claude Marketplace (enterprise tier) if traction warrants

### 8.3 Cloud-Hosted Service (托管服务)

- Users connect data sources (OAuth for Google Drive, API for Claude/GPT exports)
- Automatic ingestion + incremental compilation on server side
- Hosted MCP endpoint — no local server needed, works directly with Claude.ai
- Team knowledge bases — multiple contributors, shared compiled wiki
- Freemium: free for personal (up to X sources), paid for teams / high volume / auto-sync
- This is where the business model lives, but only worth building after MVP validates demand

### 8.4 Cross-Platform AI Access

- MCP for Claude (MVP)
- Custom GPT / OpenAI function calling for ChatGPT
- Gemini tool use integration
- Open API for any LLM framework (LangChain, LlamaIndex, etc.)
- The vision: one knowledge base, accessible from any AI model

---

## 9. Open Questions

*Note: Source citations and contradiction handling were previously listed here. They have been promoted to MVP must-haves in Section 5. Trust design details are in Section 3.3.*

These need to be resolved before or during building:

1. **Compilation quality control:** Beyond source citations and contradiction flags, do we need a "lint" step (like Karpathy suggests) to check for factual inconsistencies or stale claims? Probably v2, not MVP.

2. **Conversation filtering:** When ingesting 100+ Claude conversations, most are trivial. How aggressive should auto-filtering be? Should users tag which conversations to include? MVP approach: Haiku auto-filters, user can override.

3. **Update frequency:** When users add new sources, should compilation be manual (user clicks "recompile") or automatic? MVP approach: manual trigger.

4. **Privacy:** AI conversation exports contain personal information. If we ever move to cloud hosting, this becomes critical. For MVP (all local), this is less of a concern.

5. **Naming:** Is "KOMPILE" the right name? Alternatives: WikiSelf, KnowBase, MindCompile, Synthex, etc.

6. **Model routing granularity:** For MVP, should model selection be hardcoded per operation (e.g., always Haiku for filtering), or should the system dynamically choose based on input complexity? Hardcoded is simpler and ships faster.

7. **Target user narrowing:** Current framing is "power users who use multiple AI platforms." Should we narrow further to one specific persona (e.g., AI researchers, technical founders, content creators doing ongoing research)? First users will likely be people like Erica — multi-platform AI power users building domain expertise through AI conversations.

---

## 10. Success Metrics

For MVP validation:

- GitHub stars / forks (target: 100+ in first month)
- MCP server installs
- LinkedIn/小红书 post engagement (comments, saves, shares)
- Inbound interest from potential co-founder or users
- Qualitative: does Erica herself use this daily? Would she miss it if it disappeared?

---

*Inspired by Andrej Karpathy's "LLM Knowledge Bases" (April 2026). Core principle: knowledge belongs to the user, AI is interchangeable.*
