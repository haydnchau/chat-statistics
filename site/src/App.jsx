import { useEffect, useState } from "react";
import ChatList from "./components/ChatList.jsx";
import WordRanking from "./components/WordRanking.jsx";
import EmptyState from "./components/EmptyState.jsx";

export default function App() {
  const [manifest, setManifest] = useState(null);
  const [manifestError, setManifestError] = useState(false);
  const [activeFile, setActiveFile] = useState(null);
  const [chatData, setChatData] = useState(null);

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

  // Load the selected chat's word-frequency data whenever it changes.
  useEffect(() => {
    if (!activeFile) {
      setChatData(null);
      return;
    }
    fetch(`/data/${activeFile}`)
      .then((r) => r.json())
      .then(setChatData);
  }, [activeFile]);

  const hasChats = manifest && manifest.length > 0;

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1 className="wordmark">wordcount</h1>
        {hasChats && (
          <ChatList
            chats={manifest}
            activeFile={activeFile}
            onSelect={setActiveFile}
          />
        )}
      </aside>

      <main className="stage">
        {manifestError && (
          <EmptyState
            heading="No data yet"
            body="Run python3 process_chat.py from the project root to generate stats for a chat, then refresh this page."
          />
        )}
        {!manifestError && !hasChats && (
          <EmptyState
            heading="Nothing processed yet"
            body="Run python3 process_chat.py, pick a conversation, then refresh this page."
          />
        )}
        {hasChats && !activeFile && (
          <EmptyState
            heading="Pick a chat"
            body="Choose a conversation on the left to see its most-used words."
          />
        )}
        {activeFile && chatData && <WordRanking data={chatData} />}
      </main>
    </div>
  );
}
