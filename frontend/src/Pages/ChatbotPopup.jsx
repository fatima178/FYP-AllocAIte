import { useState } from "react";
import "../styles/Chatbot.css";
import ChatbotPanel from "../components/ChatbotPanel";
import { useChatbot } from "../hooks/useChatbot";

export default function ChatbotPopup() {
  const [open, setOpen] = useState(false);
  const chatbot = useChatbot();

  return (
    <>
      {!open && (
        <button className="chatbot-button" onClick={() => setOpen(true)}>
          Chatbot
        </button>
      )}

      {open && (
        <div className="chatbot-popup">
          <ChatbotPanel
            title="AllocAIte Assistant"
            variant="popup"
            onClose={() => setOpen(false)}
            {...chatbot}
          />
        </div>
      )}
    </>
  );
}
