import { useState } from "react";
import { deepDomains, activeNotes, surfaceNotes, sourceColors } from "../data/knowledgeBase";

// ── Content renderer ────────────────────────────────────────────────────────

function renderContent(content) {
  const lines = content.split("\n");
  return lines.map((line, i) => {
    if (!line.trim()) return <br key={i} />;

    if (line.includes("⚠ **Conflict:**") || line.includes("⚠")) {
      return (
        <div key={i} style={{ background: "#2d1f0e", border: "1px solid #7c4a10", borderRadius: "6px", padding: "0.6rem 0.8rem", margin: "0.5rem 0", fontSize: "0.82rem", color: "#d97706", lineHeight: 1.6 }}>
          {line}
        </div>
      );
    }

    if (line.includes("📋 **Suggested gap:**") || line.startsWith("📋")) {
      return (
        <div key={i} style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: "6px", padding: "0.6rem 0.8rem", margin: "0.5rem 0", fontSize: "0.82rem", color: "#8b949e", lineHeight: 1.6 }}>
          {line}
        </div>
      );
    }

    if (line.startsWith("**") && line.endsWith("**")) {
      return <div key={i} style={{ fontWeight: 600, color: "#e6edf3", marginTop: "1rem", marginBottom: "0.4rem", fontSize: "0.9rem" }}>{line.replace(/\*\*/g, "")}</div>;
    }

    if (line.startsWith("- ")) {
      return (
        <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.25rem" }}>
          <span style={{ color: "#58a6ff", flexShrink: 0 }}>·</span>
          <span style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.6 }}>{renderInline(line.slice(2))}</span>
        </div>
      );
    }

    return (
      <p key={i} style={{ fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.7, marginBottom: "0.5rem" }}>
        {renderInline(line)}
      </p>
    );
  });
}

function renderInline(text) {
  const parts = text.split(/(\[Source\]|\[Synthesis\]|\[Source:[^\]]+\])/g);
  return parts.map((part, i) => {
    if (part === "[Source]") return <span key={i} style={{ fontSize: "0.7rem", color: "#3b82f6", fontFamily: "monospace", marginRight: "2px", opacity: 0.8 }}>[Source]</span>;
    if (part === "[Synthesis]") return <span key={i} style={{ fontSize: "0.7rem", color: "#8b5cf6", fontFamily: "monospace", marginRight: "2px", opacity: 0.8 }}>[Synthesis]</span>;
    if (part.startsWith("[Source:")) return <span key={i} style={{ fontSize: "0.72rem", color: "#4d6073", fontFamily: "monospace" }}>{part}</span>;
    if (part.includes("**")) {
      const subparts = part.split(/(\*\*[^*]+\*\*)/g);
      return subparts.map((sp, j) =>
        sp.startsWith("**") ? <strong key={j} style={{ color: "#e2e8f0", fontWeight: 600 }}>{sp.replace(/\*\*/g, "")}</strong> : sp
      );
    }
    return part;
  });
}

// ── Article reader ──────────────────────────────────────────────────────────

function ArticleReader({ item, tier, onNavigate }) {
  if (!item) return null;

  const isActive = tier === "active";
  const isSurface = tier === "surface";
  const content = isActive ? item.note : isSurface ? null : item.content;
  const sources = isSurface ? [] : item.sources;
  const concepts = isSurface ? item.topics : (item.concepts || []);
  const backlinks = isActive || isSurface ? [] : (item.backlinks || []);

  return (
    <div style={{ flex: 1, minWidth: 0 }}>
      {/* Tier badge */}
      <div style={{ marginBottom: "0.5rem" }}>
        {tier === "deep" && <span style={{ fontSize: "0.7rem", background: "#1c2d3e", color: "#58a6ff", padding: "2px 8px", borderRadius: "3px", fontFamily: "monospace" }}>⚡ Deep Domain</span>}
        {tier === "active" && <span style={{ fontSize: "0.7rem", background: "#0d2818", color: "#3fb950", padding: "2px 8px", borderRadius: "3px", fontFamily: "monospace" }}>🎯 Active Topic</span>}
        {tier === "surface" && <span style={{ fontSize: "0.7rem", background: "#21262d", color: "#8b949e", padding: "2px 8px", borderRadius: "3px", fontFamily: "monospace" }}>▪ Surface Note</span>}
      </div>

      <h1 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#fff", marginBottom: "0.75rem" }}>
        {tier === "active" ? item.topic : item.title}
      </h1>

      {/* Sources */}
      {sources.length > 0 && (
        <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "6px", padding: "0.75rem 1rem", marginBottom: "1.25rem" }}>
          <div style={{ fontSize: "0.7rem", color: "#8b949e", fontFamily: "monospace", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>Sources</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
            {sources.map((s, i) => {
              const color = sourceColors[s.platform] || sourceColors.manual;
              return (
                <span key={i} style={{ fontSize: "0.78rem", padding: "3px 8px", borderRadius: "4px", background: "#1e293b", color: "#8b949e", border: "1px solid #30363d" }}>
                  {color.label} — "{s.title}" ({s.date})
                </span>
              );
            })}
          </div>
          {/* Related domains for active notes */}
          {isActive && item.related_domains?.length > 0 && (
            <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "#4d6073" }}>
              Related domains: {item.related_domains.join(", ")}
            </div>
          )}
        </div>
      )}

      {/* Surface-only: show archived message */}
      {isSurface && (
        <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "6px", padding: "0.75rem 1rem", marginBottom: "1.25rem" }}>
          <div style={{ fontSize: "0.82rem", color: "#8b949e", lineHeight: 1.6 }}>
            <strong style={{ color: "#e6edf3" }}>Summary:</strong> {item.summary}
          </div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "#4d6073" }}>
            Archived from {item.platform} on {item.date}. Single source — not compiled into a full article.
          </div>
        </div>
      )}

      {/* Concepts / topics */}
      {concepts.length > 0 && (
        <div style={{ marginBottom: "1rem", display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
          {concepts.map((c) => (
            <span key={c} style={{ fontSize: "0.72rem", padding: "2px 7px", borderRadius: "3px", background: "#1c2d3e", color: "#58a6ff", border: "1px solid #1f4068" }}>{c}</span>
          ))}
        </div>
      )}

      {/* Content */}
      {content && (
        <div style={{ lineHeight: 1.7 }}>
          {renderContent(content)}
        </div>
      )}

      {/* Backlinks */}
      {backlinks.length > 0 && (
        <div style={{ marginTop: "1.5rem", paddingTop: "1rem", borderTop: "1px solid #21262d" }}>
          <span style={{ fontSize: "0.75rem", color: "#8b949e", marginRight: "0.5rem" }}>Related:</span>
          {backlinks.map((bl) => {
            const target = deepDomains.flatMap((d) => d.articles).find((a) => a.id === bl);
            return target ? (
              <button key={bl} onClick={() => onNavigate({ item: target, tier: "deep" })}
                style={{ fontSize: "0.78rem", color: "#58a6ff", background: "none", border: "none", cursor: "pointer", padding: 0, marginRight: "0.75rem", fontFamily: "inherit", textDecoration: "underline" }}>
                {target.title}
              </button>
            ) : null;
          })}
        </div>
      )}
    </div>
  );
}

