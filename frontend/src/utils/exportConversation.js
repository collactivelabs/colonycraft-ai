/**
 * Export a conversation to different formats
 * @param {Object} conversation - The conversation object to export
 * @param {string} format - Export format: 'json', 'markdown', or 'text'
 */
export const exportConversation = (conversation, format = 'json') => {
  if (!conversation) return;

  let content = '';
  let filename = `${conversation.title || 'conversation'}-${new Date().toISOString().slice(0, 10)}`;
  let mimeType = '';

  switch (format.toLowerCase()) {
    case 'json':
      content = JSON.stringify(conversation, null, 2);
      filename += '.json';
      mimeType = 'application/json';
      break;

    case 'markdown':
      // Create a markdown version with proper formatting
      content = `# ${conversation.title || 'Conversation'}\n\n`;
      content += `**Date:** ${new Date(conversation.timestamp).toLocaleString()}\n`;
      content += `**Model:** ${conversation.model_info?.model || 'Unknown'}\n`;
      content += `**Provider:** ${conversation.model_info?.provider || 'Unknown'}\n\n`;
      content += `## Prompt\n\n\`\`\`\n${conversation.prompt}\n\`\`\`\n\n`;
      content += `## Response\n\n${conversation.text}\n\n`;
      
      if (conversation.metadata?.usage) {
        content += `## Usage Stats\n\n`;
        content += `- Input Tokens: ${conversation.metadata.usage.input_tokens || 0}\n`;
        content += `- Output Tokens: ${conversation.metadata.usage.output_tokens || 0}\n`;
        content += `- Total Tokens: ${(conversation.metadata.usage.input_tokens || 0) + (conversation.metadata.usage.output_tokens || 0)}\n`;
      }
      
      filename += '.md';
      mimeType = 'text/markdown';
      break;

    case 'text':
    default:
      content = `${conversation.title || 'Conversation'}\n\n`;
      content += `Date: ${new Date(conversation.timestamp).toLocaleString()}\n`;
      content += `Model: ${conversation.model_info?.model || 'Unknown'}\n`;
      content += `Provider: ${conversation.model_info?.provider || 'Unknown'}\n\n`;
      content += `Prompt:\n${conversation.prompt}\n\n`;
      content += `Response:\n${conversation.text}\n\n`;
      
      if (conversation.metadata?.usage) {
        content += `Usage Stats:\n`;
        content += `Input Tokens: ${conversation.metadata.usage.input_tokens || 0}\n`;
        content += `Output Tokens: ${conversation.metadata.usage.output_tokens || 0}\n`;
        content += `Total Tokens: ${(conversation.metadata.usage.input_tokens || 0) + (conversation.metadata.usage.output_tokens || 0)}\n`;
      }
      
      filename += '.txt';
      mimeType = 'text/plain';
      break;
  }

  // Create a Blob with the content
  const blob = new Blob([content], { type: mimeType });
  
  // Create a temporary link to download the file
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  
  // Trigger the download
  document.body.appendChild(link);
  link.click();
  
  // Clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
};

/**
 * Show export format selection dialog
 * @param {Object} conversation - The conversation object to export
 * @returns {Promise} - Resolves when export is complete
 */
export const showExportDialog = (conversation) => {
  return new Promise((resolve, reject) => {
    // Create modal container
    const modal = document.createElement('div');
    modal.className = 'export-modal';
    modal.innerHTML = `
      <div class="export-modal-content">
        <h3>Export Conversation</h3>
        <p>Choose a format to export:</p>
        <div class="export-format-options">
          <button class="format-btn" data-format="json">JSON</button>
          <button class="format-btn" data-format="markdown">Markdown</button>
          <button class="format-btn" data-format="text">Plain Text</button>
        </div>
        <button class="cancel-btn">Cancel</button>
      </div>
    `;
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
      .export-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1100;
      }
      
      .export-modal-content {
        background-color: var(--card-background, #fff);
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        max-width: 400px;
        width: 90%;
      }
      
      .export-modal h3 {
        margin-top: 0;
        color: var(--text-color, #000);
      }
      
      .export-format-options {
        display: flex;
        gap: 12px;
        margin: 24px 0;
      }
      
      .format-btn {
        flex: 1;
        padding: 10px;
        border: 1px solid var(--border-color, #ddd);
        background-color: var(--button-secondary-bg, #f0f0f0);
        color: var(--button-secondary-text, #333);
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
      }
      
      .format-btn:hover {
        background-color: var(--primary-color, #3a86ff);
        color: white;
      }
      
      .cancel-btn {
        width: 100%;
        padding: 10px;
        border: none;
        background-color: var(--toggle-bg, #e9ecef);
        color: var(--text-color, #333);
        border-radius: 4px;
        cursor: pointer;
        margin-top: 12px;
      }
      
      .cancel-btn:hover {
        background-color: var(--toggle-hover-bg, #dee2e6);
      }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    // Handle format selection
    const formatButtons = modal.querySelectorAll('.format-btn');
    formatButtons.forEach(button => {
      button.addEventListener('click', () => {
        const format = button.getAttribute('data-format');
        exportConversation(conversation, format);
        closeModal();
        resolve(format);
      });
    });
    
    // Handle cancel
    const cancelButton = modal.querySelector('.cancel-btn');
    cancelButton.addEventListener('click', () => {
      closeModal();
      resolve(null);
    });
    
    // Close modal function
    function closeModal() {
      document.body.removeChild(modal);
      document.head.removeChild(style);
    }
  });
};
