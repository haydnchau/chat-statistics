import { useState } from "react";

export default function WordRanking({ data }) {
  const senders = Object.keys(data.top_words_by_sender);
  const [view, setView] = useState("overall"); // "overall" | sender name

  const words =
    view === "overall"
      ? data.top_words_overall
      : data.top_words_by_sender[view] || [];

  const maxCount = words.length ? words[0][1] : 1;

  return (
    <div className="ranking">
      <header className="ranking__header">
        <h2 className="ranking__title">{data.title}</h2>
        <p className="ranking__subtitle">
          {data.total_words.toLocaleString()} words counted
        </p>
      </header>

      <div className="tabs">
        <button
          className={"tab" + (view === "overall" ? " tab--active" : "")}
          onClick={() => setView("overall")}
        >
          everyone
        </button>
        {senders.map((name) => (
          <button
            key={name}
            className={"tab" + (view === name ? " tab--active" : "")}
            onClick={() => setView(name)}
          >
            {name}
          </button>
        ))}
      </div>

      <ol className="word-bars">
        {words.slice(0, 40).map(([word, count], i) => (
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
