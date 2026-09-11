import { useState } from "react";

const COLLAPSED_COUNT = 12;

export default function Overview({ data, error }) {
  const [expanded, setExpanded] = useState(false);

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

  return (
    <div className="ranking">
      <header className="ranking__header">
        <h2 className="ranking__title">Overview</h2>
        <p className="ranking__subtitle">
          {data.chat_count} conversations · {data.you}
        </p>
      </header>

      <div className="stat-grid">
        <div className="stat-card glass">
          <div className="glass__content">
            <p className="stat-card__value">
              {data.total_messages_sent.toLocaleString()}
            </p>
            <p className="stat-card__label">messages sent</p>
          </div>
        </div>

        {data.most_active_chat && (
          <div className="stat-card glass">
            <div className="glass__content">
              <p className="stat-card__value">
                {data.most_active_chat.message_count.toLocaleString()}
              </p>
              <p className="stat-card__label">most active</p>
              <p className="stat-card__sub">{data.most_active_chat.title}</p>
            </div>
          </div>
        )}

        {data.total_reactions_given != null && (
          <div className="stat-card glass">
            <div className="glass__content">
              <p className="stat-card__value">
                {data.total_reactions_given.toLocaleString()}
              </p>
              <p className="stat-card__label">reactions given</p>
            </div>
          </div>
        )}
      </div>

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