export default function About() {
  return (
    <div style={{ maxWidth: "640px" }}>
      <div style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#58a6ff", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "1.25rem" }}>
        What is KOMPILE?
      </div>

      <p style={{ fontSize: "0.9rem", color: "#94a3b8", lineHeight: 1.75, marginBottom: "1.25rem" }}>
        KOMPILE turns months of AI conversation residue into a structured, inspectable, reusable knowledge base — owned by you, accessible to any AI model.
      </p>

      <p style={{ fontSize: "0.875rem", color: "#8b949e", lineHeight: 1.75, marginBottom: "1.5rem" }}>
        Raw sources are source code. The LLM is the compiler. The wiki is the executable. — Karpathy
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1.5rem" }}>
        {[
          { label: "Input", items: ["Claude.ai exports", "ChatGPT exports", "Claude Code files", "Raw notes / markdown"] },
          { label: "Output", items: ["Cited wiki articles", "Knowledge map", "Cross-source insights", "Contradiction flags", "Suggested gaps"] },
        ].map((col) => (
          <div key={col.label} style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "8px", padding: "0.875rem 1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "#8b949e", fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.6rem" }}>{col.label}</div>
            {col.items.map((item) => (
              <div key={item} style={{ fontSize: "0.82rem", color: "#94a3b8", marginBottom: "0.25rem" }}>· {item}</div>
            ))}
          </div>
        ))}
      </div>

      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.75rem" }}>How to use</div>
        {[
          { cmd: "pip install kompile", desc: "Install" },
          { cmd: "kompile ingest claude_export.zip", desc: "Parse source files" },
          { cmd: "kompile compile", desc: "Generate wiki (calls Claude API)" },
          { cmd: "python -m kompile.mcp.server", desc: "Start MCP server for Claude Desktop" },
        ].map((step) => (
          <div key={step.cmd} style={{ display: "flex", gap: "1rem", alignItems: "baseline", marginBottom: "0.5rem" }}>
            <code style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "#34d399", background: "#1e293b", padding: "2px 6px", borderRadius: "3px", flexShrink: 0 }}>{step.cmd}</code>
            <span style={{ fontSize: "0.8rem", color: "#4d6073" }}>{step.desc}</span>
          </div>
        ))}
      </div>

      <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "8px", padding: "0.875rem 1rem", marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.5rem" }}>MCP server config (Claude Desktop)</div>
        <pre style={{ fontSize: "0.78rem", color: "#94a3b8", overflowX: "auto", margin: 0 }}>{`{
  "mcpServers": {
    "kompile": {
      "command": "python",
      "args": ["-m", "kompile.mcp.server"],
      "cwd": "/path/to/your/kompile"
    }
  }
}`}</pre>
      </div>

      <div style={{ borderTop: "1px solid #21262d", paddingTop: "1rem", display: "flex", gap: "1rem", alignItems: "center" }}>
        <a href="https://github.com/yourusername/kompile" target="_blank" rel="noopener noreferrer"
          style={{ fontSize: "0.82rem", color: "#58a6ff", textDecoration: "none" }}>
          GitHub ↗
        </a>
        <span style={{ fontSize: "0.78rem", color: "#4d6073" }}>Open source · Local-first · No lock-in</span>
      </div>
    </div>
  );
}
