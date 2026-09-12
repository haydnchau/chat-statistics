import { useState } from "react";
import AttachmentsSummary from "./AttachmentsSummary.jsx";
import ReactionsSummary from "./ReactionsSummary.jsx";

const COLLAPSED_COUNT = 12;

export default function WordRanking({ data, onBack }) {
  const senders = Object.keys(data.top_words_by_sender);
  const [view, setView] = useState("overall"); // "overall" | sender name
  const [expanded, setExpanded] = useState(false);

  const words =
    view === "overall"
      ? data.top_words_overall
      : data.top_words_by_sender[view] || [];

  const maxCount = words.length ? words[0][1] : 1;
  const visibleWords = expanded ? words : words.slice(0, COLLAPSED_COUNT);
  const hasMore = words.length > COLLAPSED_COUNT;

  function selectView(name) {
    setView(name);
    setExpanded(false);
  }

  // Per-member breakdown: how many messages and words each person sent in
  // this chat. message_counts comes straight from process_chat.py; word
  // totals are derived by summing each sender's full top_words_by_sender
  // list (no longer capped at 50, so this sum is accurate).
  const messageCounts = data.message_counts || {};
  const members = Array.from(
    new Set([...Object.keys(messageCounts), ...senders])
  )
    .map((name) => ({
      name,
      messages: messageCounts[name] || 0,
      words: (data.top_words_by_sender[name] || []).reduce(
        (sum, [, count]) => sum + count,
        0
      ),
    }))
    .sort((a, b) => b.messages - a.messages);
  const memberTotals = members.reduce(
    (totals, m) => ({
      messages: totals.messages + m.messages,
      words: totals.words + m.words,
    }),
    { messages: 0, words: 0 }
  );

  return (
    <div className="ranking">
      <header className="ranking__header">
        {onBack && (
          <button className="back-link" onClick={onBack}>
            <span aria-hidden="true">&#8592;</span> Chats
          </button>
        )}
        <h2 className="ranking__title">{data.title}</h2>
        <p className="ranking__subtitle">
          {data.total_words.toLocaleString()} words counted
        </p>
      </header>

      <div className="tabs">
        <button
          className={"tab" + (view === "overall" ? " tab--active" : "")}
          onClick={() => selectView("overall")}
        >
          everyone
        </button>
        {senders.map((name) => (
          <button
            key={name}
            className={"tab" + (view === name ? " tab--active" : "")}
            onClick={() => selectView(name)}
          >
            {name}
          </button>
        ))}
      </div>

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
            <button className="expand-btn glass" onClick={() => setExpanded(true)}>
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

      {members.length > 0 && (
        <section className="sent">
          <h3 className="sent__title">members</h3>
          <div className="sent__table-wrap glass">
            <div className="glass__content">
              <table className="sent__table">
                <thead>
                  <tr>
                    <th></th>
                    <th>messages</th>
                    <th>words</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <tr key={m.name}>
                      <td className="sent__sender">{m.name}</td>
                      <td>{m.messages.toLocaleString()}</td>
                      <td>{m.words.toLocaleString()}</td>
                    </tr>
                  ))}
                  <tr className="sent__total-row">
                    <td className="sent__sender">total</td>
                    <td>{memberTotals.messages.toLocaleString()}</td>
                    <td>{memberTotals.words.toLocaleString()}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {data.attachment_counts && Object.keys(data.attachment_counts).length > 0 && (
        <AttachmentsSummary counts={data.attachment_counts} />
      )}

      {data.reaction_counts && Object.keys(data.reaction_counts).length > 0 && (
        <ReactionsSummary
          counts={data.reaction_counts}
          emojiCounts={data.reaction_emoji_counts}
        />
      )}

      {data.most_stretched_words?.length > 0 && (
        <section className="stretched">
          <h3 className="stretched__title">most stretched</h3>
          <ul className="stretched__list">
            {data.most_stretched_words.slice(0, 8).map((item) => (
              <li key={item.word} className="stretched__item">
                <span className="stretched__longest">{item.variants[0]}</span>
                <span className="stretched__arrow">&#8594;</span>
                <span className="stretched__canonical">{item.word}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}