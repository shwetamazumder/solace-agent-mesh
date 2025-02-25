import React, { useState } from 'react';

const OrchestratorReinvokeComponent = ({ message, elapsedTime }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const text = message.content.text || 'No reinvoke content';
  const isTruncated = text.length > 1000;
  const displayText = isExpanded ? text : (isTruncated ? text.slice(0, 1000) : text);

  return (
    <div className="message-box orchestrator-reinvoke">
      <div className="message-header">
        <span className="message-type">Orchestrator Reinvoke</span>
        <span className="elapsed-time">{elapsedTime}</span>
      </div>
      <div className="message-content">
        <p>{displayText}</p>
        {isTruncated && (
          <button 
            className="more-button" 
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Less' : 'More...'}
          </button>
        )}
      </div>
    </div>
  );
};

export default OrchestratorReinvokeComponent;