import React, { useState } from 'react';

const StimulusComponent = ({ message, elapsedTime }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const text = message.content.text || 'No text content';
  const isTruncated = text.length > 1000;
  const displayText = isExpanded ? text : (isTruncated ? text.slice(0, 1000) : text);

  return (
    <div className="message-box stimulus">
      <div className="message-header">
        <span className="message-type">Stimulus from originator</span>
        <span className="elapsed-time">{elapsedTime}</span>
      </div>
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
    </div>
  );
};

export default StimulusComponent;
