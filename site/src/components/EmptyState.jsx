export default function EmptyState({ heading, body }) {
  return (
    <div className="empty-state">
      <p className="empty-state__heading">{heading}</p>
      <p className="empty-state__body">{body}</p>
    </div>
  );
}