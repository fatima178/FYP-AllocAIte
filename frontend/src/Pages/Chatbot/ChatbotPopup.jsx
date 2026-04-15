import { useState } from "react";
import "../../styles/Chatbot.css";
import ChatbotPanel from "../../components/ChatbotPanel";
import { useChatbot } from "../../hooks/useChatbot";

export default function ChatbotPopup() {
  // popup starts closed so it does not cover the page
  const [open, setOpen] = useState(false);
  // shared chatbot state so the popup behaves the same as the main chatbot page
  const chatbot = useChatbot();

  return (
    <>
      {/* small button shown in the corner until the user opens the assistant */}
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
