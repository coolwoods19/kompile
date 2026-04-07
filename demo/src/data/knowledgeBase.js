// Pre-loaded multi-topic personal knowledge profile
// Compiled from Erica's AI conversations — March-April 2026

// ── Deep Domains (5+ sources → full articles) ──────────────────────────────

export const deepDomains = [
  {
    name: "AI Infrastructure",
    source_count: 20,
    article_count: 7,
    subtopics: [
      { name: "NVIDIA's Moat", article_ids: ["cuda-moat", "nvidia-two-pronged-strategy"] },
      { name: "Competitive Alternatives", article_ids: ["google-tpu-competition", "groq-lpu"] },
      { name: "AI Economics", article_ids: ["inference-cost-curve", "training-vs-inference"] },
      { name: "Stack Architecture", article_ids: ["ai-stack-six-layers"] },
    ],
    articles: [
      {
        id: "cuda-moat",
        title: "CUDA as NVIDIA's Moat",
        sources: [
          { platform: "claude", title: "CUDA ecosystem deep-dive", date: "2026-03-15" },
          { platform: "chatgpt", title: "Platform lock-in strategies", date: "2026-02-28" },
          { platform: "manual", title: "YouTube notes — Jensen Huang interview", date: "2026-03-10" },
        ],
        concepts: ["CUDA", "Switching Costs", "Platform Lock-in", "Developer Ecosystem"],
        backlinks: ["nvidia-two-pronged-strategy", "google-tpu-competition"],
        content: `[Synthesis] CUDA is not primarily a programming language or a chip feature — it is a 15-year-old software ecosystem. The moat is not NVIDIA's hardware; it is the accumulated library of optimized kernels, tooling, debugging infrastructure, and developer knowledge that would take years to rebuild on any alternative platform. [Source: claude — "CUDA ecosystem deep-dive" (2026-03-15)]

**What makes CUDA sticky:**

[Source] Switching cost estimates place a full migration at 6-12 months of engineering time for a mid-size AI team. This includes not just rewriting code, but retraining institutional knowledge and replacing ecosystem dependencies (cuDNN, NCCL, Nsight, TensorRT). [Source: claude — "CUDA ecosystem deep-dive" (2026-03-15)]

⚠ **Conflict:** Your Claude conversation (Mar 15) concluded that CUDA switching cost is 6-12 months of engineering time. Your ChatGPT conversation (Feb 28) cited a case study where a team migrated from CUDA to ROCm in approximately 3 months. Both claims are retained — the discrepancy may reflect team size, codebase complexity, or the specific workload type.

[Synthesis] The switching cost argument is most powerful not because migration is impossible, but because the expected value of migrating is negative for most organizations. The ecosystem has 4M+ developers, 3,500+ CUDA-optimized libraries, and training data implicitly optimized for NVIDIA hardware. Alternatives must beat CUDA not just on hardware specs but on ecosystem completeness — a much harder bar. [Source: claude — "CUDA ecosystem deep-dive" (2026-03-15)] [Source: manual — "YouTube notes — Jensen Huang interview" (2026-03-10)]

**The 15-year compounding effect:**

[Source] NVIDIA began investing in CUDA in 2006. By 2026, the ecosystem has 20 years of compounding — every paper published, every framework optimized, every hire trained on CUDA reinforces the ecosystem. This makes the moat qualitatively different from hardware advantages, which can be matched by a well-funded competitor within 2-3 chip generations. [Source: manual — "YouTube notes — Jensen Huang interview" (2026-03-10)]`,
      },
      {
        id: "nvidia-two-pronged-strategy",
        title: "NVIDIA's Two-Pronged Competitive Strategy",
        sources: [
          { platform: "claude", title: "NVIDIA strategy analysis", date: "2026-03-20" },
          { platform: "chatgpt", title: "AI chip M&A landscape", date: "2026-03-18" },
        ],
        concepts: ["NVIDIA", "NemoClaw", "Agent Layer", "M&A Strategy"],
        backlinks: ["cuda-moat", "groq-lpu"],
        content: `[Synthesis] NVIDIA is executing a two-pronged strategy in response to the inference cost compression trend: (1) acquiring inference chip companies to hedge against GPU commoditization in inference workloads, and (2) expanding up the stack into the Agent Layer via NemoClaw and enterprise AI orchestration tools. [Source: claude — "NVIDIA strategy analysis" (2026-03-20)] [Source: chatgpt — "AI chip M&A landscape" (2026-03-18)]

**Prong 1: Defensive acquisition of inference silicon**

[Source] NVIDIA reportedly explored acquiring Groq — the leading LPU (Language Processing Unit) vendor — in early 2026. The motivation is defensive: as inference becomes the dominant AI workload (vs training), specialized inference chips threaten to displace GPUs for a significant portion of AI compute spend. Owning Groq would neutralize the most credible near-term hardware alternative. [Source: chatgpt — "AI chip M&A landscape" (2026-03-18)]

**Prong 2: Expanding to the Agent Layer**

[Source] NemoClaw is NVIDIA's enterprise agent orchestration platform, positioned as the runtime layer for autonomous AI agents. By controlling both the hardware (GPU) and the agent runtime, NVIDIA aims to capture economic value even as inference hardware commoditizes. This is structurally similar to how Intel attempted to own both the CPU and enterprise software layers in the server market. [Source: claude — "NVIDIA strategy analysis" (2026-03-20)]

[Synthesis] The two prongs are complementary: the hardware acquisition buys time while the software layer (agent orchestration) creates durable defensibility independent of chip architecture. The risk is execution — NVIDIA has historically been a hardware company, and software platform plays require a different organizational capability.`,
      },
      {
        id: "google-tpu-competition",
        title: "Google TPU: The Most Credible CUDA Alternative",
        sources: [
          { platform: "claude", title: "TPU competitive analysis", date: "2026-02-20" },
          { platform: "chatgpt", title: "Cloud AI infrastructure comparison", date: "2026-02-15" },
          { platform: "manual", title: "Midjourney TPU migration notes", date: "2026-03-05" },
        ],
        concepts: ["TPU", "Google", "Trillium", "Inference Cost", "Vendor Lock-in"],
        backlinks: ["cuda-moat", "inference-cost-curve"],
        content: `[Synthesis] Google's TPU (Tensor Processing Unit) is the most mature CUDA alternative, with three structural advantages: captive demand from Google's own AI workloads, vertical integration with Google Cloud, and a 10-year head start in production-scale deployment. The Trillium generation (TPU v5) represents the most serious challenge to NVIDIA's inference dominance yet. [Source: claude — "TPU competitive analysis" (2026-02-20)]

**Trillium (TPU v5) performance claims:**

[Source] Google claims Trillium delivers a 4.7x performance improvement over TPU v4 per chip. In inference workloads, this translates to substantially lower cost-per-token — a critical metric as inference becomes the dominant AI compute spend. [Source: claude — "TPU competitive analysis" (2026-02-20)]

**Real-world validation: Anthropic and Midjourney**

[Source] Anthropic signed a significant Google Cloud contract in 2025-2026, effectively betting its training workloads on TPU availability. [Source: chatgpt — "Cloud AI infrastructure comparison" (2026-02-15)]

[Source] Midjourney migrated approximately 80% of its inference workload to TPUs, reportedly achieving an 80% reduction in inference cost. [Source: manual — "Midjourney TPU migration notes" (2026-03-05)]

⚠ **Conflict:** Your Claude conversation estimated TPU inference cost savings at 40-60% vs GPU for image generation workloads. The Midjourney data point (80% cost reduction) is significantly higher. The discrepancy may reflect Midjourney's specific workload characteristics, negotiated pricing, or custom TPU kernels. Both claims are retained.

[Synthesis] The Midjourney case demonstrates that at scale, the ecosystem switching cost (from CUDA to XLA/JAX) is worth paying for the right cost profile. This weakens the "switching costs are too high" argument for large organizations running homogeneous workloads.`,
      },
      {
        id: "groq-lpu",
        title: "Groq LPU: 10x Latency, Different Trade-offs",
        sources: [
          { platform: "claude", title: "Groq technical architecture", date: "2026-01-15" },
          { platform: "chatgpt", title: "AI inference hardware landscape 2026", date: "2026-02-01" },
        ],
        concepts: ["Groq", "LPU", "Latency", "Tensor Streaming", "Inference Specialization"],
        backlinks: ["nvidia-two-pronged-strategy", "inference-cost-curve"],
        content: `[Synthesis] Groq's LPU (Language Processing Unit) achieves ~10x lower latency vs GPU inference through a fundamentally different architectural approach: deterministic execution via tensor streaming, which eliminates the memory bandwidth bottleneck that limits transformer inference on GPUs. [Source: claude — "Groq technical architecture" (2026-01-15)]

**The tensor streaming architecture:**

[Source] Traditional GPUs process matrix operations in parallel but must wait for memory I/O between operations. Groq's LPU uses a "tensor streaming" model where data flows continuously through dedicated compute units without waiting for DRAM access. For autoregressive token generation, this eliminates the primary performance bottleneck. [Source: claude — "Groq technical architecture" (2026-01-15)]

**Performance profile:**

[Source] Groq demonstrated ~500 tokens/second on Llama-2 70B in 2024, vs ~50-80 tokens/second on comparable GPU setups. For latency-sensitive applications (real-time voice, interactive coding assistants), this is a meaningful differentiation. [Source: chatgpt — "AI inference hardware landscape 2026" (2026-02-01)]

**Strategic position:**

[Synthesis] Groq's value proposition is most defensible in latency-critical use cases rather than cost-per-token optimization. As inference hardware commoditizes, Groq needs to own either the latency niche or find a strategic acquirer (the NVIDIA acquisition exploration fits this logic).`,
      },
      {
        id: "inference-cost-curve",
        title: "Inference Cost Trends: Halving Every 8 Weeks",
        sources: [
          { platform: "claude", title: "AI inference economics analysis", date: "2026-03-01" },
          { platform: "chatgpt", title: "LLM pricing trends 2024-2026", date: "2026-02-10" },
          { platform: "manual", title: "Personal notes — AI cost tracking", date: "2026-03-25" },
        ],
        concepts: ["Inference Cost", "Token Pricing", "AI Economics", "Commoditization"],
        backlinks: ["google-tpu-competition", "groq-lpu", "training-vs-inference"],
        content: `[Synthesis] LLM inference cost has been halving approximately every 8 weeks since mid-2023. This rate — faster than Moore's Law — is driven by three compounding factors: hardware improvements (GPU/TPU generations), software optimization (quantization, speculative decoding, batching), and market competition (more providers, lower margins). [Source: claude — "AI inference economics analysis" (2026-03-01)]

**The three drivers:**

[Source] Hardware: Each GPU/TPU generation delivers 2-4x throughput improvement per dollar. H100 → H200 → B100 represents roughly a 4x improvement over 18 months. [Source: claude — "AI inference economics analysis" (2026-03-01)]

[Source] Software optimization: Quantization (INT8/INT4), speculative decoding, continuous batching, and flash attention have collectively reduced compute per token by 3-5x since GPT-3's launch. [Source: chatgpt — "LLM pricing trends 2024-2026" (2026-02-10)]

[Source] Market competition: GPT-4-class capabilities now available at $0.002/1K tokens (early 2026), down from $0.06/1K at launch. [Source: manual — "Personal notes — AI cost tracking" (2026-03-25)]

📋 **Suggested gap:** Sources extensively cover inference cost trends but contain limited information about training cost trends. This may be intentional or an area to explore.`,
      },
      {
        id: "training-vs-inference",
        title: "Training vs Inference: Fundamentally Different Workloads",
        sources: [
          { platform: "claude", title: "ML fundamentals — forward pass and backprop", date: "2026-01-20" },
          { platform: "manual", title: "Personal notes — LLM architecture basics", date: "2026-01-25" },
        ],
        concepts: ["Training", "Inference", "Backpropagation", "Forward Pass", "Compute Profile"],
        backlinks: ["inference-cost-curve", "google-tpu-competition"],
        content: `[Synthesis] Training and inference are structurally different computational problems that favor different hardware architectures. Training requires the forward pass AND backpropagation, which necessitates storing large intermediate activations. Inference requires only the forward pass — more memory-bandwidth-bound than compute-bound for large models. [Source: claude — "ML fundamentals — forward pass and backprop" (2026-01-20)]

**Training compute profile:**

[Source] The backward pass requires storing all intermediate activations from the forward pass (for the chain rule calculation), making training roughly 3x more memory-intensive than inference per token processed. [Source: claude — "ML fundamentals — forward pass and backprop" (2026-01-20)]

**Inference compute profile:**

[Source] Inference requires only the forward pass: take input tokens, run through all transformer layers, sample the next token. No gradients, no activation storage beyond the KV cache for context. [Source: manual — "Personal notes — LLM architecture basics" (2026-01-25)]

**Hardware implications:**

[Synthesis] Training is compute-bound → GPUs with high FLOP/s are optimal. Inference is memory-bandwidth-bound → specialized inference chips (LPUs, TPUs) that optimize memory access patterns can outperform GPUs on cost-per-token. This is why Groq LPU and Google TPU are more competitive in inference than in training. [Source: claude — "ML fundamentals — forward pass and backprop" (2026-01-20)]`,
      },
      {
        id: "ai-stack-six-layers",
        title: "The AI Stack: Six Layers",
        sources: [
          { platform: "claude", title: "AI infrastructure layered model", date: "2026-02-05" },
          { platform: "chatgpt", title: "AI ecosystem mapping", date: "2026-02-08" },
        ],
        concepts: ["AI Stack", "Infrastructure Layers", "Value Chain", "Silicon", "Foundation Models"],
        backlinks: ["cuda-moat", "inference-cost-curve"],
        content: `[Synthesis] The AI value chain can be organized into six distinct layers, each with different competitive dynamics, margin profiles, and defensibility characteristics. [Source: claude — "AI infrastructure layered model" (2026-02-05)]

**Layer 1: Silicon (Hardware)** — NVIDIA GPUs, Google TPUs, Groq LPUs, AMD MI300X. Capital-intensive, long design cycles. NVIDIA dominates training; competition intensifying in inference.

**Layer 2: Cloud Infrastructure** — Data centers, power, cooling, networking. AWS, Azure, GCP, CoreWeave. Margin compression as capacity builds.

**Layer 3: Model Training Infrastructure** — Distributed training frameworks (Megatron-LM, DeepSpeed). Increasingly commoditized.

**Layer 4: Foundation Models** — GPT-4/4o, Claude 3/3.5, Gemini, Llama 3, Mistral. Open-source compressing value at this layer.

**Layer 5: Inference & Serving Infrastructure** — Model serving (vLLM, TensorRT-LLM), inference APIs. Rapidly commoditizing.

**Layer 6: Application Layer** — Products built on foundation models: GitHub Copilot, Cursor, Perplexity, Harvey. Highest margin potential long-term.

[Synthesis] Value in the AI stack is currently concentrated at Layer 1 (NVIDIA) and Layer 6 (applications with strong distribution), with Layers 2-5 commoditizing rapidly. [Source: claude — "AI infrastructure layered model" (2026-02-05)] [Source: chatgpt — "AI ecosystem mapping" (2026-02-08)]`,
      },
    ],
  },
];