// ── Sidebar ─────────────────────────────────────────────────────────────────

function SidebarButton({ label, isSelected, onClick, indent = false }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "block", width: "100%", textAlign: "left",
        padding: indent ? "0.35rem 0.6rem 0.35rem 1.1rem" : "0.4rem 0.6rem",
        fontSize: "0.78rem",
        background: isSelected ? "#1c2d3e" : "none",
        border: isSelected ? "1px solid #1f4068" : "1px solid transparent",
        borderRadius: "4px", cursor: "pointer",
        color: isSelected ? "#58a6ff" : "#8b949e",
        marginBottom: "2px", fontFamily: "inherit",
        lineHeight: 1.4,
      }}
    >
      {label}
    </button>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

const firstArticle = deepDomains[0]?.articles[0];

export default function Articles() {
  const [selected, setSelected] = useState({ item: firstArticle, tier: "deep" });

  const handleSelect = (item, tier) => setSelected({ item, tier });

  const allDeepArticles = deepDomains.flatMap((d) => d.articles);
  const totalItems = allDeepArticles.length + activeNotes.length + surfaceNotes.length;

  return (
    <div style={{ display: "flex", gap: "1.5rem", alignItems: "flex-start" }}>
      {/* Sidebar */}
      <div style={{ width: "220px", flexShrink: 0 }}>
        <div style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#8b949e", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>
          {totalItems} items
        </div>

        {/* Deep Domains */}
        {deepDomains.map((domain) => (
          <div key={domain.name} style={{ marginBottom: "1rem" }}>
            <div style={{ fontSize: "0.68rem", color: "#58a6ff", fontFamily: "monospace", marginBottom: "0.35rem", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              ⚡ {domain.name}
            </div>
            {domain.articles.map((art) => (
              <SidebarButton
                key={art.id}
                label={art.title}
                isSelected={selected.item?.id === art.id && selected.tier === "deep"}
                onClick={() => handleSelect(art, "deep")}
                indent
              />
            ))}
          </div>
        ))}

        {/* Active Topics */}
        {activeNotes.length > 0 && (
          <div style={{ marginBottom: "1rem" }}>
            <div style={{ fontSize: "0.68rem", color: "#3fb950", fontFamily: "monospace", marginBottom: "0.35rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              🎯 Active Topics
            </div>
            {activeNotes.map((note) => (
              <SidebarButton
                key={note.topic}
                label={note.topic}
                isSelected={selected.item?.topic === note.topic && selected.tier === "active"}
                onClick={() => handleSelect(note, "active")}
                indent
              />
            ))}
          </div>
        )}

        {/* Surface Notes */}
        {surfaceNotes.length > 0 && (
          <div style={{ marginBottom: "1rem" }}>
            <div style={{ fontSize: "0.68rem", color: "#8b949e", fontFamily: "monospace", marginBottom: "0.35rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              ▪ Surface Notes
            </div>
            {surfaceNotes.map((note) => (
              <SidebarButton
                key={note.source_id}
                label={note.title}
                isSelected={selected.item?.source_id === note.source_id && selected.tier === "surface"}
                onClick={() => handleSelect(note, "surface")}
                indent
              />
            ))}
          </div>
        )}
      </div>

      {/* Article reader */}
      <ArticleReader
        item={selected.item}
        tier={selected.tier}
        onNavigate={({ item, tier }) => setSelected({ item, tier })}
      />
    </div>
  );
}
