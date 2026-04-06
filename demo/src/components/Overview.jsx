import { kb, sourceColors } from "../data/knowledgeBase";

const S = {
  section: { marginBottom: "2rem" },
  sectionTitle: { fontSize: "0.75rem", fontFamily: "monospace", color: "#58a6ff", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "1rem" },
  card: { background: "#161b22", border: "1px solid #21262d", borderRadius: "8px", padding: "1rem 1.25rem", marginBottom: "0.75rem" },
  domainName: { fontSize: "0.875rem", fontWeight: 600, color: "#e6edf3", marginBottom: "0.5rem" },
  subtopic: { fontSize: "0.8rem", color: "#8b949e", paddingLeft: "0.75rem", marginBottom: "0.25rem" },
  articleLink: { color: "#58a6ff", textDecoration: "none", fontSize: "0.8rem" },
  insightText: { fontSize: "0.875rem", color: "#94a3b8", lineHeight: 1.65, marginBottom: "0.5rem" },
  insightSources: { fontSize: "0.75rem", color: "#4d6073", fontStyle: "italic" },
  gapTitle: { fontSize: "0.875rem", fontWeight: 600, color: "#e6edf3", marginBottom: "0.25rem" },
  gapDetail: { fontSize: "0.82rem", color: "#8b949e", lineHeight: 1.6 },
  conceptBadge: { display: "inline-block", background: "#1c2d3e", border: "1px solid #1f4068", borderRadius: "4px", padding: "2px 8px", fontSize: "0.75rem", color: "#58a6ff", marginRight: "0.4rem", marginBottom: "0.4rem" },
  stat: { textAlign: "center", padding: "0.75rem 1.5rem" },
  statNum: { fontSize: "1.75rem", fontWeight: 700, color: "#58a6ff", fontFamily: "monospace" },
  statLabel: { fontSize: "0.75rem", color: "#8b949e", marginTop: "0.15rem" },
};

export default function Overview() {
  const articleCount = kb.articles.length;
  const insightCount = kb.insights.length;
  const gapCount = kb.suggested_gaps.length;
  const conceptCount = kb.cross_topic_concepts.length;

  return (
    <div>
      {/* Stats bar */}
      <div style={{ background: "#161b22", border: "1px solid #21262d", borderRadius: "8px", display: "flex", justifyContent: "space-around", marginBottom: "2rem", padding: "0.5rem 0" }}>
        {[
          { num: kb.source_count, label: "sources compiled" },
          { num: articleCount, label: "articles" },
          { num: insightCount, label: "cross-source insights" },
          { num: gapCount, label: "suggested gaps" },
        ].map((s) => (
          <div key={s.label} style={S.stat}>
            <div style={S.statNum}>{s.num}</div>
            <div style={S.statLabel}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Knowledge Map */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Knowledge Map</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "0.75rem" }}>
          {kb.domains.map((domain) => (
            <div key={domain.name} style={S.card}>
              <div style={S.domainName}>{domain.name}</div>
              {domain.subtopics.map((st) => (
                <div key={st.name}>
                  <div style={{ ...S.subtopic, color: "#6e7f8d", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", marginTop: "0.4rem" }}>{st.name}</div>
                  {st.article_ids.map((aid) => {
                    const art = kb.articles.find((a) => a.id === aid);
                    return art ? (
                      <div key={aid} style={{ ...S.subtopic }}>
                        → {art.title}
                      </div>
                    ) : null;
                  })}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Cross-domain concepts */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Cross-Domain Concepts</div>
        {kb.cross_topic_concepts.map((c) => (
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

      {/* Cross-source Insights */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Cross-Source Insights</div>
        {kb.insights.map((ins, i) => (
          <div key={i} style={S.card}>
            <div style={S.insightText}>{ins.text}</div>
            <div style={S.insightSources}>Sources: {ins.sources.join(", ")}</div>
          </div>
        ))}
      </div>

      {/* Suggested Gaps */}
      <div style={S.section}>
        <div style={S.sectionTitle}>Suggested Gaps</div>
        {kb.suggested_gaps.map((gap, i) => (
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