// ── Active Topics (2-4 sources → single synthesized note) ──────────────────

export const activeNotes = [
  {
    topic: "Product Strategy",
    sources: [
      { platform: "claude", title: "Karpathy knowledge base concept", date: "2026-04-01" },
      { platform: "chatgpt", title: "Personal knowledge management tools", date: "2026-03-28" },
      { platform: "manual", title: "KOMPILE product notes", date: "2026-04-03" },
    ],
    concepts: ["Personal Knowledge", "LLM Compiler", "Knowledge Graph", "MCP"],
    related_domains: ["AI Infrastructure"],
    note: `[Synthesis] Andrej Karpathy's April 2026 concept of the "LLM Knowledge Base" introduces a compelling frame: raw conversation history is source code, the LLM is the compiler, and the structured wiki is the executable. The key insight is that current AI memory is implicit and opaque — KOMPILE makes it explicit, structured, and portable. [Source: claude — "Karpathy knowledge base concept" (2026-04-01)]

**Why this is the right wedge:**

[Source] Existing tools (NotebookLM, Mem.ai, Claude Memory) either search documents without compiling them into structured knowledge, or store memory implicitly without provenance. The gap is: user-owned, inspectable, cross-model compiled knowledge with source citations. [Source: chatgpt — "Personal knowledge management tools" (2026-03-28)]

⚠ **Conflict:** ChatGPT conversation suggested the primary moat is the cross-platform aggregation (Claude + GPT + Claude Code in one place). Personal notes argue the moat is the compilation artifact itself (cited articles with contradiction flags). Both are likely true but emphasize different user needs. Both claims are retained.

**Product positioning:**

[Source] KOMPILE is NOT a note-taking app, NOT a RAG pipeline, NOT "better memory" — it's a knowledge compiler. The output is a durable artifact (wiki) not a retrieval system. This distinction matters for the go-to-market: target users who have already invested deeply in AI conversations and want those conversations to compound. [Source: manual — "KOMPILE product notes" (2026-04-03)]`,
  },
  {
    topic: "Personal Finance",
    sources: [
      { platform: "chatgpt", title: "Portfolio strategy discussion", date: "2026-02-14" },
      { platform: "manual", title: "Investment framework notes", date: "2026-02-20" },
    ],
    concepts: ["Switching Costs", "Platform Lock-in", "Portfolio Construction", "Risk Management"],
    related_domains: ["AI Infrastructure"],
    note: `[Synthesis] Discussions about portfolio construction and asset allocation converge on one key framework: the cost of switching between investment theses or asset classes. Once capital is deployed in illiquid or concentrated positions, the switching cost (tax implications, opportunity cost, market impact) creates the same lock-in dynamics observed in technology platforms. [Source: chatgpt — "Portfolio strategy discussion" (2026-02-14)]

**The switching cost framework applied to finance:**

[Source] In portfolio construction, switching cost is the friction that prevents rational reallocation — similar to how CUDA switching cost prevents rational migration to cheaper inference hardware. Both represent cases where the economically optimal move is blocked by accumulated switching friction. [Source: manual — "Investment framework notes" (2026-02-20)]

**Core framework:**

[Synthesis] The key variables in any lock-in analysis: (1) current cost of staying, (2) expected benefit of switching, (3) one-time switching cost, (4) time to amortize switching cost. When expected benefit ÷ switching cost < time horizon threshold, switching is irrational even if alternatives are technically superior. This math applies equally to chip migrations and portfolio rebalancing. [Source: chatgpt — "Portfolio strategy discussion" (2026-02-14)] [Source: manual — "Investment framework notes" (2026-02-20)]`,
  },
];

