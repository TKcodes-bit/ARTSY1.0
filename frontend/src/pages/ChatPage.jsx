import { useEffect, useState } from "react";
import api from "../api";
import { useAuth } from "../context/AuthContext.jsx";

export default function ChatPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [activeConvo, setActiveConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");

  async function loadConversations() {
    const res = await api.get("/chat/conversations");
    setConversations(res.data);
    if (!activeConvo && res.data.length > 0) {
      setActiveConvo(res.data[0]);
    }
  }

  async function loadMessages(conversationId) {
    const res = await api.get(`/chat/messages/${conversationId}`);
    setMessages(res.data);
  }

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (!activeConvo) return;
    loadMessages(activeConvo._id);
    const id = setInterval(() => {
      loadMessages(activeConvo._id);
    }, 3000);
    return () => clearInterval(id);
  }, [activeConvo?._id]);

  async function sendMessage(e) {
    e.preventDefault();
    if (!text.trim() || !activeConvo) return;
    const res = await api.post(`/chat/messages/${activeConvo._id}`, { text });
    setMessages((prev) => [...prev, res.data]);
    setText("");
  }

  return (
    <div className="chat-layout">
      <aside className="chat-sidebar">
        <h3>Conversations</h3>
        {conversations.map((c) => {
          const other = c.participants.find((p) => p._id !== user.id);
          return (
            <button
              key={c._id}
              className={activeConvo?._id === c._id ? "chat-item active" : "chat-item"}
              onClick={() => setActiveConvo(c)}
            >
              {other?.name || "Unknown"}
            </button>
          );
        })}
        {conversations.length === 0 && <p>No conversations yet.</p>}
      </aside>
      <section className="chat-main">
        {activeConvo ? (
          <>
            <div className="chat-messages">
              {messages.map((m) => (
                <div
                  key={m._id}
                  className={
                    m.sender._id === user.id ? "chat-message mine" : "chat-message theirs"
                  }
                >
                  <div className="chat-text">{m.text}</div>
                  <div className="chat-meta">
                    {new Date(m.createdAt).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
            <form className="chat-input-bar" onSubmit={sendMessage}>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Send a message..."
              />
              <button type="submit">Send</button>
            </form>
          </>
        ) : (
          <p>Select a conversation to start chatting.</p>
        )}
      </section>
    </div>
  );
}

