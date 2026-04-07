import { useState } from "react";
import {
  deepDomains, activeNotes, crossDomainInsights, suggestedGaps
} from "../data/knowledgeBase";

const EXAMPLE_QUESTIONS = [
  "What is NVIDIA's main competitive moat and how durable is it?",
  "How is inference cost changing and what's driving it?",
  "What connections do you see between my AI Infrastructure research and my Personal Finance thinking?",
];

function buildContext() {
  // Deep domain articles
  const articles = deepDomains.flatMap((d) =>
    d.articles.map((a) => `## ${a.title}\n${a.content}`)
  ).join("\n\n---\n\n");

  // Active topic notes
  const notes = activeNotes.map((n) => `## ${n.topic} (Active Topic)\n${n.note}`).join("\n\n---\n\n");

  // Cross-domain insights and gaps
  const insights = crossDomainInsights.map((i) => `- ${i.text}`).join("\n");
  const gaps = suggestedGaps.map((g) => `- ${g.gap}: ${g.detail}`).join("\n");

  return `# Knowledge Profile\n\n## Deep Domains\n\n${articles}\n\n## Active Topics\n\n${notes}\n\n# Cross-Domain Insights\n${insights}\n\n# Suggested Gaps\n${gaps}`;
}

export default function QA() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);

  async function askQuestion(q) {
    if (!q.trim()) return;
    if (!apiKey.trim()) {
      setShowApiKeyInput(true);
      setError("Enter your Anthropic API key to use Q&A. Your key is not stored.");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");

    try {
      const context = buildContext();
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey.trim(),
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1024,
          system: `You are answering questions based on a personal knowledge base compiled from AI conversations.
Answer using the knowledge base content provided. Cite which articles you're drawing from.
Be concise and direct. If the knowledge base doesn't cover something, say so clearly.

KNOWLEDGE BASE:
${context}`,
          messages: [{ role: "user", content: q }],
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error?.message || `API error ${response.status}`);
      }

      const data = await response.json();
      setAnswer(data.content[0].text);
    } catch (e) {
      setError(e.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: "680px" }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#58a6ff", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
          Ask the knowledge base
        </div>
        <p style={{ fontSize: "0.875rem", color: "#8b949e", lineHeight: 1.6, marginBottom: "1rem" }}>
          Claude reads the compiled wiki and answers your question with citations. This demonstrates how KOMPILE works with Claude via MCP in real use.
        </p>
      </div>

      {/* API Key input */}
      {showApiKeyInput && (
        <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "6px", padding: "0.75rem 1rem", marginBottom: "1rem" }}>
          <div style={{ fontSize: "0.78rem", color: "#8b949e", marginBottom: "0.5rem" }}>
            Anthropic API key (not stored, used for this request only):
          </div>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => { setApiKey(e.target.value); setError(""); }}
            placeholder="sk-ant-..."
            style={{ width: "100%", background: "#0d1117", border: "1px solid #30363d", borderRadius: "4px", padding: "0.4rem 0.6rem", color: "#e6edf3", fontSize: "0.875rem", fontFamily: "monospace", outline: "none" }}
          />
        </div>
      )}

      {/* Example questions */}
      <div style={{ marginBottom: "1rem" }}>
        <div style={{ fontSize: "0.72rem", color: "#4d6073", marginBottom: "0.4rem" }}>Try an example:</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => { setQuestion(q); askQuestion(q); }}
              style={{ textAlign: "left", background: "#161b22", border: "1px solid #21262d", borderRadius: "5px", padding: "0.5rem 0.75rem", fontSize: "0.82rem", color: "#8b949e", cursor: "pointer", fontFamily: "inherit", transition: "border-color 0.15s" }}
              onMouseOver={(e) => e.currentTarget.style.borderColor = "#30363d"}
              onMouseOut={(e) => e.currentTarget.style.borderColor = "#21262d"}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askQuestion(question)}
          placeholder="Ask anything about AI infrastructure..."
          style={{ flex: 1, background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", padding: "0.6rem 0.8rem", color: "#e6edf3", fontSize: "0.875rem", fontFamily: "inherit", outline: "none" }}
        />
        <button
          onClick={() => askQuestion(question)}
          disabled={loading}
          style={{ background: "#1f6feb", border: "none", borderRadius: "6px", padding: "0.6rem 1rem", color: "#fff", fontSize: "0.875rem", cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.6 : 1, fontFamily: "inherit", flexShrink: 0 }}
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: "#2d1520", border: "1px solid #6e3050", borderRadius: "6px", padding: "0.6rem 0.8rem", fontSize: "0.82rem", color: "#f87171", marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      {/* Answer */}
      {answer && (
        <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "8px", padding: "1rem 1.25rem" }}>
          <div style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#58a6ff", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.75rem" }}>
            Answer — drawn from knowledge base
          </div>
          <div style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.75, whiteSpace: "pre-wrap" }}>
            {answer}
          </div>
        </div>
      )}

      <div style={{ marginTop: "1.5rem", fontSize: "0.75rem", color: "#4d6073", lineHeight: 1.6 }}>
        In real use, KOMPILE runs a local MCP server. Claude Desktop automatically calls <code style={{ fontFamily: "monospace", color: "#3b82f6", background: "#1e293b", padding: "1px 4px", borderRadius: "3px" }}>get_index</code> and <code style={{ fontFamily: "monospace", color: "#3b82f6", background: "#1e293b", padding: "1px 4px", borderRadius: "3px" }}>get_article</code> — no manual context-pasting needed.
      </div>
    </div>
  );
}
