import { useState } from "react";
import Overview from "./components/Overview";
import Articles from "./components/Articles";
import QA from "./components/QA";
import About from "./components/About";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "articles", label: "Articles" },
  { id: "qa", label: "Q&A" },
  { id: "about", label: "About" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div style={{ minHeight: "100vh", background: "#0d1117", color: "#e6edf3" }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid #21262d", background: "#161b22" }}>
        <div style={{ maxWidth: "900px", margin: "0 auto", padding: "1rem 1.5rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span style={{ fontFamily: "monospace", fontSize: "1.2rem", fontWeight: 700, color: "#58a6ff", letterSpacing: "-0.02em" }}>
              KOMPILE
            </span>
            <span style={{ color: "#8b949e", fontSize: "0.82rem" }}>
              AI conversations → structured knowledge
            </span>
          </div>
          <a
            href="https://github.com/yourusername/kompile"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#8b949e", fontSize: "0.8rem", textDecoration: "none" }}
          >
            GitHub ↗
          </a>
        </div>
        {/* Tabs */}
        <div style={{ maxWidth: "900px", margin: "0 auto", padding: "0 1.5rem", display: "flex" }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "0.5rem 1rem",
                fontSize: "0.875rem",
                background: "none",
                border: "none",
                cursor: "pointer",
                color: activeTab === tab.id ? "#e6edf3" : "#8b949e",
                borderBottom: activeTab === tab.id ? "2px solid #58a6ff" : "2px solid transparent",
                fontFamily: "inherit",
                transition: "color 0.15s",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* Content */}
      <main style={{ maxWidth: "900px", margin: "0 auto", padding: "2rem 1.5rem" }}>
        {activeTab === "overview" && <Overview />}
        {activeTab === "articles" && <Articles />}
        {activeTab === "qa" && <QA />}
        {activeTab === "about" && <About />}
      </main>
    </div>
  );
}
