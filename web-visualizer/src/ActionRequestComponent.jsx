import React from 'react';

const ActionRequestComponent = ({ message, elapsedTime, response }) => {
  const { agent_name, action_name, action_params } = message.content;

  return (
    <div className="message-box action-request">
      <div className="message-header">
        <div className="action-header">
          <span className="action-request-label">Action Request</span>
          <span className="agent-name">{agent_name}</span>
          <span className="action-name">{action_name}</span>
        </div>
        <span className="elapsed-time">{elapsedTime}</span>
      </div>
      <div className="message-content">
        <div className="action-params">
          <h4>Action Parameters:</h4>
          <ul>
            {Object.entries(action_params).map(([key, value]) => (
              <li key={key}><strong>{key}:</strong> {JSON.stringify(value)}</li>
            ))}
          </ul>
        </div>
      </div>
      {response && (
        <div className="action-response">
          <h4>Response:</h4>
          <p>{response.content.message}</p>
        </div>
      )}
    </div>
  );
};

export default ActionRequestComponent;