// ── Surface Notes (1 source → archived, not compiled) ──────────────────────

export const surfaceNotes = [
  {
    source_id: "gpt-travel-tokyo",
    title: "Tokyo travel itinerary",
    platform: "chatgpt",
    date: "2026-01-10",
    summary: "7-day Tokyo itinerary including Shibuya, Shinjuku, Kyoto day trip, and restaurant recommendations",
    topics: ["Travel"],
  },
  {
    source_id: "claude-cooking-ramen",
    title: "Homemade ramen recipe",
    platform: "claude",
    date: "2026-02-03",
    summary: "Tonkotsu broth technique, chashu pork preparation, and tare variations",
    topics: ["Cooking"],
  },
  {
    source_id: "claude-fitness-routine",
    title: "Strength training routine",
    platform: "claude",
    date: "2026-03-11",
    summary: "4-day split program with progressive overload targeting compound movements",
    topics: ["Fitness"],
  },
];

// ── Cross-domain data ───────────────────────────────────────────────────────

export const crossTopicConcepts = [
  {
    concept: "Switching Costs",
    appears_in: ["AI Infrastructure", "Personal Finance"],
    note: "The same lock-in economics framework appears in both AI hardware (CUDA switching cost 6-12 months) and investment portfolio construction (tax/opportunity cost of rebalancing). You may be applying this mental model across domains without realizing it.",
  },
  {
    concept: "Platform Lock-in",
    appears_in: ["AI Infrastructure", "Product Strategy"],
    note: "Platform lock-in dynamics discussed in CUDA moat analysis connect directly to KOMPILE's product positioning — the value of user-owned, portable knowledge vs platform-bound memory.",
  },
  {
    concept: "Commoditization Dynamics",
    appears_in: ["AI Infrastructure", "Product Strategy"],
    note: "Inference commoditization in AI Infrastructure and the 'notebook LLM is commoditizing' argument in Product Strategy share the same underlying dynamic: falling unit costs shifting competition to higher layers.",
  },
];

