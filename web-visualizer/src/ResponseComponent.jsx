import React, { useState } from 'react';

const ResponseComponent = ({ message, elapsedTime, isStreaming, isComplete }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const text = message.content.text || 'No response text';
  const isTruncated = text.length > 1000;
  const displayText = isExpanded ? text : (isTruncated ? text.slice(0, 1000) : text);

  return (
    <div className={`message-box response ${isStreaming ? 'streaming' : ''} ${isComplete ? 'complete' : ''}`}>
      <div className="message-header">
        <span className="message-type">
          {isComplete ? 'Response Complete' : isStreaming ? 'Streaming Response' : 'Response to originator'}
          {isStreaming && !message.content.last_chunk && ' (In Progress)'}
        </span>
        <span className="elapsed-time">{elapsedTime}</span>
      </div>
      {!isComplete && (
        <div className="message-content">
          {displayText}
          {isTruncated && (
            <button 
              className="more-button" 
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Less' : 'More...'}
            </button>
          )}
        </div>
      )}
      {message.content.files && message.content.files.length > 0 && (
        <div className="file-list">
          <h4>Files:</h4>
          <ul>
            {message.content.files.map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ResponseComponent;
