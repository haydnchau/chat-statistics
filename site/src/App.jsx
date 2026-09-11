import { useEffect, useState } from "react";
import ChatList from "./components/ChatList.jsx";
import WordRanking from "./components/WordRanking.jsx";
import EmptyState from "./components/EmptyState.jsx";
import Overview from "./components/Overview.jsx";

function GlassFilter() {
  // SVG turbulence + displacement, applied via `filter: url(#glass-distortion)`
  // in index.css. This is what actually refracts the backdrop instead of
  // just blurring it flat.
  return (
    <svg style={{ position: "absolute", width: 0, height: 0 }} aria-hidden="true">
      <filter id="glass-distortion" x="-20%" y="-20%" width="140%" height="140%">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.009 0.012"
          numOctaves="2"
          seed="7"
          result="noise"
        />
        <feGaussianBlur in="noise" stdDeviation="2" result="softNoise" />
        <feDisplacementMap
          in="SourceGraphic"
          in2="softNoise"
          scale="26"
          xChannelSelector="R"
          yChannelSelector="G"
        />
      </filter>
    </svg>
  );
}

function useTheme() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("chatstats-theme");
    if (saved) return saved;
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("chatstats-theme", theme);
  }, [theme]);

  return [theme, setTheme];
}

export default function App() {
  const [manifest, setManifest] = useState(null);
  const [manifestError, setManifestError] = useState(false);
  const [page, setPage] = useState("overview"); // "overview" | a chat's filename
  const [chatData, setChatData] = useState(null);
  const [overview, setOverview] = useState(null);
  const [overviewError, setOverviewError] = useState(false);
  const [theme, setTheme] = useTheme();

  // Load the list of processed chats once on mount.
  useEffect(() => {
    fetch("/data/manifest.json")
      .then((r) => {
        if (!r.ok) throw new Error("no manifest");
        return r.json();
      })
      .then(setManifest)
      .catch(() => setManifestError(true));
  }, []);

  // Load the cross-chat overview once on mount.
  useEffect(() => {
    fetch("/data/overview.json")
      .then((r) => {
        if (!r.ok) throw new Error("no overview");
        return r.json();
      })
      .then(setOverview)
      .catch(() => setOverviewError(true));
  }, []);

  // Load the selected chat's word-frequency data whenever it changes.
  useEffect(() => {
    if (page === "overview") {
      setChatData(null);
      return;
    }
    fetch(`/data/${page}`)
      .then((r) => r.json())
      .then(setChatData);
  }, [page]);

  const hasChats = manifest && manifest.length > 0;

  return (
    <div className="layout">
      <GlassFilter />

      <aside className="sidebar">
        <h1 className="wordmark">ChatStats</h1>

        <button
          className={
            "chat-item nav-item" + (page === "overview" ? " chat-item--active" : "")
          }
          onClick={() => setPage("overview")}
        >
          <span className="chat-item__title">Overview</span>
        </button>

        <div className="sidebar__scroll">
          {hasChats && (
            <ChatList chats={manifest} activeFile={page} onSelect={setPage} />
          )}
        </div>

        <button
          className="theme-toggle glass"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          <span className="glass__content" style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="theme-toggle__dot" />
            {theme === "dark" ? "Dark mode" : "Light mode"}
          </span>
        </button>
      </aside>

      <main className="stage">
        {page === "overview" && (
          <Overview data={overview} error={overviewError} />
        )}

        {page !== "overview" && manifestError && (
          <EmptyState
            heading="No data yet"
            body="Run python3 process_chat.py from the project root to generate stats for a chat, then refresh this page."
          />
        )}
        {page !== "overview" && !manifestError && !hasChats && (
          <EmptyState
            heading="Nothing processed yet"
            body="Run python3 process_chat.py, pick a conversation, then refresh this page."
          />
        )}
        {page !== "overview" && chatData && <WordRanking data={chatData} />}
      </main>
    </div>
  );
}