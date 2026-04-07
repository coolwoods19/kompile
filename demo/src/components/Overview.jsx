import {
  deepDomains, activeNotes, surfaceNotes,
  crossTopicConcepts, crossDomainInsights, suggestedGaps,
  profileStats,
} from "../data/knowledgeBase";

const S = {
  section: { marginBottom: "2rem" },
  sectionTitle: { fontSize: "0.75rem", fontFamily: "monospace", color: "#58a6ff", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "1rem" },
  card: { background: "#161b22", border: "1px solid #21262d", borderRadius: "8px", padding: "1rem 1.25rem", marginBottom: "0.75rem" },
  insightText: { fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.65, marginBottom: "0.5rem" },
  insightSources: { fontSize: "0.75rem", color: "#4d6073", fontStyle: "italic" },
  gapTitle: { fontSize: "0.875rem", fontWeight: 600, color: "#e6edf3", marginBottom: "0.25rem" },
  gapDetail: { fontSize: "0.82rem", color: "#8b949e", lineHeight: 1.6 },
  conceptBadge: { display: "inline-block", background: "#1c2d3e", border: "1px solid #1f4068", borderRadius: "4px", padding: "2px 8px", fontSize: "0.75rem", color: "#58a6ff", marginRight: "0.4rem", marginBottom: "0.4rem" },
  stat: { textAlign: "center", padding: "0.75rem 1.25rem" },
  statNum: { fontSize: "1.75rem", fontWeight: 700, color: "#58a6ff", fontFamily: "monospace" },
  statLabel: { fontSize: "0.72rem", color: "#8b949e", marginTop: "0.15rem" },
};

const MAX_BAR = 12;

function DepthBar({ count, max = MAX_BAR }) {
  const filled = Math.min(count, max);
  return (
    <span style={{ fontFamily: "monospace", fontSize: "0.8rem", letterSpacing: "1px" }}>
      <span style={{ color: "#58a6ff" }}>{"█".repeat(filled)}</span>
      <span style={{ color: "#21262d" }}>{"█".repeat(max - filled)}</span>
    </span>
  );
}

export default function Overview() {
  return (
    <div>
      {/* Stats bar */}
      <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "8px", display: "flex", justifyContent: "space-around", marginBottom: "2rem", padding: "0.5rem 0", flexWrap: "wrap" }}>
        {[
          { num: profileStats.total_sources, label: "sources compiled" },
          { num: profileStats.articles, label: "deep articles" },
          { num: profileStats.active_topics, label: "active topics" },
          { num: profileStats.insights, label: "cross-domain insights" },
        ].map((s) => (
          <div key={s.label} style={S.stat}>
            <div style={S.statNum}>{s.num}</div>
            <div style={S.statLabel}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Knowledge Profile */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Knowledge Profile</div>
        <div style={S.card}>
          {/* Deep Domains */}
          <div style={{ fontSize: "0.7rem", color: "#58a6ff", fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.6rem" }}>
            Deep Domains
          </div>
          {deepDomains.map((d) => (
            <div key={d.name} style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.82rem", color: "#e6edf3", width: "180px", flexShrink: 0 }}>
                ⚡ {d.name}
              </span>
              <DepthBar count={d.source_count} />
              <span style={{ fontSize: "0.75rem", color: "#4d6073", fontFamily: "monospace" }}>
                {d.source_count} sources, {d.article_count} articles
              </span>
            </div>
          ))}

          {/* Active Topics */}
          <div style={{ fontSize: "0.7rem", color: "#3fb950", fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "1rem", marginBottom: "0.6rem" }}>
            Active Topics
          </div>
          {activeNotes.map((n) => (
            <div key={n.topic} style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.82rem", color: "#e6edf3", width: "180px", flexShrink: 0 }}>
                🎯 {n.topic}
              </span>
              <DepthBar count={n.sources.length} />
              <span style={{ fontSize: "0.75rem", color: "#4d6073", fontFamily: "monospace" }}>
                {n.sources.length} sources, 1 note
              </span>
            </div>
          ))}

          {/* Surface Notes */}
          <div style={{ fontSize: "0.7rem", color: "#8b949e", fontFamily: "monospace", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "1rem", marginBottom: "0.5rem" }}>
            Surface Notes
          </div>
          <div style={{ fontSize: "0.8rem", color: "#4d6073" }}>
            {surfaceNotes.map((n, i) => (
              <span key={n.source_id}>
                ▪ {n.title} ({n.platform}){i < surfaceNotes.length - 1 ? "  |  " : ""}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Cross-Domain Concepts */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Cross-Domain Concepts</div>
        {crossTopicConcepts.map((c) => (
          <div key={c.concept} style={{ ...S.card, marginBottom: "0.5rem" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
              <span style={{ ...S.conceptBadge, marginBottom: 0, flexShrink: 0 }}>{c.concept}</span>
              <div>
                <div style={{ fontSize: "0.8rem", color: "#4d6073", marginBottom: "0.3rem" }}>
                  {c.appears_in.join(" · ")}
                </div>
                <div style={{ fontSize: "0.82rem", color: "#8b949e", lineHeight: 1.6 }}>{c.note}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Cross-Domain Insights */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Cross-Domain Insights</div>
        {crossDomainInsights.map((ins, i) => (
          <div key={i} style={S.card}>
            <div style={S.insightText}>{ins.text}</div>
            <div style={S.insightSources}>Sources: {ins.sources.join(", ")}</div>
          </div>
        ))}
      </div>

      {/* Suggested Gaps */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Suggested Gaps</div>
        {suggestedGaps.map((gap, i) => (
          <div key={i} style={{ ...S.card, borderLeft: "3px solid #30363d" }}>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "flex-start" }}>
              <span style={{ color: "#8b949e", fontSize: "0.9rem" }}>📋</span>
              <div>
                <div style={S.gapTitle}>{gap.gap}</div>
                <div style={S.gapDetail}>{gap.detail}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
