import { useState, useEffect, useRef } from "react";
import "../styles/Chatbot.css";
import { apiFetch } from "../api";

export default function ChatbotPopup() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const chatEndRef = useRef(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userId = localStorage.getItem("user_id");
    if (!userId) {
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Please log in before using the assistant." },
      ]);
      return;
    }

    const userMsg = { sender: "user", text: input };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await apiFetch("/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input, user_id: Number(userId) }),
      });
      const botMsg = { sender: "bot", text: res.response };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Server error. Try again." },
      ]);
    }

    setInput("");
  };

  const suggestions = [
    "Who is available next week?",
    "Who has Python skills?",
    "What is Emma doing this week?",
    "Show all backend developers"
  ];

  return (
    <>
      {/* Floating “Chatbot” Button */}
      {!open && (
        <button className="chatbot-button" onClick={() => setOpen(true)}>
          Chatbot
        </button>
      )}

      {/* Chatbot Popup */}
      {open && (
        <div className="chatbot-popup">
          <div className="chatbot-header">
            <span>AllocAIte Assistant</span>
            <button className="close-btn" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.sender}`}>
                {msg.text}
              </div>
            ))}
            <div ref={chatEndRef}></div>
          </div>

          <div className="suggestions">
            <span>Suggestions:</span>
            <div className="suggestion-list">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  className="suggestion-btn"
                  onClick={() => setInput(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="chatbot-input-area">
            <input
              type="text"
              placeholder="Type message..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      )}
    </>
  );
}
