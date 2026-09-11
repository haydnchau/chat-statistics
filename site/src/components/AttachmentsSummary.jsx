const TYPE_ORDER = ["photo", "video", "reel", "post", "story", "link", "gif", "sticker", "voice message"];

export default function AttachmentsSummary({ counts }) {
  const senders = Object.keys(counts);
  const totals = {};
  for (const sender of senders) {
    for (const [type, qty] of Object.entries(counts[sender])) {
      totals[type] = (totals[type] || 0) + qty;
    }
  }
  const types = Object.keys(totals).sort(
    (a, b) => TYPE_ORDER.indexOf(a) - TYPE_ORDER.indexOf(b)
  );

  return (
    <section className="sent">
      <h3 className="sent__title">sent</h3>
      <div className="sent__table-wrap glass">
        <table className="sent__table glass__content">
          <thead>
            <tr>
              <th></th>
              {types.map((t) => (
                <th key={t}>{t}s</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {senders.map((sender) => (
              <tr key={sender}>
                <td className="sent__sender">{sender}</td>
                {types.map((t) => (
                  <td key={t}>{counts[sender][t] || 0}</td>
                ))}
              </tr>
            ))}
            <tr className="sent__total-row">
              <td className="sent__sender">total</td>
              {types.map((t) => (
                <td key={t}>{totals[t]}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}