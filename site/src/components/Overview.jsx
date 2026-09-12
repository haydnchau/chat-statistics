import { useEffect, useState } from "react";

const COLLAPSED_COUNT = 12;

// Some reaction emoji (like a plain heart) render as a monochrome glyph
// without the emoji variation selector (U+FE0F), inheriting the page's
// text color instead of showing as colorful. Force it, same as
// ReactionsSummary.jsx does for the per-chat view.
function asEmojiPresentation(str) {
  return str.endsWith("\uFE0F") ? str : str + "\uFE0F";
}

function StatModal({ title, items, valueLabel, formatLabel, onClose }) {
  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const maxCount = items.length ? items[0].count : 1;
  const label = formatLabel || ((x) => x);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal glass"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="glass__content">
          <div className="modal__header">
            <h3 className="modal__title">{title}</h3>
            <button className="modal__close" onClick={onClose} aria-label="Close">
              ×
            </button>
          </div>

          {items.length === 0 ? (
            <p className="empty-state__body">Nothing here yet.</p>
          ) : (
            <ol className="word-bars">
              {items.map((item, i) => (
                <li className="word-bar" key={item.file || item.title}>
                  <span className="word-bar__rank">{i + 1}</span>
                  <span className="word-bar__word">{label(item.title)}</span>
                  <span className="word-bar__track">
                    <span
                      className="word-bar__fill"
                      style={{ width: `${(item.count / maxCount) * 100}%` }}
                    />
                  </span>
                  <span className="word-bar__count">
                    {item.count.toLocaleString()}
                    {valueLabel ? ` ${valueLabel}` : ""}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Overview({ data, error }) {
  const [expanded, setExpanded] = useState(false);
  const [openStat, setOpenStat] = useState(null); // "messages" | "words" | "active" | "reactions"

  if (error) {
    return (
      <div className="ranking">
        <header className="ranking__header">
          <h2 className="ranking__title">Overview</h2>
        </header>
        <p className="empty-state__body">
          No overview yet. Run python3 process_chat.py on a couple of
          conversations first, then refresh this page.
        </p>
      </div>
    );
  }

  if (!data) return null; // still loading

  if (!data.you) {
    return (
      <div className="ranking">
        <header className="ranking__header">
          <h2 className="ranking__title">Overview</h2>
        </header>
        <p className="empty-state__body">
          Process at least one more conversation so I can figure out which
          participant is you (the name common to every chat), then refresh.
        </p>
      </div>
    );
  }

  const words = data.top_words_mine || [];
  const maxCount = words.length ? words[0][1] : 1;
  const visibleWords = expanded ? words : words.slice(0, COLLAPSED_COUNT);
  const hasMore = words.length > COLLAPSED_COUNT;

  // Config for the popup each stat card opens. Only stats with per-chat
  // breakdown data available get made clickable.
  const statModals = {
    messages: {
      title: "Messages sent, by chat",
      items: data.messages_by_chat || [],
      valueLabel: "",
    },
    words: {
      title: "Words sent, by chat",
      items: data.words_by_chat || [],
      valueLabel: "",
    },
    active: {
      title: "Most active chats",
      items: (data.active_chats || []).map((c) => ({
        file: c.file,
        title: c.title,
        count: c.message_count,
      })),
      valueLabel: "total",
    },
    reactions: {
      title: "Reactions you've given",
      items: (data.reaction_emojis_mine || []).map(([emoji, count]) => ({
        title: emoji,
        count,
      })),
      formatLabel: asEmojiPresentation,
    },
  };

  return (
    <div className="ranking">
      <header className="ranking__header">
        <h2 className="ranking__title">Overview</h2>
        <p className="ranking__subtitle">
          {data.chat_count} conversations · {data.you}
        </p>
      </header>

      <div className="stat-grid">
        <button className="stat-card glass" onClick={() => setOpenStat("messages")}>
          <div className="glass__content">
            <p className="stat-card__value">
              {data.total_messages_sent.toLocaleString()}
            </p>
            <p className="stat-card__label">messages sent</p>
          </div>
        </button>

        {data.total_words_mine != null && (
          <button className="stat-card glass" onClick={() => setOpenStat("words")}>
            <div className="glass__content">
              <p className="stat-card__value">
                {data.total_words_mine.toLocaleString()}
              </p>
              <p className="stat-card__label">words sent</p>
            </div>
          </button>
        )}

        {data.most_active_chat && (
          <button className="stat-card glass" onClick={() => setOpenStat("active")}>
            <div className="glass__content">
              <p className="stat-card__value">
                {data.most_active_chat.message_count.toLocaleString()}
              </p>
              <p className="stat-card__label">most active</p>
              <p className="stat-card__sub">{data.most_active_chat.title}</p>
            </div>
          </button>
        )}

        {data.total_reactions_given != null && (
          <button className="stat-card glass" onClick={() => setOpenStat("reactions")}>
            <div className="glass__content">
              <p className="stat-card__value">
                {data.total_reactions_given.toLocaleString()}
              </p>
              <p className="stat-card__label">reactions given</p>
            </div>
          </button>
        )}
      </div>

      {openStat && (
        <StatModal
          title={statModals[openStat].title}
          items={statModals[openStat].items}
          valueLabel={statModals[openStat].valueLabel}
          formatLabel={statModals[openStat].formatLabel}
          onClose={() => setOpenStat(null)}
        />
      )}

      {data.attachments_sent && Object.keys(data.attachments_sent).length > 0 && (
        <section className="section">
          <h3 className="section-title">Things you've sent</h3>
          <div className="emoji-chips">
            {Object.entries(data.attachments_sent).map(([type, count]) => (
              <span className="stat-chip glass" key={type}>
                <span className="glass__content">
                  <span className="stat-chip__count">{count.toLocaleString()}</span>
                  <span className="stat-chip__label">
                    {type}
                    {count === 1 ? "" : "s"}
                  </span>
                </span>
              </span>
            ))}
          </div>
        </section>
      )}

      {words.length > 0 && (
        <section className="section">
          <h3 className="section-title">Your top words</h3>

          <div className="word-bars-wrap">
            <ol className="word-bars">
              {visibleWords.map(([word, count], i) => (
                <li className="word-bar" key={word}>
                  <span className="word-bar__rank">{i + 1}</span>
                  <span className="word-bar__word">{word}</span>
                  <span className="word-bar__track">
                    <span
                      className="word-bar__fill"
                      style={{ width: `${(count / maxCount) * 100}%` }}
                    />
                  </span>
                  <span className="word-bar__count">{count}</span>
                </li>
              ))}
            </ol>

            {hasMore && !expanded && (
              <div className="word-bars-fade">
                <button
                  className="expand-btn glass"
                  onClick={() => setExpanded(true)}
                >
                  <span className="glass__content">
                    Show all {words.length} words
                  </span>
                </button>
              </div>
            )}
          </div>

          {hasMore && expanded && (
            <button
              className="expand-btn expand-btn--standalone glass"
              onClick={() => setExpanded(false)}
            >
              <span className="glass__content">Show fewer</span>
            </button>
          )}
        </section>
      )}
    </div>
  );
}