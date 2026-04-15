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
  // popup and full page use the same component with slightly different layout
  const isPopup = variant === "popup";
  const hasMessages = messages.length > 0;

  return (
    <div className={`chatbot-shell ${isPopup ? "is-popup" : "is-full"}`}>
      <div className="chatbot-panel-header">
        <div className="chatbot-panel-heading">
          <span className="chatbot-kicker">AI Assistant</span>
          {isPopup ? (
            <h2 className="chatbot-panel-title chatbot-panel-title--popup">{title}</h2>
          ) : (
            <>
              <h1 className="chatbot-panel-title">{title}</h1>
              <p className="chatbot-panel-subtitle">{subtitle}</p>
            </>
          )}
        </div>
        {isPopup && onClose ? (
          <button className="close-btn" type="button" onClick={onClose} aria-label="Close chatbot">
            ×
          </button>
        ) : null}
      </div>

      <div className="chatbot-message-panel">
        {/* empty state only appears on the full chatbot page before any messages */}
        {!hasMessages && !isPopup ? (
          <div className="chatbot-empty-state">
            <div className="chatbot-empty-icon">A</div>
            <div className="chatbot-empty-copy">
              <h3>Ask about your team</h3>
              <p>
                Check availability, skills, assignments, and employee details using plain language.
              </p>
            </div>
          </div>
        ) : null}

        <div className="chatbot-messages">
          {/* render each user/bot message with a different css class */}
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-msg-row ${msg.sender}`}>
              <div className={`chat-msg ${msg.sender}`}>
                {msg.text}
              </div>
            </div>
          ))}
          <div ref={chatEndRef}></div>
        </div>
      </div>

      <div className="chatbot-suggestions">
        <div className="chatbot-suggestions-header">
          {isPopup ? "Try one of these" : "Try a prompt"}
        </div>
        <div className="suggestion-list">
          {/* clicking a suggestion fills the input so the user can edit or send it */}
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
        {/* enter key sends the current message, same as clicking Send */}
        <input
          type="text"
          placeholder={isPopup ? "Type message..." : "Type your question..."}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && sendMessage()}
        />
        <button type="button" onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}
