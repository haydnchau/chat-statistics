function asEmojiPresentation(str) {
  // Some reaction emoji (like a plain heart) render as a monochrome glyph
  // without the emoji variation selector (U+FE0F), inheriting the page's
  // text color instead of showing as colorful. Force it.
  return str.endsWith("\uFE0F") ? str : str + "\uFE0F";
}

export default function ReactionsSummary({ counts, emojiCounts }) {
  const ranked = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const maxCount = ranked.length ? ranked[0][1] : 1;
  const emojis = Object.entries(emojiCounts || {}).sort((a, b) => b[1] - a[1]);

  return (
    <section className="sent">
      <h3 className="sent__title">reactions given</h3>

      <ol className="word-bars">
        {ranked.map(([sender, count], i) => (
          <li className="word-bar" key={sender}>
            <span className="word-bar__rank">{i + 1}</span>
            <span className="word-bar__word">{sender}</span>
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

      {emojis.length > 0 && (
        <div className="emoji-chips">
          {emojis.slice(0, 10).map(([emoji, count]) => (
            <span className="emoji-chip glass" key={emoji}>
              <span className="glass__content">
                <span className="emoji-chip__emoji">{asEmojiPresentation(emoji)}</span>
                <span className="emoji-chip__count">{count}</span>
              </span>
            </span>
          ))}
        </div>
      )}
    </section>
  );
}