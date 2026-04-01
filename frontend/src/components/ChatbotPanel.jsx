export default function ChatbotPanel({
  title,
  subtitle,
  messages,
  input,
  setInput,
  sendMessage,
  chatEndRef,
  suggestions,
  variant = "full",
  onClose,
}) {
  const isPopup = variant === "popup";

  return (
    <>
      {isPopup ? (
        <div className="chatbot-header">
          <span>{title}</span>
          {onClose ? (
            <button className="close-btn" onClick={onClose}>×</button>
          ) : null}
        </div>
      ) : (
        <>
          <h1 className="chatbot-title">{title}</h1>
          <p className="chatbot-subtitle">{subtitle}</p>
        </>
      )}

      <div className={isPopup ? "chatbot-messages" : "chatbot-full-messages"}>
        {messages.map((msg, index) => (
          <div key={`${msg.sender}-${index}`} className={`chat-msg ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        <div ref={chatEndRef}></div>
      </div>

      <div className={isPopup ? "suggestions" : "chatbot-full-suggestions"}>
        <span>Suggestions:</span>
        <div className="suggestion-list">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="suggestion-btn"
              onClick={() => setInput(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      <div className="chatbot-input-area">
        <input
          type="text"
          placeholder={isPopup ? "Type message..." : "Type your question..."}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && sendMessage()}
        />
        <button type="button" onClick={sendMessage}>Send</button>
      </div>
    </>
  );
}
