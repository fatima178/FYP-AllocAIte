import Menu from "../Menu";
import "../../styles/Chatbot.css";
import ChatbotPanel from "../../components/ChatbotPanel";
import { useChatbot } from "../../hooks/useChatbot";

function ChatbotPage() {
  const chatbot = useChatbot();

  return (
    <>
      <Menu />

      <div className="chatbot-full-wrapper">
        <div className="chatbot-full-container">
          <ChatbotPanel
            title="AllocAIte Assistant"
            subtitle="Ask questions about employees, skills, schedules and more."
            {...chatbot}
          />
        </div>
      </div>
    </>
  );
}

export default ChatbotPage;
