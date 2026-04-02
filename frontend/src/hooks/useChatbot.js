import { useEffect, useRef, useState } from "react";

import { apiFetch } from "../api";
import { getSessionItem } from "../session";

export function useChatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const chatEndRef = useRef(null);
  const nextMessageIdRef = useRef(1);

  const createMessage = (sender, text) => ({
    id: nextMessageIdRef.current++,
    sender,
    text,
  });

  useEffect(() => {
    if (!chatEndRef.current || messages.length === 0) {
      return;
    }
    chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const userId = getSessionItem("user_id");
    if (!userId) {
      setSuggestions([]);
      return;
    }

    let active = true;

    const loadSuggestions = async () => {
      try {
        const res = await apiFetch(`/chatbot/suggestions?user_id=${Number(userId)}`);
        if (active) {
          setSuggestions(Array.isArray(res.suggestions) ? res.suggestions : []);
        }
      } catch {
        if (active) {
          setSuggestions([]);
        }
      }
    };

    loadSuggestions();

    return () => {
      active = false;
    };
  }, []);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const userId = getSessionItem("user_id");
    if (!userId) {
      setMessages((prev) => [
        ...prev,
        createMessage("bot", "Please log in before using the assistant."),
      ]);
      return;
    }

    setMessages((prev) => [...prev, createMessage("user", trimmed)]);

    try {
      const res = await apiFetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          user_id: Number(userId),
        }),
      });

      setMessages((prev) => [...prev, createMessage("bot", res.response)]);
    } catch {
      setMessages((prev) => [
        ...prev,
        createMessage("bot", "Server error. Try again."),
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
    suggestions,
  };
}
