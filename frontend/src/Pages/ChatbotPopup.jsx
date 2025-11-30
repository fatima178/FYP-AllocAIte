import { useState, useEffect, useRef } from "react";
import "../styles/Chatbot.css";
import { apiFetch } from "../api";

export default function ChatbotPopup() {
  // controls whether the chatbot popup is visible
  const [open, setOpen] = useState(false);

  // stores the full chat history (user + bot)
  const [messages, setMessages] = useState([]);

  // stores the text the user is currently typing
  const [input, setInput] = useState("");

  // used for automatically scrolling to newest message
  const chatEndRef = useRef(null);

  // scroll to bottom whenever messages update
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // send a message to the backend chatbot
  const sendMessage = async () => {
    // don't allow empty submissions
    if (!input.trim()) return;

    // check if user is logged in
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      // push a warning message from the bot
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Please log in before using the assistant." },
      ]);
      return;
    }

    // add the user's message to chat
    const userMsg = { sender: "user", text: input };
    setMessages(prev => [...prev, userMsg]);

    try {
      // send request to backend chatbot API
      const res = await apiFetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          user_id: Number(userId),
        }),
      });

      // add bot response to chat
      const botMsg = { sender: "bot", text: res.response };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      // fallback message when server fails
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Server error. Try again." },
      ]);
    }

    // reset input
    setInput("");
  };

  // predefined suggestions shown in popup
  const suggestions = [
    "Who is available next week?",
    "Who has Python skills?",
    "What is Emma doing this week?",
    "Show all backend developers"
  ];

  return (
    <>
      {/* Floating chatbot button when popup is closed */}
      {!open && (
        <button className="chatbot-button" onClick={() => setOpen(true)}>
          Chatbot
        </button>
      )}

      {/* Main popup box when open */}
      {open && (
        <div className="chatbot-popup">

          {/* Popup header with title and close button */}
          <div className="chatbot-header">
            <span>AllocAIte Assistant</span>
            <button className="close-btn" onClick={() => setOpen(false)}>×</button>
          </div>

          {/* Chat message list */}
          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.sender}`}>
                {msg.text}
              </div>
            ))}

            {/* Invisible anchor used for auto-scroll */}
            <div ref={chatEndRef}></div>
          </div>

          {/* Suggested quick questions */}
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

          {/* Input area + send button */}
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
