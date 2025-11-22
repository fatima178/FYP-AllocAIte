import { useState, useEffect, useRef } from "react";
import Menu from "./Menu";
import "../styles/Chatbot.css";
import { apiFetch } from "../api";

function ChatbotPage() {
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
        { sender: "bot", text: "Server error. Try again." }
      ]);
    }

    setInput("");
  };

  const suggestions = [
    "Who is available next week?",
    "Who has Python skills?",
    "What is Emma doing this week?",
    "Show all backend developers",
  ];

  return (
    <>
      <Menu />

      <div className="chatbot-full-wrapper">

        <div className="chatbot-full-container">

          <h1 className="chatbot-title">AllocAIte Assistant</h1>
          <p className="chatbot-subtitle">Ask questions about employees, skills, schedules and more.</p>

          <div className="chatbot-full-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.sender}`}>
                {msg.text}
              </div>
            ))}
            <div ref={chatEndRef}></div>
          </div>

          <div className="chatbot-full-suggestions">
            <span>Suggestions:</span>
            <div className="suggestion-list">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setInput(s)}
                  className="suggestion-btn"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="chatbot-input-area">
            <input
              type="text"
              placeholder="Type your question..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage}>Send</button>
          </div>

        </div>
      </div>
    </>
  );
}

export default ChatbotPage;
