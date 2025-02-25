import React, { useState } from "react";

const LlmServiceResponseComponent = ({ message, elapsedTime }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="message-box llm-service-response">
      <div className="message-header">
        <span className="message-type">LLM Service Response</span>
        <span className="elapsed-time">{elapsedTime}</span>
      </div>
      <div className="message-content">
        {expanded ? (
          <pre>{JSON.stringify(message.content, null, 2)}</pre>
        ) : (
          <p>{JSON.stringify(message.content).slice(0, 100)}...</p>
        )}
        <button className="more-button" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show Less" : "Show More"}
        </button>
      </div>
    </div>
  );
};

export default LlmServiceResponseComponent;
