import React, { useState, useEffect } from 'react';
import '../../styles/ConversationManager.css';

// Data structure for a conversation entry
const ConversationEntry = ({ 
  id, 
  title, 
  provider, 
  model, 
  timestamp, 
  onSelect, 
  onDelete,
  selected
}) => {
  const date = new Date(timestamp).toLocaleString();
  
  return (
    <div className={`conversation-entry ${selected ? 'selected' : ''}`}>
      <div className="entry-content" onClick={() => onSelect(id)}>
        <h4 className="entry-title">{title}</h4>
        <div className="entry-metadata">
          <span className="provider-badge" data-provider={provider}>
            {provider}
          </span>
          <span className="model-badge">{model}</span>
          <span className="entry-date">{date}</span>
        </div>
      </div>
      <button 
        className="delete-entry-btn" 
        onClick={() => onDelete(id)}
        aria-label="Delete conversation"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
        >
          <path d="M3 6h18"></path>
          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
        </svg>
      </button>
    </div>
  );
};

const ConversationManager = ({ 
  currentConversation,
  onLoadConversation,
  onSaveConversation,
  onExportConversation
}) => {
  // State for conversations (will be loaded from localStorage)
  const [conversations, setConversations] = useState([]);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  
  // Load conversations from localStorage on component mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('conversations');
    if (savedConversations) {
      setConversations(JSON.parse(savedConversations));
    }
  }, []);

  // Save conversations to localStorage when updated
  useEffect(() => {
    localStorage.setItem('conversations', JSON.stringify(conversations));
  }, [conversations]);

  // Handle conversation selection
  const handleSelect = (id) => {
    setSelectedConversationId(id);
    const conversation = conversations.find(c => c.id === id);
    if (conversation && onLoadConversation) {
      onLoadConversation(conversation);
    }
  };

  // Handle conversation deletion
  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      setConversations(conversations.filter(c => c.id !== id));
      if (selectedConversationId === id) {
        setSelectedConversationId(null);
      }
    }
  };

  // Save current conversation
  const handleSave = () => {
    if (!currentConversation) return;
    
    // Generate a title if not provided
    const title = newTitle.trim() || 
      `Conversation ${new Date().toLocaleDateString()}`;
    
    const newConversation = {
      id: Date.now().toString(),
      title,
      ...currentConversation,
      timestamp: Date.now()
    };
    
    setConversations([newConversation, ...conversations]);
    setNewTitle('');
    setSelectedConversationId(newConversation.id);
    
    if (onSaveConversation) {
      onSaveConversation(newConversation);
    }
  };

  // Export the selected conversation
  const handleExport = () => {
    if (!selectedConversationId) return;
    
    const conversation = conversations.find(c => c.id === selectedConversationId);
    if (conversation && onExportConversation) {
      onExportConversation(conversation);
    }
  };

  return (
    <div className="conversation-manager">
      <button 
        className={`toggle-sidebar-btn ${isVisible ? 'active' : ''}`}
        onClick={() => setIsVisible(!isVisible)}
        aria-label="Toggle conversation manager"
      >
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
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span>Conversations</span>
      </button>
      
      <div className={`sidebar ${isVisible ? 'visible' : ''}`}>
        <div className="sidebar-header">
          <h3>Saved Conversations</h3>
          <button 
            className="close-sidebar-btn"
            onClick={() => setIsVisible(false)}
            aria-label="Close conversation manager"
          >
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
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div className="save-conversation">
          <input
            type="text"
            placeholder="Conversation title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
          />
          <button 
            className="save-btn"
            onClick={handleSave}
            disabled={!currentConversation}
          >
            Save Current
          </button>
        </div>
        
        <div className="conversation-actions">
          <button 
            className="export-btn"
            onClick={handleExport}
            disabled={!selectedConversationId}
          >
            Export
          </button>
        </div>
        
        <div className="conversations-list">
          {conversations.length === 0 ? (
            <p className="no-conversations">No saved conversations yet</p>
          ) : (
            conversations.map(conversation => (
              <ConversationEntry
                key={conversation.id}
                id={conversation.id}
                title={conversation.title}
                provider={conversation.model_info?.provider || 'unknown'}
                model={conversation.model_info?.model || 'unknown'}
                timestamp={conversation.timestamp}
                onSelect={handleSelect}
                onDelete={handleDelete}
                selected={selectedConversationId === conversation.id}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ConversationManager;
