
import { useState } from "react";
import api from "../api";
import "./ChatbotWidget.css";

const suggestions = [
  "Show me tech events",
  "Show me music events",
  "What are my bookings?",
  "Show me events this weekend",
  "I need help with tickets",
];

function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hi! 👋 Welcome to SmartEvent. I can help you discover events, check your bookings, and get ticket support.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text = message) => {
    const userMessage = text.trim();

    if (!userMessage || loading) return;

    if (!localStorage.getItem("token")) {
      setMessages((previous) => [
        ...previous,
        { sender: "user", text: userMessage },
        {
          sender: "bot",
          text: "Please log in first to use the chatbot.",
        },
      ]);
      setMessage("");
      return;
    }

    setMessages((previous) => [
      ...previous,
      { sender: "user", text: userMessage },
    ]);
    setMessage("");
    setLoading(true);

    try {
      const response = await api.post("/chatbot", {
        message: userMessage,
      });

      const answer =
        response.data?.answer || "Sorry, I couldn't find an answer.";

      setMessages((previous) => [
        ...previous,
        { sender: "bot", text: answer },
      ]);
    } catch (error) {
      const errorText =
        error.response?.status === 401
          ? "Your login session may have expired. Please log in again."
          : error.response?.data?.detail ||
            "I couldn't connect right now. Please try again.";

      setMessages((previous) => [
        ...previous,
        { sender: "bot", text: errorText },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  return (
    <div className="chatbot-widget">
      {isOpen && (
        <section
          className="chatbot-panel"
          aria-label="SmartEvent chatbot"
        >
          <header className="chatbot-header">
            <div>
              <h3>SmartEvent Assistant</h3>
              <p>Event discovery and booking help</p>
            </div>

            <button
              type="button"
              className="chatbot-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chatbot"
            >
              ×
            </button>
          </header>

          <div className="chatbot-messages" aria-live="polite">
            {messages.map((item, index) => (
              <div
                key={`${index}-${item.sender}`}
                className={`chatbot-message ${item.sender}`}
              >
                {item.text}
              </div>
            ))}

            {loading && (
              <div className="chatbot-message bot">
                Thinking...
              </div>
            )}
          </div>

          <div className="chatbot-suggestions">
            <p>Try asking:</p>

            {suggestions.map((suggestion) => (
              <button
                type="button"
                key={suggestion}
                disabled={loading}
                onClick={() => sendMessage(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>

          <form className="chatbot-form" onSubmit={handleSubmit}>
            <input
              type="text"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Ask me something..."
              aria-label="Your message"
              disabled={loading}
            />

            <button
              type="submit"
              disabled={loading || !message.trim()}
            >
              Send
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        className="chatbot-toggle"
        onClick={() => setIsOpen((previous) => !previous)}
        aria-label={isOpen ? "Close chatbot" : "Open chatbot"}
        title="Chat with SmartEvent"
      >
        {isOpen ? "×" : "💬"}
      </button>
    </div>
  );
}

export default ChatbotWidget;
