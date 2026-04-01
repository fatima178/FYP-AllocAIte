import { useEffect, useRef, useState } from "react";

import { apiFetch } from "../api";
import { getSessionItem } from "../session";

const DEFAULT_SUGGESTIONS = [
  "Who is available next week?",
  "Who has Python skills?",
  "What is Emma doing this week?",
  "Show all backend developers",
];

export function useChatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (!chatEndRef.current || messages.length === 0) {
      return;
    }
    chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const userId = getSessionItem("user_id");
    if (!userId) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Please log in before using the assistant." },
      ]);
      return;
    }

    setMessages((prev) => [...prev, { sender: "user", text: trimmed }]);

    try {
      const res = await apiFetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          user_id: Number(userId),
        }),
      });

      setMessages((prev) => [...prev, { sender: "bot", text: res.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Server error. Try again." },
      ]);
    } finally {
      setInput("");
    }
  };

  return {
    messages,
    input,
    setInput,
    sendMessage,
    chatEndRef,
    suggestions: DEFAULT_SUGGESTIONS,
  };
}
