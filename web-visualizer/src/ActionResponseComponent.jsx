import React from 'react';

const ActionResponseComponent = ({ message, elapsedTime }) => {
  return (
    <div className="message-box action-response">
      <div className="message-header">
        <span className="message-type">Action Response</span>
        <span className="elapsed-time">{elapsedTime}</span>
      </div>
      <div className="message-content">
        <p>{message.content.message || 'No message content'}</p>
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
    </div>
  );
};

export default ActionResponseComponent;