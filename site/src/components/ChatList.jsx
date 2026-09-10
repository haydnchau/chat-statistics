export default function ChatList({ chats, activeFile, onSelect }) {
  return (
    <nav className="chat-list">
      {chats.map((chat) => (
        <button
          key={chat.file}
          className={"chat-item" + (chat.file === activeFile ? " chat-item--active" : "")}
          onClick={() => onSelect(chat.file)}
        >
          <span className="chat-item__title">{chat.title}</span>
          <span className="chat-item__count">{chat.message_count.toLocaleString()}</span>
        </button>
      ))}
    </nav>
  );
}
