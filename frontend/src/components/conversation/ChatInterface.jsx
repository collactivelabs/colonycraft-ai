import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import MarkdownRenderer from '../ui/MarkdownRenderer';
import '../../styles/ChatInterface.css';

// Individual message component
const ChatMessage = ({ message, isUser }) => {
  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="user-avatar">U</div>
        ) : (
          <div className="assistant-avatar">AI</div>
        )}
      </div>
      <div className="message-content">
        {isUser ? (
          <div className="message-text">{message.text}</div>
        ) : (
          <div className="message-text">
            <MarkdownRenderer>{message.text}</MarkdownRenderer>
            {message.model_info && (
              <div className="message-metadata">
                <span className="provider-badge" data-provider={message.model_info.provider}>
                  {message.model_info.provider}
                </span>
                <span className="model-badge">
                  {message.model_info.model}
                </span>
                {message.metadata?.usage && (
                  <span className="token-usage">
                    Tokens: {message.metadata.usage.input_tokens + message.metadata.usage.output_tokens}
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

ChatMessage.propTypes = {
  message: PropTypes.shape({
    text: PropTypes.string.isRequired,
    model_info: PropTypes.shape({
      provider: PropTypes.string,
      model: PropTypes.string
    }),
    metadata: PropTypes.shape({
      usage: PropTypes.shape({
        input_tokens: PropTypes.number,
        output_tokens: PropTypes.number
      })
    })
  }).isRequired,
  isUser: PropTypes.bool.isRequired
};

const ChatInterface = ({
  providers,
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
  onGenerateResponse,
  loading,
  error
}) => {
  // State for conversation messages
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  
  // Scroll to bottom whenever messages change
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Handle sending a message
  const handleSendMessage = async () => {
    if (!input.trim() || !selectedProvider || !selectedModel) return;
    
    // Add user message to conversation
    const userMessage = {
      id: Date.now(),
      text: input,
      isUser: true
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    
    try {
      // Call API to generate response
      const response = await onGenerateResponse(input);
      
      // Add assistant response to conversation
      if (response) {
        const assistantMessage = {
          id: Date.now() + 1,
          text: response.text,
          model_info: response.model_info,
          metadata: response.metadata,
          isUser: false
        };
        
        setMessages(prevMessages => [...prevMessages, assistantMessage]);
      }
    } catch (err) {
      // If there's an error, add an error message
      const errorMessage = {
        id: Date.now() + 1,
        text: `Error: ${err.message || 'Failed to generate response'}`,
        isUser: false,
        isError: true
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    }
  };
  
  // Handle key press (Enter to send)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Clear conversation
  const handleClearConversation = () => {
    if (window.confirm('Are you sure you want to clear the conversation?')) {
      setMessages([]);
    }
  };
  
  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="model-selector">
          <div className="select-group">
            <label htmlFor="provider-select">Provider:</label>
            <select
              id="provider-select"
              value={selectedProvider}
              onChange={(e) => onProviderChange(e.target.value)}
              disabled={loading}
            >
              <option value="">Select Provider</option>
              {providers.map(provider => (
                <option key={provider.name} value={provider.name}>
                  {provider.name}
                </option>
              ))}
            </select>
          </div>

          <div className="select-group">
            <label htmlFor="model-select">Model:</label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => onModelChange(e.target.value)}
              disabled={!selectedProvider || loading}
            >
              <option value="">Select Model</option>
              {selectedProvider &&
                providers
                  .find(p => p.name === selectedProvider)?.models
                  .map(model => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))
              }
            </select>
          </div>
        </div>
        
        <button 
          className="clear-chat-btn" 
          onClick={handleClearConversation}
          disabled={messages.length === 0}
        >
          Clear Chat
        </button>
      </div>
      
      {error && (
        <div className="error-message">
          <span className="error-icon">!</span>
          {error}
        </div>
      )}
      
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            {/* Wrap emoji for accessibility */}
            <div className="empty-chat-icon"><span role="img" aria-label="Speech bubble emoji">💬</span></div>
            <h3>Start a new conversation</h3>
            <p>Select a model and enter your message below to begin chatting.</p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
              isUser={message.isUser} 
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-container">
        <textarea
          className="chat-input"
          placeholder="Type your message here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading || !selectedModel}
          rows="3"
        />
        <button 
          className="send-button" 
          onClick={handleSendMessage}
          disabled={loading || !input.trim() || !selectedModel}
        >
          {loading ? (
            <span className="loading-spinner"></span>
          ) : (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          )}
        </button>
      </div>
    </div>
  );
};

ChatInterface.propTypes = {
  providers: PropTypes.array.isRequired,
  selectedProvider: PropTypes.string.isRequired,
  selectedModel: PropTypes.string.isRequired,
  onProviderChange: PropTypes.func.isRequired,
  onModelChange: PropTypes.func.isRequired,
  onGenerateResponse: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string
};

export default ChatInterface;