import { useMemo, useState } from "react";

export default function ChatsPage({ chats, onSelect }) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return chats;
    return chats.filter((c) => {
      if (c.title?.toLowerCase().includes(q)) return true;
      return (c.participants || []).some((p) => p.toLowerCase().includes(q));
    });
  }, [chats, query]);

  const sorted = useMemo(
    () => [...filtered].sort((a, b) => b.message_count - a.message_count),
    [filtered]
  );

  return (
    <div className="ranking">
      <header className="ranking__header">
        <h2 className="ranking__title">Chats</h2>
        <p className="ranking__subtitle">
          {chats.length.toLocaleString()} conversation{chats.length === 1 ? "" : "s"}
        </p>
      </header>

      <input
        className="chats-search glass"
        type="text"
        placeholder="Search by name..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {sorted.length === 0 ? (
        <p className="empty-state__body" style={{ marginTop: 20 }}>
          No chats match "{query}".
        </p>
      ) : (
        <div className="chats-grid">
          {sorted.map((chat) => (
            <button
              key={chat.file}
              className="chat-card glass"
              onClick={() => onSelect(chat.file)}
            >
              <div className="glass__content">
                <p className="chat-card__title">{chat.title}</p>
                <p className="chat-card__meta">
                  {chat.message_count.toLocaleString()} messages
                  {chat.participants?.length > 2
                    ? ` · ${chat.participants.length} people`
                    : ""}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}