export const crossDomainInsights = [
  {
    text: "Your Claude conversations about CUDA switching costs (AI Infrastructure) and your ChatGPT conversations about portfolio lock-in (Personal Finance) are applying the same mental model — lock-in economics. The formula is identical: switching cost / expected benefit > time horizon = stay put. You've developed a cross-domain framework without naming it.",
    sources: ["CUDA ecosystem deep-dive", "Portfolio strategy discussion"],
  },
  {
    text: "Your CUDA moat analysis and your inference cost curve analysis are making opposite arguments about the same underlying trend: as inference cost falls, the ROI of migrating to cheaper inference hardware (TPU, LPU) increases. The CUDA moat may be stronger for training than for inference — your sources support this but don't state it directly.",
    sources: ["CUDA ecosystem deep-dive", "AI inference economics analysis"],
  },
  {
    text: "The Midjourney 80% cost reduction case (AI Infrastructure) and the Karpathy knowledge base concept (Product Strategy) are both examples of the same pattern: a power user who invests in a non-standard workflow achieves outsized returns. Your research suggests you identify with this persona — worth making explicit in KOMPILE's go-to-market.",
    sources: ["Midjourney TPU migration notes", "KOMPILE product notes"],
  },
];

export const suggestedGaps = [
  {
    gap: "Training Cost Trends",
    detail: "Sources extensively cover inference cost trends but contain limited information about whether training costs are declining at a similar rate. This may be intentional (inference is the near-term focus) or an area to explore.",
  },
  {
    gap: "Open-Source Model Economics",
    detail: "Multiple sources mention Llama and Mistral as competitive pressure but do not analyze the economics of running open-source models at scale vs proprietary APIs. This may be intentional or an area to explore.",
  },
  {
    gap: "KOMPILE Competitive Landscape",
    detail: "Product Strategy note mentions NotebookLM and Mem.ai but contains limited information about pricing, user numbers, or growth trajectory of competitors. This may be intentional or an area to explore.",
  },
];

// ── Profile stats ───────────────────────────────────────────────────────────

export const profileStats = {
  total_sources: 26,
  deep_domains: deepDomains.length,
  active_topics: activeNotes.length,
  surface_notes: surfaceNotes.length,
  articles: deepDomains.reduce((sum, d) => sum + d.articles.length, 0),
  insights: crossDomainInsights.length,
  gaps: suggestedGaps.length,
};

// ── Source color helpers ────────────────────────────────────────────────────

export const sourceColors = {
  claude: { bg: "bg-orange-900/30", text: "text-orange-400", label: "💬 Claude" },
  chatgpt: { bg: "bg-green-900/30", text: "text-green-400", label: "💬 ChatGPT" },
  manual: { bg: "bg-blue-900/30", text: "text-blue-400", label: "📝 Personal note" },
  claude_code: { bg: "bg-purple-900/30", text: "text-purple-400", label: "⌨ Claude Code" },
  article: { bg: "bg-yellow-900/30", text: "text-yellow-400", label: "📄 Article" },
  youtube: { bg: "bg-red-900/30", text: "text-red-400", label: "▶ YouTube" },
};
