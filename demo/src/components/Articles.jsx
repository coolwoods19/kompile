import { useState } from "react";
import { kb, sourceColors } from "../data/knowledgeBase";

function renderContent(content) {
  // Render article content with special markers highlighted
  const lines = content.split("\n");
  return lines.map((line, i) => {
    if (!line.trim()) return <br key={i} />;

    // Conflict flag
    if (line.includes("⚠ **Conflict:**") || line.includes("⚠")) {
      return (
        <div key={i} style={{ background: "#2d1f0e", border: "1px solid #7c4a10", borderRadius: "6px", padding: "0.6rem 0.8rem", margin: "0.5rem 0", fontSize: "0.82rem", color: "#d97706", lineHeight: 1.6 }}>
          {line}
        </div>
      );
    }

    // Suggested gap
    if (line.includes("📋 **Suggested gap:**") || line.startsWith("📋")) {
      return (
        <div key={i} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", padding: "0.6rem 0.8rem", margin: "0.5rem 0", fontSize: "0.82rem", color: "#8b949e", lineHeight: 1.6 }}>
          {line}
        </div>
      );
    }

    // Heading
    if (line.startsWith("**") && line.endsWith("**")) {
      return <div key={i} style={{ fontWeight: 600, color: "#e6edf3", marginTop: "1rem", marginBottom: "0.4rem", fontSize: "0.9rem" }}>{line.replace(/\*\*/g, "")}</div>;
    }

    // List item
    if (line.startsWith("- ")) {
      const text = line.slice(2);
      return (
        <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.25rem" }}>
          <span style={{ color: "#58a6ff", flexShrink: 0 }}>·</span>
          <span style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.6 }}>{renderInline(text)}</span>
        </div>
      );
    }

    // Paragraph with markers
    return (
      <p key={i} style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.7, marginBottom: "0.5rem" }}>
        {renderInline(line)}
      </p>
    );
  });
}

function renderInline(text) {
  // Highlight [Source] and [Synthesis] markers + source citations
  const parts = text.split(/(\[Source\]|\[Synthesis\]|\[Source:[^\]]+\])/g);
  return parts.map((part, i) => {
    if (part === "[Source]") return <span key={i} style={{ fontSize: "0.7rem", color: "#3b82f6", fontFamily: "monospace", marginRight: "2px", opacity: 0.8 }}>[Source]</span>;
    if (part === "[Synthesis]") return <span key={i} style={{ fontSize: "0.7rem", color: "#8b5cf6", fontFamily: "monospace", marginRight: "2px", opacity: 0.8 }}>[Synthesis]</span>;
    if (part.startsWith("[Source:")) return <span key={i} style={{ fontSize: "0.72rem", color: "#4d6073", fontFamily: "monospace" }}>{part}</span>;
    // Bold **text**
    if (part.includes("**")) {
      const subparts = part.split(/(\*\*[^*]+\*\*)/g);
      return subparts.map((sp, j) =>
        sp.startsWith("**") ? <strong key={j} style={{ color: "#e2e8f0", fontWeight: 600 }}>{sp.replace(/\*\*/g, "")}</strong> : sp
      );
    }
    return part;
  });
}

export default function Articles() {
  const [selectedId, setSelectedId] = useState(kb.articles[0]?.id);
  const article = kb.articles.find((a) => a.id === selectedId);

  return (
    <div style={{ display: "flex", gap: "1.5rem", alignItems: "flex-start" }}>
      {/* Sidebar */}
      <div style={{ width: "220px", flexShrink: 0 }}>
        <div style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>
          {kb.articles.length} articles
        </div>
        {kb.domains.map((domain) => (
          <div key={domain.name} style={{ marginBottom: "1rem" }}>
            <div style={{ fontSize: "0.7rem", color: "#58a6ff", fontFamily: "monospace", marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              {domain.name}
            </div>
            {domain.subtopics.flatMap((st) =>
              st.article_ids.map((aid) => {
                const art = kb.articles.find((a) => a.id === aid);
                if (!art) return null;
                const isSelected = selectedId === aid;
                return (
                  <button
                    key={aid}
                    onClick={() => setSelectedId(aid)}
                    style={{
                      display: "block", width: "100%", textAlign: "left",
                      padding: "0.4rem 0.6rem", fontSize: "0.8rem",
                      background: isSelected ? "#1c2d3e" : "none",
                      border: isSelected ? "1px solid #1f4068" : "1px solid transparent",
                      borderRadius: "4px", cursor: "pointer",
                      color: isSelected ? "#58a6ff" : "#8b949e",
                      marginBottom: "2px", fontFamily: "inherit",
                    }}
                  >
                    {art.title}
                  </button>
                );
              })
            )}
          </div>
        ))}
      </div>

      {/* Article reader */}
      {article && (
        <div style={{ flex: 1, minWidth: 0 }}>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#fff", marginBottom: "0.75rem" }}>{article.title}</h1>

          {/* Sources header */}
          <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "6px", padding: "0.75rem 1rem", marginBottom: "1.25rem" }}>
            <div style={{ fontSize: "0.7rem", color: "#8b949e", fontFamily: "monospace", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>Sources</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
              {article.sources.map((s, i) => {
                const color = sourceColors[s.platform] || sourceColors.manual;
                return (
                  <span key={i} style={{ fontSize: "0.78rem", padding: "3px 8px", borderRadius: "4px", background: "#1e293b", color: "#8b949e", border: "1px solid #30363d" }}>
                    {color.label} — "{s.title}" ({s.date})
                  </span>
                );
              })}
            </div>
          </div>

          {/* Concepts */}
          {article.concepts.length > 0 && (
            <div style={{ marginBottom: "1rem", display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
              {article.concepts.map((c) => (
                <span key={c} style={{ fontSize: "0.72rem", padding: "2px 7px", borderRadius: "3px", background: "#1c2d3e", color: "#58a6ff", border: "1px solid #1f4068" }}>{c}</span>
              ))}
            </div>
          )}

          {/* Content */}
          <div style={{ lineHeight: 1.7 }}>
            {renderContent(article.content)}
          </div>

          {/* Backlinks */}
          {article.backlinks.length > 0 && (
            <div style={{ marginTop: "1.5rem", paddingTop: "1rem", borderTop: "1px solid #21262d" }}>
              <span style={{ fontSize: "0.75rem", color: "#8b949e", marginRight: "0.5rem" }}>Related:</span>
              {article.backlinks.map((bl) => {
                const target = kb.articles.find((a) => a.id === bl);
                return target ? (
                  <button key={bl} onClick={() => setSelectedId(bl)}
                    style={{ fontSize: "0.78rem", color: "#58a6ff", background: "none", border: "none", cursor: "pointer", padding: 0, marginRight: "0.75rem", fontFamily: "inherit", textDecoration: "underline" }}>
                    {target.title}
                  </button>
                ) : null;
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
