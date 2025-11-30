import { useState, useEffect, useRef } from "react";
import Menu from "./Menu";
import "../styles/Chatbot.css";
import { apiFetch } from "../api";

function ChatbotPage() {
  // stores all messages shown in the chat (both user + bot)
  const [messages, setMessages] = useState([]);

  // stores the user's current input
  const [input, setInput] = useState("");

  // reference used to scroll to the bottom automatically
  const chatEndRef = useRef(null);

  // auto-scroll whenever messages update
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // sends a message to the backend and updates UI
  const sendMessage = async () => {
    // ignore empty messages
    if (!input.trim()) return;

    // check if the user is logged in
    const userId = localStorage.getItem("user_id");
    if (!userId) {
      // add message telling user to log in
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Please log in before using the assistant." },
      ]);
      return;
    }

    // push user's own message to chat window
    const userMsg = { sender: "user", text: input };
    setMessages(prev => [...prev, userMsg]);

    try {
      // backend chatbot request
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
      // fallback if server returns an error
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Server error. Try again." },
      ]);
    }

    // clear the input box
    setInput("");
  };

  // common example queries to assist the user
  const suggestions = [
    "Who is available next week?",
    "Who has Python skills?",
    "What is Emma doing this week?",
    "Show all backend developers",
  ];

  return (
    <>
      {/* top navigation bar */}
      <Menu />

      <div className="chatbot-full-wrapper">
        <div className="chatbot-full-container">

          {/* header text for the chatbot page */}
          <h1 className="chatbot-title">AllocAIte Assistant</h1>
          <p className="chatbot-subtitle">
            Ask questions about employees, skills, schedules and more.
          </p>

          {/* message list container */}
          <div className="chatbot-full-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.sender}`}>
                {msg.text}
              </div>
            ))}

            {/* auto-scroll anchor */}
            <div ref={chatEndRef}></div>
          </div>

          {/* pre-defined suggestion buttons */}
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

          {/* chat input field and send button */}
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
